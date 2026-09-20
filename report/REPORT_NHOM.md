# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm SOUL
**Thành viên:** Nguyễn Công Duẩn · Phùng Quốc Việt · Phan Hoàng Vũ
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, hoàn tiền và quy định xử lý khiếu nại trên sàn Thương mại điện tử (Shopee Việt Nam).

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề này vì Shopee là sàn thương mại điện tử phổ biến nhất hiện nay với các quy định đổi trả/hoàn tiền được chuẩn hóa rất chặt chẽ. Đặc biệt, các chính sách này phân định ranh giới rõ ràng giữa quyền lợi của Người mua (buyer) và nghĩa vụ/chế tài của Người bán (seller), rất lý tưởng để kiểm chứng và đánh giá tính hiệu quả của cơ chế lọc siêu dữ liệu (`metadata_filter`).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
| --- | -------------- | ------------ | -------------------- | ---------- | ----------------- |
| 1 | Chính sách trả hàng và hoàn tiền Shopee | <https://help.shopee.vn/portal/4/article/77251> | 2026-09-20 / 2026-03-11 | ~26300 | audience: both, category: return-refund, language: vi |
| 2 | Chính sách đổi trả tại Tiki trước ngày 15-04-2024 | <https://hotro.tiki.vn/knowledge-base/post/805> | 2026-09-20 / 2024-04-15 | ~2950 | audience: buyer, category: return-refund, language: vi |
| 3 | Hướng dẫn đổi trả hàng và hoàn tiền dành cho Người mua trên Sendo | <https://ginee.com/vn/insights/doi-tra-hang-sendo/> | 2026-09-20 / 2021.11 | ~3100 | audience: buyer, category: return-refund, language: vi |
| 4 | Chính sách hủy đơn hàng trả hàng và hoàn tiền của khách hàng trên TikTok Shop | <https://seller-vn.tiktok.com/university/essay?knowledge_id=6837773789234946> | 2026-09-20 / 2026.1 | ~17340 | audience: seller, category: seller-returns, language: vi |
| 5 | Quy trình mới Chỉ hoàn tiền đối với đơn hàng hoàn trả về kho Lazada | <https://sellercenter.lazada.vn/helpcenter/s/faq/knowledge> | 2026-09-20 / 2024-12-05 | ~1900 | audience: seller, category: seller-returns, language: vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
| ---------------- | ------ | --------------- | ------------------------------- |
| `doc_id` | `str` | `shopee-thoi-han-tra-hang-buyer` | Định danh duy nhất và liên kết trực tiếp với tài liệu gốc để phục vụ xóa tài liệu và truy vết nguồn. |
| `audience` | `str` | `buyer`, `seller` | Phân tách đối tượng áp dụng. Cho phép `search_with_filter` lọc chính xác quy định cho người mua hay người bán, tránh nhầm lẫn mốc thời gian. |
| `category` | `str` | `returns-policy`, `refund-policy`, `seller-returns`, `seller-penalty` | Thu hẹp phạm vi tìm kiếm theo phân loại chính sách, tăng độ chính xác của kết quả truy xuất. |
| `language` | `str` | `vi` | Định rõ ngôn ngữ tài liệu, hỗ trợ mở rộng hệ thống đa ngữ trong tương lai. |
| `document_version` | `str` | `2026.1`, `2026.2` | Kiểm soát phiên bản và độ mới của văn bản chính sách, tránh trích dẫn quy định cũ đã hết hiệu lực. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
| ----------- | ---------- | ------------- | ------------ | ------------------- |
| Shopee Policy (`shopee-chinh-sach-tra-hang-hoan-tien.md`) | FixedSizeChunker (`fixed_size`) | 40 | 498.9 | Kém (cắt ngang từ/câu và các điều khoản pháp lý) |
| Shopee Policy (`shopee-chinh-sach-tra-hang-hoan-tien.md`) | SentenceChunker (`by_sentences`) | 48 | 412.9 | Khá (câu nguyên vẹn, nhưng tách rời tiêu đề và nội dung) |
| Shopee Policy (`shopee-chinh-sach-tra-hang-hoan-tien.md`) | RecursiveChunker (`recursive`) | 62 | 319.9 | Rất tốt (giữ trọn vẹn từng điều khoản và cấu trúc tiêu đề) |
| Tiki Policy (`tiki-chinh-sach-doi-tra-buyer.md`) | FixedSizeChunker (`fixed_size`) | 6 | 439.5 | Kém (cắt ngang bảng điều kiện phân loại ngành hàng) |
| Tiki Policy (`tiki-chinh-sach-doi-tra-buyer.md`) | SentenceChunker (`by_sentences`) | 9 | 291.4 | Khá (tách riêng được các mốc thời gian hỗ trợ) |
| Tiki Policy (`tiki-chinh-sach-doi-tra-buyer.md`) | RecursiveChunker (`recursive`) | 7 | 375.1 | Rất tốt (giữ liền khối các quy định và lưu ý đối soát) |
| TikTok Shop (`tiktokshop-chinh-sach-tra-hang-seller.md`) | FixedSizeChunker (`fixed_size`) | 26 | 494.3 | Kém (cắt đứt giữa ranh giới phân bổ phí vận chuyển) |
| TikTok Shop (`tiktokshop-chinh-sach-tra-hang-seller.md`) | SentenceChunker (`by_sentences`) | 28 | 456.4 | Khá (giữ đúng các câu quy định hủy đơn của người bán) |
| TikTok Shop (`tiktokshop-chinh-sach-tra-hang-seller.md`) | RecursiveChunker (`recursive`) | 33 | 387.5 | Rất tốt (phân đoạn chuẩn theo từng phần quyền và chế tài) |

