const form = document.querySelector("#question-form");
const questionInput = document.querySelector("#question");
const count = document.querySelector("#char-count");
const button = document.querySelector("#ask-button");
const errorMessage = document.querySelector("#error-message");
const answerPanel = document.querySelector("#answer-panel");
const answer = document.querySelector("#answer");
const sources = document.querySelector("#sources");
const apiBase =
  window.location.port === "8767"
    ? ""
    : "http://127.0.0.1:8767";

questionInput.addEventListener("input", () => {
  count.textContent = `${questionInput.value.length} / 2000`;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  errorMessage.hidden = true;
  answerPanel.hidden = true;
  button.disabled = true;
  button.querySelector("span").textContent = "Analyse en cours…";

  try {
    const response = await fetch(`${apiBase}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const body = await response.text();
    let data;
    try {
      data = JSON.parse(body);
    } catch {
      throw new Error(
        response.ok
          ? "Le serveur a renvoyé une réponse invalide."
          : `Le serveur a refusé la requête (${response.status}). Lancez app.py puis rechargez la page.`,
      );
    }
    if (!response.ok) throw new Error(data.error || "Une erreur est survenue.");

    answer.textContent = data.answer;
    sources.innerHTML = "";
    if (data.sources.length) {
      sources.insertAdjacentHTML("beforeend", "<h3>Sources consultées</h3>");
      data.sources.forEach((source) => {
        const item = document.createElement("div");
        item.className = "source";
        item.innerHTML = `<strong>${escapeHtml(source.title)}</strong><br>${escapeHtml(source.arxiv_id)} · ${escapeHtml(source.section)}`;
        sources.appendChild(item);
      });
    }
    answerPanel.hidden = false;
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Analyser la question";
  }
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[character]));
}
