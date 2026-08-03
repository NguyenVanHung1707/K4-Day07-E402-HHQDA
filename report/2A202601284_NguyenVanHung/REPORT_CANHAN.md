# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Hưng
**Mã sinh viên:** 2A202601284
**Lớp / Biến thể:** K4 (Truy xuất Chính sách Thương mại điện tử / Hỗ trợ khách hàng)
**Ngày:** 03/08/2026

> **Báo cáo cá nhân nộp riêng cho sinh viên Nguyễn Văn Hưng.** Phần nhóm được trình bày riêng trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60/60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine đo góc giữa hai vector biểu diễn văn bản trong không gian đa chiều. Độ tương tự cosine cao (gần 1.0) có nghĩa là hai đoạn văn bản có cùng hướng định vị ngữ nghĩa, biểu thị sự tương đồng cao về mặt ý nghĩa bất kể độ dài ngắn của từng câu.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** "Chính sách đổi trả hàng áp dụng trong vòng 7 ngày kể từ khi nhận hàng thành công."
- **Câu B:** "Khách hàng có quyền gửi yêu cầu hoàn trả sản phẩm trong thời hạn 7 ngày."
- **Tại sao tương đồng:** Cả hai câu đều diễn đạt cùng một nội dung về quyền và thời hạn 7 ngày đổi trả sản phẩm cho người mua, sử dụng các cụm từ ngữ nghĩa tương đương ("đổi trả hàng" = "hoàn trả sản phẩm", "trong vòng 7 ngày" = "thời hạn 7 ngày").

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** "Chính sách đổi trả hàng áp dụng trong vòng 7 ngày kể từ khi nhận hàng thành công."
- **Câu B:** "Người bán phải hoàn tất đăng ký giấy phép kinh doanh trước khi niêm yết gian hàng."
- **Tại sao khác:** Hai câu hướng tới hai đối tượng hoàn toàn khác nhau trong hệ thống TMĐT (`customer_role`: `buyer` vs `seller`) và đề cập tới hai quy trình độc lập (quy trình hoàn trả sản phẩm vs thủ tục pháp lý niêm yết).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid chịu ảnh hưởng mạnh bởi độ dài vector (tương ứng với số lượng từ/ký tự của văn bản). Hai câu có cùng nội dung nhưng một câu viết dài gấp đôi sẽ có khoảng cách Euclid rất lớn. Cosine Similarity loại bỏ hoàn toàn yếu tố độ dài nhờ việc chuẩn hóa vector, chỉ đánh giá hướng ngữ nghĩa thực sự của văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) $= \text{chunk\_size} - \text{overlap} = 500 - 50 = 450$
> - Công thức: $\text{Số chunk} = \left\lceil \frac{\text{độ\_dài} - \text{overlap}}{\text{step}} \right\rceil = \left\lceil \frac{10000 - 50}{450} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \left\lceil 22.111 \right\rceil = 23$
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Trình bày phép tính:*
> - Bước nhảy mới $= 500 - 100 = 400$
> - Số chunk mới $= \left\lceil \frac{10000 - 100}{400} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \left\lceil 24.75 \right\rceil = 25$
> *Đáp án:* Số lượng chunk tăng từ **23 lên 25 chunks** (tăng thêm 2 chunks).
> *Lý do tăng overlap:* Tăng độ chồng chéo giúp duy trì mạch ngữ cảnh liên tục ở phần ranh giới giữa các chunk kế tiếp, tránh hiện tượng câu văn hoặc ý tưởng quan trọng bị ngắt đôi dẫn tới mất mát thông tin khi retriever thực hiện tìm kiếm vector.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận khi lập trình các phần chính trong gói `src`:

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\n+', text)` để tách văn bản dựa theo các dấu câu kết thúc câu (`.`, `!`, `?`) hoặc ký tự xuống dòng. Các câu sau khi tách được làm sạch khoảng trắng và gom thành các chunk với số lượng câu tối đa `max_sentences_per_chunk`. Xử lý trường hợp ngoại lệ văn bản rỗng hoặc không có dấu câu bằng cách trả về danh sách phù hợp.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán đệ quy thử nghiệm danh sách phân cách theo ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi đoạn văn bản có độ dài $\le \text{chunk\_size}$ hoặc không còn dấu phân cách nào. Thuật toán tách văn bản theo phân cách hiện tại, nếu mảnh nào vẫn vượt quá `chunk\_size` thì gọi đệ quy `_split` với danh sách phân cách tiếp theo, còn các mảnh nhỏ hơn được gom liên tiếp lại sao cho tổng độ dài không vượt quá kích thước chunk tối đa.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong `add_documents`, từng `Document` được trích xuất metadata (bảo toàn `doc_id`), tạo vector nhúng thông qua `self._embedding_fn` và lưu dưới dạng dict vào danh sách trong bộ nhớ `self._store`. Trong `search`, câu hỏi `query` được nhúng thành vector, tính điểm tương đồng Cosine Similarity với vector của từng chunk bằng `compute_similarity`, sau đó sắp xếp danh sách kết quả theo điểm `score` giảm dần và lấy `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện tiền lọc (pre-filtering): duyệt qua `self._store` và chỉ giữ lại những chunk có `metadata` khớp hoàn toàn với tất cả các cặp key-value trong `metadata_filter`, sau đó mới tính điểm tương đồng trên tập đã lọc. `delete_document` thực hiện lọc bỏ tất cả record có `doc_id`, `id` hoặc `metadata['doc_id']` trùng với `doc_id` truyền vào và trả về `True` nếu có ít nhất 1 chunk bị loại bỏ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Triển khai mô hình RAG (Retrieval-Augmented Generation): Gọi `store.search(question, top_k=top_k)` để thu thập các chunk thông tin có độ tương đồng cao nhất. Trích xuất nội dung `content` của các chunk, hợp nhất thành chuỗi ngữ cảnh `context`, xây dựng prompt chuẩn (`Context:\n...\n\nQuestion: ...\nAnswer:`) và truyền cho hàm `llm_fn` để tạo ra câu trả lời chính xác dựa trên tri thức được cung cấp.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua toàn bộ bộ kiểm thử unit test (`pytest tests/ -v`).

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\hung\VinAI\Lab\Lab7\DAY07_2A202601284_NguyenVanHung
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.19s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng trong 7 ngày. | Khách hàng có thể đổi trả trong vòng 7 ngày. | cao | -0.0022 (Mock) / 0.88 (Semantic) | Đúng |
| 2 | Quy định thanh toán trực tuyến qua thẻ. | Hướng dẫn thanh toán bằng thẻ tín dụng và ATM. | cao | 0.0546 (Mock) / 0.82 (Semantic) | Đúng |
| 3 | Chính sách đổi trả sản phẩm lỗi. | Quy định dành cho người bán khi niêm yết sản phẩm. | thấp | -0.0193 (Mock) / 0.21 (Semantic) | Đúng |
| 4 | Hỗ trợ giao hàng hỏa tốc trong 2 giờ. | Phương thức vận chuyển tiết kiệm toàn quốc. | cao | 0.1463 (Mock) / 0.65 (Semantic) | Đúng |
| 5 | Hướng dẫn bảo mật thông tin cá nhân. | Trái cây tươi đóng gói giao trong ngày. | thấp | 0.0052 (Mock) / 0.08 (Semantic) | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Trình nhúng mặc định `MockEmbedder` băm (hash) chuỗi ký tự nên các giá trị similarity score nhận được dao động quanh 0 (-0.02 đến 0.14) và gần như ngẫu nhiên về mặt từ ngữ. Khi chuyển sang mô hình nhúng thực sự (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`), các câu cùng ngữ nghĩa đạt điểm tương đồng cao (>0.80) ngay cả khi không trùng lặp 100% từ ngữ. Điều này khẳng định embedding ngữ nghĩa thực sự biểu diễn vị trí văn bản dựa theo bản chất ý nghĩa khái niệm chứ không chỉ so sánh chuỗi ký tự bề mặt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy 5 câu hỏi đánh giá benchmark K4 của nhóm trên mã nguồn cá nhân trong gói `src` với tập dữ liệu `data/data_shopee/`:

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Dung lượng tối đa đối với bằng chứng ảnh/video khi yêu cầu Trả hàng/Hoàn tiền là bao nhiêu? Nếu vượt quá dung lượng thì làm thế nào? (`filter: customer_role="both"`) | "Dung lượng tối đa: Hình ảnh không quá 5MB/ảnh, Video không quá 100 MB/video (tối đa 1 phút)... tải lên YouTube hoặc Google Drive..." | 0.2752 | Có | "Hình ảnh không quá 5MB/ảnh, Video không quá 100MB. Nếu quá dung lượng hãy upload Youtube/Drive để công khai và gửi link." |
| 2 | Thời gian xử lý yêu cầu Trả hàng/Hoàn tiền và thời gian hoàn tiền trên Shopee mất bao lâu? (`filter: customer_role="buyer"`) | "Thời gian xử lý: 3 - 5 ngày làm việc... Thời gian hoàn tiền: 1 - 14 ngày làm việc tùy phương thức thanh toán." | 0.3545 | Có | "Thời gian xử lý yêu cầu là 3-5 ngày làm việc và thời gian hoàn tiền từ 1-14 ngày làm việc." |
| 3 | Điều kiện bắt buộc về thông tin tài khoản để sử dụng Voucher ShopeeFood trong gói ShopeeVIP là gì? (`filter: category="voucher-khuyen-mai"`) | "Việc liên kết chỉ thành công khi số điện thoại đăng ký tài khoản Shopee và tài khoản ShopeeFood giống nhau..." | 0.1899 | Có | "Số điện thoại đăng ký tài khoản Shopee và ShopeeFood bắt buộc phải trùng khớp nhau." |
| 4 | Số lượng mã giảm giá tối đa có thể lưu vào Kho Voucher trên ứng dụng Shopee là bao nhiêu? (`unfiltered`) | "Số lượng các mã giảm giá có thể lưu vào Kho Voucher hoàn toàn không bị giới hạn." | 0.1760 | Có | "Số lượng mã giảm giá lưu vào Kho Voucher hoàn toàn không bị giới hạn." |
| 5 | Người dùng có thể theo dõi trạng thái xử lý Trả hàng/Hoàn tiền qua những kênh nào ngoài mục Đơn Mua? (`filter: customer_role="both"`) | "Tất cả các thông tin/trạng thái xử lý Trả hàng hoàn tiền sẽ được cập nhật qua Mục Thông báo, Email, Banner điện thoại và Chatbot Tép Thám Tử..." | 0.1433 | Có | "Có thể theo dõi qua Mục Thông báo app, Email liên kết, biểu ngữ điện thoại và Trò Chuyện Với Shopee." |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ việc thực thi:**
> Tiền lọc bằng siêu dữ liệu (`metadata_filter={"customer_role": "both"}` hoặc `{"category": "voucher-khuyen-mai"}`) giúp khoanh vùng tập dữ liệu truy xuất chính xác, loại bỏ hẳn nhiễu từ các văn bản không thuộc phạm vi trước khi tính toán vector similarity.


---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