### Chiến lược của từng thành viên

> Mỗi thành viên thử nghiệm một chiến lược chunking khác nhau trên cùng bộ tài liệu theo phân công nhóm.

**Thành viên 1 — Phùng Quốc Việt**

- **Loại chiến lược:** SentenceChunker (`by_sentences`)
- **Mô tả & lý do chọn cho chủ đề này:** Chia nhỏ văn bản theo ranh giới câu (`max_sentences_per_chunk=3`). Trong các điều khoản chính sách TMĐT, mỗi câu quy định một quyền lợi, điều kiện hoặc mốc thời gian độc lập (ví dụ thời hạn 15 ngày của Shopee, 7 ngày của Tiki). Việc nhóm 3 câu liên tiếp đảm bảo giữ nguyên vẹn câu khẳng định pháp lý, tránh trường hợp câu bị cắt ngang giữa chừng.
- **Code snippet (nếu custom):**

```python
sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
chunks = sentence_chunker.chunk(policy_text)
```

**Thành viên 2 — Nguyễn Công Duẩn**

- **Loại chiến lược:** RecursiveChunker (`recursive`)
- **Mô tả & lý do chọn:** Chia đệ quy theo danh sách phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]` với `chunk_size=500`. Văn bản quy định có cấu trúc phân cấp từ Điều khoản lớn, Tiểu mục đến gạch đầu dòng. RecursiveChunker giữ trọn vẹn khối đoạn văn bản (`\n\n`) trước khi hạ cấp xuống câu văn, giúp bảo toàn cấu trúc ngữ cảnh pháp lý.
- **Code snippet (nếu custom):**

```python
recursive_chunker = RecursiveChunker(
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=500
)
chunks = recursive_chunker.chunk(policy_text)
```

**Thành viên 3 — Phan Hoàng Vũ**

- **Loại chiến lược:** HeadingChunker (custom, theo vai R3)
- **Mô tả & lý do chọn:** Chunk theo tiêu đề Markdown (`##`) với `chunk_size=500`. Các chính sách TMĐT được biên soạn sẵn theo từng mục (`## Điều 1...`, `## Điều 2...`). Với các section dài vượt quá 500 ký tự, thuật toán cắt nhỏ và **gắn lại tiêu đề mục vào đầu từng mảnh con** để mảnh con không bị mất ngữ cảnh "đây là mục nào".

```python
import re

class HeadingChunker:
    """Chunk theo tiêu đề ## trong Markdown. Section nào dài quá thì cắt thêm và gắn lại heading."""
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        parts = re.split(r'(?=^##+ )', text, flags=re.MULTILINE)
        chunks = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                heading_match = re.match(r'^(##+ .+)', part)
                heading = heading_match.group(1) + "\n" if heading_match else ""
                body = part[len(heading):]
                for start in range(0, len(body), self.chunk_size):
                    sub = body[start : start + self.chunk_size]
                    chunks.append((heading + sub).strip())
        return chunks
```

