from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."

        context_blocks = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("doc_id") or r.get("id")
            context_blocks.append(f"[{i}] (Nguồn: {source}):\n{r['content']}")

        context_text = "\n\n".join(context_blocks)
        prompt = (
            f"Bạn là trợ lý AI trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            f"Chỉ sử dụng thông tin trong ngữ cảnh dưới đây. Trích dẫn số thứ tự nguồn [1], [2]... nếu có thể.\n"
            f"Nếu thông tin không có trong ngữ cảnh, hãy nói rõ là không tìm thấy.\n\n"
            f"--- NGỮ CẢNH ---\n"
            f"{context_text}\n\n"
            f"--- CÂU HỎI ---\n"
            f"{question}\n\n"
            f"--- TRẢ LỜI ---"
        )
        return self.llm_fn(prompt)
