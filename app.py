"""Serveur web léger pour interroger la base RAG arXiv."""

import errno
import json
import logging
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from rag.src.rag.generator import Generator
from rag.src.rag.prompt import PromptBuilder
from rag.src.retrievers.openrouter import Retriever
from rag.src.vectorstore.openrouter import ChromaVectorStore

ROOT_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT_DIR / "web"
HOST = os.getenv("ARXIV_BOT_HOST", "127.0.0.1")
PORT = int(os.getenv("ARXIV_BOT_PORT", "8767"))
MAX_QUESTION_LENGTH = 2_000
DEFAULT_TOP_K = 5

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class RagService:
    """Initialise les composants coûteux une seule fois par processus."""

    def __init__(self) -> None:
        vector_store = ChromaVectorStore()
        self.retriever = Retriever(vector_store.collection, vector_store.embedding_model)
        self.prompt_builder = PromptBuilder()
        self.generator = Generator()

    def answer(self, question: str, top_k: int = DEFAULT_TOP_K) -> dict:
        chunks = self.retriever.retrieve(question, top_k=top_k)
        if not chunks:
            return {
                "answer": "Aucun document pertinent n'a été trouvé dans la base.",
                "sources": [],
            }

        prompt = self.prompt_builder.build(question, chunks)
        answer = self.generator.generate(prompt).strip()
        sources = [
            {
                "title": chunk["metadata"].get("title", "Titre inconnu"),
                "arxiv_id": chunk["metadata"].get("arxiv_id")
                or chunk["metadata"].get("article_id", "Inconnu"),
                "section": chunk["metadata"].get("section") or "Section non précisée",
                "source": chunk["metadata"].get("source", ""),
                "distance": chunk.get("distance"),
            }
            for chunk in chunks
        ]
        return {"answer": answer, "sources": sources}


_service: RagService | None = None


def get_service() -> RagService:
    global _service
    if _service is None:
        _service = RagService()
    return _service


class RequestHandler(BaseHTTPRequestHandler):
    """Expose l'API JSON et les fichiers statiques de l'interface."""

    def do_OPTIONS(self) -> None:
        if urlparse(self.path).path == "/api/ask":
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_cors_headers()
            self.end_headers()
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Route introuvable.")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        if path == "/":
            self._send_file(WEB_DIR / "index.html")
            return
        if path in {"/styles.css", "/app.js"}:
            relative_path = Path(path.removeprefix("/"))
            self._send_file(WEB_DIR / relative_path)
            return
        if path.startswith("/static/"):
            relative_path = Path(path.removeprefix("/static/"))
            file_path = (WEB_DIR / relative_path).resolve()
            if WEB_DIR.resolve() not in file_path.parents:
                self._send_error(HTTPStatus.NOT_FOUND, "Ressource introuvable.")
                return
            self._send_file(file_path)
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Route introuvable.")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/ask":
            self._send_error(HTTPStatus.NOT_FOUND, "Route introuvable.")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            question = str(payload.get("question", "")).strip()
            top_k = min(max(int(payload.get("top_k", DEFAULT_TOP_K)), 1), 10)
        except (ValueError, TypeError, json.JSONDecodeError):
            self._send_error(HTTPStatus.BAD_REQUEST, "Requête JSON invalide.")
            return

        if not question:
            self._send_error(HTTPStatus.BAD_REQUEST, "La question est obligatoire.")
            return
        if len(question) > MAX_QUESTION_LENGTH:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                f"La question ne doit pas dépasser {MAX_QUESTION_LENGTH} caractères.",
            )
            return

        try:
            self._send_json(get_service().answer(question, top_k))
        except (RuntimeError, ValueError) as error:
            logger.exception("Échec du traitement de la question")
            self._send_error(
                HTTPStatus.BAD_GATEWAY,
                str(error),
            )
        except Exception:
            logger.exception("Échec du traitement de la question")
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Impossible de générer une réponse. Vérifiez les logs du serveur.",
            )

    def _send_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self._send_error(HTTPStatus.NOT_FOUND, "Ressource introuvable.")
            return
        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin.startswith(("http://localhost:", "http://127.0.0.1:")):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message}, status)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    try:
        server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            logger.error(
                "Le port %s est déjà utilisé. Arrêtez l'autre serveur "
                "ou lancez ARXIV_BOT_PORT=8780 ./env/bin/python app.py.",
                PORT,
            )
            raise SystemExit(1) from error
        raise
    logger.info("Interface disponible sur http://%s:%s", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