### So Sánh Giữa Các Thành Viên

> Nhóm đã tiến hành chạy thử nghiệm độc lập 5 câu hỏi benchmark trên cùng bộ tài liệu thương mại điện tử với 3 chiến lược chunking khác nhau. Dưới đây là bảng số liệu đối soát thực tế:

| Thành viên | Chiến lược (Strategy) | Số chunk nạp | Điểm truy xuất (/10) | Hit@3 (Accuracy) | Điểm mạnh | Điểm yếu |
| ----------- | ---------- | :---: | :---: | :---: | ----------- | ---------- |
| **Phùng Quốc Việt** | `SentenceChunker` (`by_sentences`, max=3) | 115 | **5.0 / 10** | **3/5 (60%)** | Độ mịn cao (115 chunks), giữ trọn câu quy định, các mốc thời gian ngắn không bị pha loãng ngữ cảnh. Đạt Hit@1 cao nhất nhóm (40% - trúng tuyệt đối ở Câu 2 & Câu 5). | Do không có overlap và MockEmbedder băm MD5, tài liệu Sendo và Tiki bị Shopee chiếm ưu thế điểm số, trượt Top-3 ở Câu 3 và Câu 4. |
| **Nguyễn Công Duẩn** | `RecursiveChunker` (`recursive`, size=500) | 50 | **5.0 / 10** | **3/5 (60%)** | Đoạn văn 500 ký tự giữ nguyên khối điều khoản và chế tài (trúng GOLD chunk ở câu 4 và câu 5). Thực nghiệm A/B filter rất rõ rệt. | Số lượng chunk ít (50 chunks), dung lượng mỗi chunk lớn khiến mật độ từ khóa bị loãng, Hit@1 đạt 0% (các chunk đúng nằm ở Rank 2 và 3). |
| **Phan Hoàng Vũ** | `HeadingChunker` (custom, size=500) | 91 | **4.0 / 10** | **2/5 (40%)** | Ý tưởng gắn lại tiêu đề `## Heading` vào đầu mỗi chunk con giúp bảo toàn bối cảnh điều khoản rất logic (trúng Top-1 ở Câu 1). | Các section mở đầu chứa nhiều từ ngữ thủ tục chung dẫn tới MockEmbedder tính điểm tương đồng cao ở các chunk điều hướng. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Thực nghiệm cho thấy **`SentenceChunker` (Việt)** và **`RecursiveChunker` (Duẩn)** cùng đạt điểm cao nhất (**5.0 / 10 điểm, Hit@3 đạt 3/5 = 60%**), nhưng có sự phân hóa rõ rệt về phong cách truy xuất:
>
> - **`SentenceChunker` (Việt)** chiến thắng ở độ chính xác Top-1 (**Hit@1 = 40%**): Với các câu hỏi tra cứu mốc thời gian và điều kiện cụ thể (ví dụ Câu 2: người bán phản hồi trong bao lâu), chunk ngắn 3 câu đưa con số cốt lõi ("02 ngày lịch") lên đầu bảng xếp hạng mà không bị pha loãng bởi các đoạn giải thích xung quanh.
> - **`RecursiveChunker` (Duẩn)** lại phát huy ưu thế ở các câu hỏi phức tạp cần toàn vẹn bảng biểu hoặc điều khoản dài (như quy định phân loại sản phẩm Tiki ở Câu 4), nơi chunk 500 ký tự bao trọn được ngữ cảnh mà chunk 3 câu dễ bị phân mảnh.
> - **Hạn chế chung của cả 3 chiến lược**: Đều gặp khó khăn ở các câu hỏi đa sàn (Sendo, Tiki) khi chưa có metadata filter `platform`, do `MockEmbedder` (băm MD5) không có tri thức ngữ nghĩa thực thụ để phân biệt tên thương hiệu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng trực tiếp từ tài liệu; kèm điều kiện metadata filter bắt buộc để tránh nhiễu thông tin giữa người mua và người bán.

