"""
Benchmark script for Lab 7: Vector Store and Retrieval.
Personal Strategy: Phùng Quốc Việt - SentenceChunker(max_sentences_per_chunk=3)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.chunking import SentenceChunker
from src.embeddings import MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

# 5 Benchmark Queries agreed by the team
QUERIES = [
    {
        "id": 1,
        "query": "Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng?",
        "gold_answer": "15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công",
        "expected_doc": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": {"audience": "buyer"},
    },
    {
        "id": 2,
        "query": "Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu?",
        "gold_answer": "02 ngày lịch kể từ ngày nhận thông báo",
        "expected_doc": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": {"audience": "seller"},
    },
    {
        "id": 3,
        "query": "Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu?",
        "gold_answer": "Hoàn tiền 100% vào ví Senpay, thời gian khoảng 3–7 ngày",
        "expected_doc": "sendo-chinh-sach-doi-tra-buyer",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày?",
        "gold_answer": "7 ngày đầu — hình thức Đổi mới / Hoàn tiền",
        "expected_doc": "tiki-chinh-sach-doi-tra-buyer",
        "filter": {"audience": "buyer"},
    },
    {
        "id": 5,
        "query": "Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không?",
        "gold_answer": "Không — người bán không chịu chi phí khi lỗi do đơn vị vận chuyển",
        "expected_doc": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": {"audience": "seller"},
    },
]


def parse_markdown_file(path: Path) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter and body text from a Markdown file."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_fm = parts[1]
            body = parts[2].strip()
            fm = dict(re.findall(r"^(\w+):\s*(.+)$", raw_fm, re.MULTILINE))
            return fm, body
    return {}, text.strip()


def build_knowledge_base(data_dir: Path, chunker: Any) -> list[Document]:
    """Load Markdown files, parse frontmatter, chunk bodies, and create Documents."""
    documents: list[Document] = []
    md_files = sorted(data_dir.glob("*.md"))

    for path in md_files:
        fm, body = parse_markdown_file(path)
        doc_id = fm.get("doc_id", path.stem)
        chunks = chunker.chunk(body)

        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **fm,
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_file": path.name,
            }
            doc = Document(
                id=f"{path.stem}#{i}",
                content=chunk,
                metadata=chunk_metadata,
            )
            documents.append(doc)

    return documents


def run_benchmark() -> None:
    data_dir = Path("data/ecommerce")
    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist.")
        return

    # CHIẾN LƯỢC RIÊNG CỦA PHÙNG QUỐC VIỆT: SentenceChunker (max 3 sentences)
    chunker = SentenceChunker(max_sentences_per_chunk=3)
    embedder = MockEmbedder()
    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=embedder)

    lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    log("================================================================")
    log("           BENCHMARK RETRIEVAL — LAB 7 (CHECKPOINT 5)")
    log("Thành viên : Phùng Quốc Việt")
    log("Chiến lược : SentenceChunker(max_sentences_per_chunk=3)")
    log("Chủ đề     : E-commerce Return & Refund Policies")
    log("================================================================\n")

    # 1. Nạp dữ liệu và chia nhỏ
    documents = build_knowledge_base(data_dir, chunker)
    store.add_documents(documents)

    log(f"[OK] Đã nạp thành công {len(documents)} chunks từ các tài liệu trong '{data_dir}'.")
    log(f"[OK] Kích thước kho lưu trữ (Collection size): {store.get_collection_size()} chunks.\n")

    # 2. Chạy 5 câu hỏi benchmark
    log("----------------------------------------------------------------")
    log("                     KẾT QUẢ TRUY XUẤT TOP-3")
    log("----------------------------------------------------------------\n")

    eval_summary = []
    total_score = 0

    for item in QUERIES:
        qid = item["id"]
        q_text = item["query"]
        gold = item["gold_answer"]
        expected_doc = item["expected_doc"]
        f_dict = item["filter"]

        log(f"Query #{qid}: {q_text}")
        log(f"Filter áp dụng: {f_dict}")
        log(f"Gold Answer   : {gold}")

        results = store.search_with_filter(q_text, top_k=3, metadata_filter=f_dict)
        log(f"Số kết quả trả về: {len(results)}")

        sources = [r.get("metadata", {}).get("doc_id", "") for r in results]

        for rank, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("doc_id", "unknown")
            score = r.get("score", 0.0)
            preview = r["content"][:150].replace("\n", " ").strip()
            log(f"  [{rank}] Score: {score:.4f} | Nguồn: {source}")
            log(f"      Nội dung: {preview}...")

        log("-" * 64 + "\n")

        # Kiểm tra Hit@1 và Hit@3 theo tài liệu nguồn và từ khóa nội dung (Gold Content)
        gold_keywords_map = {
            1: ["15", "mười lăm", "thời hạn"],
            2: ["02 ngày", "2 ngày", "phản hồi", "thông báo"],
            3: ["senpay", "3-7", "3 đến 7", "ví senpay"],
            4: ["7 ngày", "bảy ngày", "điện thoại", "đổi mới"],
            5: ["không chịu chi phí", "vận chuyển", "hoàn trả", "người bán"],
        }
        kws = gold_keywords_map.get(qid, [])

        hit_top1_doc = bool(sources and sources[0] == expected_doc)
        hit_top3_doc = any(s == expected_doc for s in sources)

        # Kiểm tra xem có chunk nào trong top-3 vừa đúng doc vừa chứa gold keyword
        has_gold_chunk = False
        gold_rank = None
        for rank, r in enumerate(results, 1):
            if r.get("metadata", {}).get("doc_id") == expected_doc:
                content_lower = r["content"].lower()
                if any(kw.lower() in content_lower for kw in kws):
                    has_gold_chunk = True
                    gold_rank = rank
                    break

        # Chấm điểm nghiêm ngặt theo docs/SCORING.md:
        # 2đ: Top-1 đúng doc và chứa từ khóa câu trả lời
        # 1đ: Top-3 có doc liên quan hoặc chứa nội dung liên quan nhưng không ở Top-1
        # 0đ: Không truy xuất được tài liệu đúng trong Top-3
        if gold_rank == 1 or (hit_top1_doc and has_gold_chunk):
            q_score = 2
            status = "Chính xác tuyệt đối (Top-1 trúng nội dung Gold)"
        elif has_gold_chunk or hit_top3_doc:
            q_score = 1
            status = "Đúng tài liệu nguồn trong Top-3 (Cần cải thiện rank)"
        else:
            q_score = 0
            status = "Trượt Top-3 (Do MockEmbedder không hiểu ngữ nghĩa)"

        total_score += q_score
        eval_summary.append({
            "id": qid,
            "expected": expected_doc,
            "top1": sources[0] if sources else "None",
            "hit_top1": hit_top1_doc and has_gold_chunk,
            "hit_top3": hit_top3_doc,
            "score": q_score,
            "status": status,
        })

    # 3. Tính toán Accuracy và Điểm Chất lượng Truy xuất (Retrieval Quality)
    log("================================================================")
    log("          TỔNG KẾT HIỆU SUẤT TRUY XUẤT (ACCURACY & METRICS)")
    log("================================================================\n")

    # In bảng tổng hợp
    log(f"{'#':<3} | {'Expected Doc':<38} | {'Top-1 Doc':<38} | {'Hit@1':<6} | {'Hit@3':<6} | {'Điểm':<4} | Ghi chú")
    log("-" * 115)
    for ev in eval_summary:
        h1 = "ĐÚNG" if ev['hit_top1'] else "SAI"
        h3 = "CÓ" if ev['hit_top3'] else "KHÔNG"
        log(f"{ev['id']:<3} | {ev['expected'][:38]:<38} | {ev['top1'][:38]:<38} | {h1:<6} | {h3:<6} | {ev['score']}/2  | {ev['status']}")
    log("-" * 115 + "\n")

    hits_3 = sum(1 for ev in eval_summary if ev["hit_top3"])
    hits_1 = sum(1 for ev in eval_summary if ev["hit_top1"])
    accuracy_top3 = (hits_3 / len(QUERIES)) * 100
    accuracy_top1 = (hits_1 / len(QUERIES)) * 100

    log(f"▶ Top-3 Retrieval Accuracy (Hit@3) : {hits_3}/{len(QUERIES)} ({accuracy_top3:.1f}%)")
    log(f"▶ Top-1 Retrieval Accuracy (Hit@1) : {hits_1}/{len(QUERIES)} ({accuracy_top1:.1f}%)")
    log(f"▶ Điểm Đánh Giá Truy Xuất (Score) : {total_score}/10 điểm (theo tiêu chí docs/SCORING.md)")
    log("================================================================\n")

    out_file = Path("ket_qua_benchmark.txt")
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Đã lưu toàn bộ kết quả kèm Accuracy vào '{out_file.name}' (UTF-8).")


if __name__ == "__main__":
    run_benchmark()
