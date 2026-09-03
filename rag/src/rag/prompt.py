
from ...config import SYSTEM_PROMPT

class PromptBuilder:

    def build(self, question: str, retrieved_chunks: list) -> str:

        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, start=1):

            metadata = chunk["metadata"]

            arxiv_id = metadata.get("arxiv_id", "Unknown")
            title = metadata.get("title", "Unknown")
            section = metadata.get("section", "Unknown")

            text = chunk["text"]

            context_parts.append(
                f"""
                    [Source {i}]
                    Title: {title}
                    arXiv ID: {arxiv_id}
                    Section: {section}

                    {text}
                """
            )

        context = "\n".join(context_parts)

        prompt = f"""
            {self.SYSTEM_PROMPT}

            ====================
            CONTEXT
            ====================

            {context}

            ====================
            QUESTION
            ====================

            {question}

            ====================
            ANSWER
            ====================
        """

        return prompt