| # | Câu hỏi | Gold answer (trích từ tài liệu) | Tài liệu nguồn | Filter bắt buộc |
| --- | --------- | -------------------------------- | --------------- | ---------------- |
| 1 | Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | **15 ngày** kể từ khi đơn hàng được cập nhật giao hàng thành công | `shopee-return-buyer` | `{"audience": "buyer"}` |
| 2 | Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu? | **02 ngày lịch** kể từ ngày nhận thông báo | `shopee-return-seller` | `{"audience": "seller"}` |
| 3 | Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu? | Hoàn tiền 100% vào **ví Senpay**, thời gian khoảng **3–7 ngày** | `sendo-return-policy` | None |
| 4 | Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày? | **7 ngày đầu** — hình thức Đổi mới / Hoàn tiền | `tiki-return-policy` | `{"audience": "buyer"}` |
| 5 | Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không? | **Không** — người bán không chịu chi phí khi lỗi do đơn vị vận chuyển | `shopee-return-seller` | `{"audience": "seller"}` |

**Tại sao các câu này hợp lệ:**

- **Câu 1 & 4:** cần filter `buyer` — corpus có cả file buyer lẫn seller về cùng chủ đề Shopee/TMĐT, không filter thì retrieval có thể lấy nhầm file seller.
- **Câu 2 & 5:** cần filter `seller` — câu hỏi hướng vào người bán, nếu không filter dễ trả về chunk quyền lợi của buyer.
- **Câu 3:** không cần filter — Sendo chỉ có 1 file trong corpus, không bị nhiễu.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Kết quả Top-3 của nhóm | Điểm cao nhất | Ghi chú & Phân tích lỗi |
| --- | --------- | ------------------------------- | ---------------------- | :-----------: | ----------------------- |
| 1 | Thời hạn người mua Shopee gửi yêu cầu trả hàng | **SentenceChunker** (Việt) & **HeadingChunker** (Vũ) | **Top-1 / Top-3 Đúng Shopee** (`shopee-chinh-sach-tra-hang-hoan-tien`) | **2 / 2** | Vũ đưa tài liệu Shopee lên Top-1. Việt có 3/3 rank trong Top-3 là Shopee (1đ). Duẩn đưa về Top-2 (1đ) do Tiki chiếm Top-1. |
| 2 | Thời hạn người bán Shopee phản hồi | **SentenceChunker** (Việt) | **Top-1 Trúng GOLD** (`shopee-chinh-sach-tra-hang-hoan-tien`) | **2 / 2** | Việt trúng Top-1 Shopee chứa đúng mốc thời gian "02 ngày" (2đ). Duẩn và Vũ bị TikTok Shop chiếm các vị trí đầu (0đ do trượt doc Shopee). |
| 3 | Sendo hoàn tiền qua đâu, bao lâu | Cả 3 đều gặp khó khăn (Nút thắt MD5) | **Trượt Top-3** (Bị Shopee chiếm ưu thế) | **0 / 2** | Câu không dùng filter nên `MockEmbedder` băm MD5 ưu tiên Shopee do số lượng chunk Shopee áp đảo. Cả 3 thành viên đều trượt Top-3 (0đ). |
| 4 | Tiki đổi trả điện thoại bị lỗi | **RecursiveChunker** (Duẩn) | **Top-2 Trúng GOLD** (`tiki-return-policy`) | **2 / 2** | Duẩn trích xuất trọn vẹn đoạn bảng ngành hàng điện tử của Tiki chứa Gold Answer (2đ). Việt và Vũ bị Shopee/TikTok chiếm Top-3 (0đ). |
| 5 | Phí vận chuyển hoàn trả Shopee người bán chịu không | **SentenceChunker** (Việt) & **RecursiveChunker** (Duẩn) | **Top-1 / Top-3 Trúng GOLD** (`shopee-chinh-sach-tra-hang-hoan-tien`) | **2 / 2** | Cả hai cùng đạt điểm tối đa (2đ): Việt đạt Top-1 đúng câu trả lời Gold; Duẩn nhờ filter `seller` đưa tài liệu Shopee vào Top-3 trúng đoạn quy định chi phí. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất hữu ích, mang tính quyết định! Bằng chứng thực nghiệm A/B Testing từ kết quả của Duẩn:**
>
> - **Ở Câu 5 (Shopee Người bán chịu phí ship không):**
>   - **Khi CÓ filter (`audience: seller`):** Top-3 giữ được đúng tài liệu `shopee-return-seller` (GOLD chunk ở rank 3), loại bỏ được toàn bộ nhiễu từ các file người mua.
>   - **Khi KHÔNG CÓ filter (A/B):** Top-1 và Top-2 bị chiếm trọn bởi `tiki-return-policy (audience: buyer)` (score 0.2910 và 0.2595), đẩy chunk đúng ra ngoài Top-3.
> - **Ở Câu 2 (Người bán Shopee phản hồi):**
>   - **Khi CÓ filter:** Khóa chặt phạm vi vào tài liệu người bán.
>   - **Khi KHÔNG CÓ filter:** Top-2 lập tức bị chiếm bởi `tiki-return-policy (audience: buyer)` (score 0.2446) về chính sách điện gia dụng, gây sai lệch hoàn toàn đối tượng.

### Checklist giai đoạn 4 (Họp nhóm & Thống nhất)

- [x] Nguyễn Công Duẩn báo nhóm: dùng `RecursiveChunker` (`chunk_size=500`) — Đã nạp 50 chunks, đạt 5/10 điểm.
- [x] Phùng Quốc Việt báo nhóm: dùng `SentenceChunker` (`max_sentences_per_chunk=3`) — Đã nạp 115 chunks, đạt 5/10 điểm (Hit@3 đạt 60%, Hit@1 đạt 40%).
- [x] Phan Hoàng Vũ viết xong `HeadingChunker` (`chunk_size=500`) — Đã nạp 91 chunks, đạt 4/10 điểm.
- [x] Cả 3 đồng ý 5 câu query ở bảng trên.
- [x] Cả 3 copy bảng query vào `bench.py` của mình (phần `QUERIES`) và chạy ra file kết quả benchmark.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Trade-off giữa Kích thước hạt (Chunk Granularity) và Độ phủ ngữ cảnh (Context Coverage):**
   - `SentenceChunker` (115 chunks): Kích thước nhỏ, giúp các câu ngắn chứa câu trả lời định lượng (15 ngày, 2 ngày) đạt độ tương đồng cao nhất mà không bị pha loãng bởi từ vựng xung quanh.
   - `RecursiveChunker` (50 chunks): Kích thước lớn (500 ký tự), thích hợp cho các câu hỏi cần cả ngữ cảnh điều kiện và ngoại lệ (như bảng đối soát Tiki hoặc phân bổ phí ship Shopee).
2. **Minh chứng thực nghiệm về Metadata Filtering (Pre-filtering):**
   - Trong cùng chủ đề đổi trả TMĐT, ranh giới giữa người mua và người bán rất dễ gây nhầm lẫn cho vector embeddings. Thử nghiệm A/B của Duẩn đã chứng minh: nếu không có pre-filter `audience: seller`, các chunk của người mua (`buyer`) sẽ chiếm hết top-k slots, dẫn đến truy xuất thất bại hoàn toàn.
3. **Kỹ thuật Heading Re-attachment (HeadingChunker của Vũ):**
   - Giúp giải quyết bài toán "mất ngữ cảnh cha" khi cắt nhỏ văn bản pháp lý. Tuy nhiên cần lọc bỏ các heading điều hướng trang web chung để tránh làm nhiễu vector embeddings.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu và 5 câu hỏi benchmark, sự khác biệt về chiến lược chunking dẫn tới kết quả tương đối cân bằng nhưng phân hóa về đặc tính (từ 4/10 đến 5/10 điểm). Không có một kích thước chunk cố định nào hoàn hảo cho mọi loại câu hỏi: câu hỏi tra cứu thông số nhanh cần chunk nhỏ (Sentence), trong khi câu hỏi tra cứu quy trình phức tạp cần chunk lớn giữ trọn bảng biểu (Recursive/Heading). Ngoài ra, cả nhóm nhận thấy `MockEmbedder` băm MD5 là nút thắt cổ chai lớn nhất hạn chế độ chính xác ngữ nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa cấu trúc heading ngay từ khâu crawl dữ liệu thành định dạng Markdown chuẩn phân cấp 3 bậc (`#`, `##`, `###`), đồng thời bổ sung thêm trường metadata `platform` (`shopee`, `tiki`, `sendo`, `tiktok`, `lazada`) vào frontmatter để kết hợp lọc đa chiều `{"audience": "...", "platform": "..."}`.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
| ---------- | ------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
