# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Công Đăng -2A202601280
**Nhóm:HHQDA**
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai vector embedding gần như cùng hướng trong không gian nhiều chiều (giá trị gần 1.0), nghĩa là hai đoạn văn bản mang ý nghĩa (semantic) tương đồng, bất kể chúng dùng từ ngữ khác nhau hay độ dài câu khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Tôi rất vui khi được gặp bạn."
- Câu B: "Tôi cảm thấy hạnh phúc khi gặp lại bạn."
- Tại sao tương đồng: hai câu diễn đạt cùng một cảm xúc (vui/hạnh phúc khi gặp gỡ) bằng từ vựng khác nhau (đồng nghĩa khác từ) nên vector embedding của chúng có hướng gần giống nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Hôm nay trời mưa rất to."
- Câu B: "Giá cổ phiếu công ty tăng mạnh trong quý này."
- Tại sao khác: hai câu thuộc hai chủ đề hoàn toàn không liên quan (thời tiết vs tài chính), nên vector embedding của chúng nằm theo các hướng khác nhau, gần vuông góc.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chỉ đo góc (hướng ngữ nghĩa) giữa hai vector, không quan tâm độ dài (magnitude) của vector — vốn có thể bị ảnh hưởng bởi độ dài văn bản hoặc cách chuẩn hóa (normalization) của model. Euclidean distance lại nhạy với magnitude, nên hai câu cùng nghĩa nhưng một câu dài/nhiều token hơn có thể bị tính là "xa nhau" dù hướng vector gần như trùng nhau — gây sai lệch khi so sánh ngữ nghĩa văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_
> Bước trượt (step) = chunk_size − overlap = 500 − 50 = 450 ký tự.
> Vị trí bắt đầu (start) chạy 0, 450, 900, ..., dừng khi start + chunk_size ≥ 10000, tức start ≥ 9500.
> start cuối cùng thỏa điều kiện dừng là 9450 (vì 9450 + 500 = 9950 < 10000, chưa dừng) → start tiếp theo 9900 (9900+500=10400 ≥ 10000 → dừng).
> Số chunk = số giá trị start trong dãy {0, 450, 900, ..., 9900} = 9900/450 + 1 = 23.
>
> **Đáp án: 23 chunks** (đã xác minh bằng code, khớp với công thức đề bài đưa ra).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Overlap tăng 50 → 100 làm step giảm (500−100=400 thay vì 450), nên số chunk **tăng** từ 23 lên 25 (đã kiểm chứng bằng code). Đánh đổi (trade-off): overlap lớn giúp giữ ngữ cảnh liên tục qua ranh giới chunk (giảm nguy cơ cắt đứt một ý ngay giữa câu/đoạn, cải thiện độ phủ ngữ nghĩa khi truy xuất — retrieval), nhưng đổi lại tốn thêm chi phí tính toán và lưu trữ (nhiều chunk hơn → nhiều lần gọi embedding hơn) và tạo nội dung trùng lặp giữa các chunk liền kề.

---

## 2. Hướng tiếp cận của tôi (`RecursiveChunker.chunk`) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Tôi cấu hình `chunk_size=350`, `separators=["\n\n", "\n", ". ", " "]` — thử cắt theo ranh giới lớn nhất trước (đoạn văn → dòng → câu → từ) để giữ mạch văn và cấu trúc danh sách bước hướng dẫn trong tài liệu Shopee. `_split` đệ quy: tách `current_text` theo separator ưu tiên cao nhất còn lại, rồi gộp dần các phần nhỏ vào một buffer cho đến ngay trước khi vượt `chunk_size` mới "chốt" thành một chunk; phần nào tự nó đã dài hơn `chunk_size` thì gọi đệ quy `_split` tiếp với separator ưu tiên thấp hơn (ví dụ đoạn quá dài thì thử cắt theo dòng, rồi theo câu, rồi theo từ).
>
> Base case: (1) `len(current_text) <= chunk_size` → trả về nguyên văn bản đó thành 1 chunk; (2) hết danh sách separator (kể cả khi list rỗng ngay từ đầu) → cắt cố định theo `chunk_size` (fixed-size cut) để đảm bảo luôn dừng, không đệ quy vô hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Lưu trữ in-memory bằng `self._store: list[dict]` — mỗi record gồm `id` (dạng `f"{doc.id}_{self._next_index}"`), `content`, `metadata` (shallow-copy qua `dict(doc.metadata)` để tránh mutate object gốc, tự động `setdefault("doc_id", doc.id)` để `delete_document`/lọc theo `doc_id` luôn hoạt động kể cả khi caller không truyền sẵn) và `embedding` (gọi `self._embedding_fn(doc.content)` ngay khi add, không tính lại lúc search). `search` embed câu query đúng 1 lần rồi tính **dot product** (`_dot` tái dùng từ `chunking.py`) giữa vector query và từng embedding đã lưu — vì `MockEmbedder`/`LocalEmbedder` đều chuẩn hóa vector về norm 1 nên dot product ở đây tương đương cosine similarity. Kết quả sort giảm dần theo `score`, cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> **Filter trước, search sau (filter-first):** duyệt `self._store`, chỉ giữ lại record mà **mọi** cặp `key: value` trong `metadata_filter` đều khớp `record["metadata"]` (dùng `all(...)`), rồi mới gọi `_search_records` trên tập đã lọc — cách này vừa đúng ngữ nghĩa yêu cầu, vừa tiết kiệm hơn tính điểm toàn bộ store rồi lọc sau. `delete_document` xóa theo `metadata["doc_id"]` bằng list comprehension loại bỏ mọi chunk có `doc_id` khớp, so sánh độ dài trước/sau để trả về `True`/`False` (không xóa được gì → `False`).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Gọi `store.search(question, top_k=top_k)`; nếu rỗng trả câu fallback báo không tìm thấy thông tin thay vì gọi LLM với context trống. Ghép các chunk truy xuất được thành block `Context` có đánh số `[1] (Nguồn: doc_id)`, `[2] (Nguồn: doc_id)`... để LLM biết trích dẫn từ tài liệu nào (grounding, hỗ trợ truy vết nguồn). Prompt gồm 4 phần: hướng dẫn "chỉ dùng thông tin trong Context, nếu thiếu thì nói rõ không trả lời được" (giảm hallucination), khối `Context`, `Question`, và `Answer:` để mở đầu phần sinh câu trả lời — cuối cùng gọi `self.llm_fn(prompt)` và trả nguyên kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
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

============================== 42 passed in 0.19s ===============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                    | Câu B                                          | Dự đoán                                    | Điểm thực tế (`MockEmbedder`) | Đúng? |
| --- | -------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------ | ----------------------------- | ----- |
| 1   | "Tôi muốn trả lại sản phẩm bị lỗi."                      | "Tôi cần hoàn trả hàng vì sản phẩm hư hỏng."   | cao (đồng nghĩa khác từ)                   | −0.1762 → thấp                | Sai   |
| 2   | "Voucher giảm giá của tôi khi nào hết hạn?"              | "Mã ưu đãi của tôi còn hiệu lực đến ngày nào?" | cao (đồng nghĩa khác từ)                   | 0.2632 → thấp/trung bình      | Sai   |
| 3   | "Làm sao để liên kết tài khoản ShopeeFood?"              | "Thời tiết hôm nay thế nào?"                   | thấp (khác chủ đề hoàn toàn)               | −0.3351 → thấp                | Đúng  |
| 4   | "Thời gian hoàn tiền là bao lâu?"                        | "Thời gian giao hàng dự kiến là bao lâu?"      | cao (cùng miền "thời gian xử lý đơn hàng") | −0.2619 → thấp                | Sai   |
| 5   | "Cách chuẩn bị video bằng chứng khi khiếu nại hàng lỗi." | "Cách nấu phở bò tại nhà."                     | thấp (khác chủ đề hoàn toàn)               | −0.0074 → thấp                | Đúng  |

_(Điểm thực tế lấy trực tiếp từ `compute_similarity(_mock_embed(A), _mock_embed(B))` — số liệu thật, không ước lượng. Ngưỡng quy đổi cao/thấp: score ≥ 0.3 → cao, còn lại → thấp, vì `MockEmbedder` gần như không bao giờ cho vector đồng hướng mạnh.)_

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là Cặp 1: hai câu đồng nghĩa rõ ràng ("trả lại sản phẩm lỗi" vs "hoàn trả hàng vì hư hỏng") lại có điểm **âm** (−0.1762) — thấp hơn cả Cặp 5 gồm hai câu hoàn toàn không liên quan (−0.0074). Điều này không phải do chiến lược chunking hay công thức cosine sai, mà vì `MockEmbedder` sinh vector từ hash MD5 của chuỗi ký tự (không encode ngữ nghĩa), nên hai câu đồng nghĩa nhưng khác từ vựng vẫn cho ra vector gần như ngẫu nhiên so với nhau. Bài học: độ chính xác của cosine similarity phụ thuộc hoàn toàn vào **chất lượng embedding model**, không phải vào công thức toán — cùng 1 công thức `compute_similarity` đúng 100% (đã pass test), nhưng kết quả vô nghĩa nếu model không thực sự "hiểu" ngôn ngữ. Cần chạy lại bảng này với `EMBEDDING_PROVIDER=local` để có dự đoán và thực tế khớp nhau như kỳ vọng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| #                     | Câu hỏi (Query)                                                                                             | Top-1 Chunk truy xuất được (tóm tắt)                                                            | Điểm Score | Có liên quan không? (Relevant)                               | Câu trả lời của Agent (tóm tắt)                                                                    |
| --------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| 1 (Số liệu)           | Thời gian xử lý/hoàn tiền yêu cầu Trả hàng/Hoàn tiền?                                                       | `huong-dan-gui-yeu-cau-tra-hang-hoan-tien` — chunk mở đầu (đoạn giới thiệu, KHÔNG chứa số liệu) | 0.2774     | Không (đúng doc, sai chunk)                                  | Agent lấy ngữ cảnh từ đoạn mở đầu + 2 chunk không liên quan, không có số liệu 3-5 ngày / 1-14 ngày |
| 2 (Điều kiện)         | Điều kiện liên kết Shopee ↔ ShopeeFood?                                                                     | `theo-doi-tinh-trang-tra-hang-hoan-tien` — chunk "Mục Thông báo"                                | 0.2983     | Không                                                        | Agent trả lời lạc đề (dựa trên chunk theo dõi đơn hàng, không phải điều kiện liên kết SĐT)         |
| 3 (Quy trình)         | Các bước gửi yêu cầu Trả hàng/Hoàn tiền trực tiếp?                                                          | `kho-voucher-shopee-la-gi` — danh sách loại Voucher                                             | 0.2332     | Không                                                        | Agent trả lời sai hẳn chủ đề (Voucher thay vì quy trình trả hàng)                                  |
| 4 (Liệt kê)           | Kho Voucher lọc theo những loại nào?                                                                        | `huong-dan-chuan-bi-bang-chung` — đoạn quy định bổ sung bằng chứng                              | 0.3232     | Không                                                        | Agent không liệt kê được các loại Voucher thật                                                     |
| 5 (Ngoại lệ + Filter) | Người bán theo dõi tình trạng Trả hàng/Hoàn tiền qua kênh nào? (`metadata_filter={"customer_role":"both"}`) | `theo-doi-tinh-trang-tra-hang-hoan-tien` — chunk Bước 4 (đúng doc)                              | 0.1832     | Một phần (đúng doc nhờ filter, top-2 mới có "Mục Thông báo") | Agent trả lời đúng doc nguồn nhờ filter loại bớt nhiễu, dù chunk top-1 chưa phải đoạn tối ưu nhất  |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **1** / 5 (chỉ Q5 — nhờ có `metadata_filter`; Q1–Q4 dùng `search()` thường đều lệch)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> _Viết 2-3 câu (điền sau khi demo chéo với các thành viên FixedSizeChunker/SentenceChunker trong nhóm):_

> **Lưu ý minh bạch số liệu:** Bảng trên chạy thật bằng `bench.py` trên corpus `data/data_shopee` (5 tài liệu Shopee thật) với `RecursiveChunker(chunk_size=350)` + **`MockEmbedder`** (vector giả lập từ hash MD5, không phản ánh ngữ nghĩa thật — xem cảnh báo có sẵn trong `main.py`). Vì vậy precision thấp phản ánh đúng hạn chế của MockEmbedder, không hẳn là lỗi của chiến lược chunking. Phân tích sâu hơn (tách riêng ảnh hưởng của chunking vs. embedding) ở mục 6 bên dưới. Trước khi nộp bản cuối, khuyến nghị chạy lại với `EMBEDDING_PROVIDER=local` (cần `pip install -r requirements-local.txt`) để có số liệu phản ánh đúng chất lượng ngữ nghĩa.

---

## 6. Phân tích chuyên sâu Chiến lược Cá nhân (`RecursiveChunker`)

> _Mục bổ sung theo yêu cầu Checkpoint 6 (không nằm trong thang 60 điểm gốc ở đầu file) — đào sâu mục 5 bằng phân tích ở mức chunk thay vì chỉ `doc_id`. Toàn bộ số liệu dưới đây chạy thật trên corpus K4 (`data/data_shopee` — chính sách/hỗ trợ khách hàng Shopee), không dùng dữ liệu K3 (quy định đại học)._

### 6.1. Cấu hình Strategy Cá nhân

- **Strategy Name:** `RecursiveChunker_Size350_Paragraph-Line-Sentence-Word`
- **Thuật toán:** `RecursiveChunker` — đệ quy theo phân cấp separator `["\n\n", "\n", ". ", " "]`, hết separator thì cắt cố định (fixed-size).
- **Tham số:** `chunk_size=350`. _(Lưu ý: `RecursiveChunker` trong codebase của lab này **không có tham số `overlap`** — khác với `FixedSizeChunker`. Đây là một hạn chế thật của thuật toán, không phải thiếu sót khi cấu hình — xem mục 6.4.)_
- **Embedding Model:** `MockEmbedder` (dim=64, vector giả lập từ hash MD5 nội dung). Đã thử cài `sentence-transformers` để chạy `LocalEmbedder` thật nhưng môi trường chạy thử bị giới hạn thời gian tải model nên chưa hoàn tất — số liệu dưới đây phản ánh đúng hành vi MockEmbedder, cần chạy lại `EMBEDDING_PROVIDER=local` để có số liệu ngữ nghĩa thật trước khi nộp.

### 6.2. Kết quả Benchmark & Đánh giá mức Chunk (Precision & Coherence)

Chấm theo sự xuất hiện của **chuỗi đặc trưng (gold string)** trong nội dung Top-3 thật (không chỉ `doc_id`):

| Query ID | Dạng Query        | Gold Document (thật)                                | Trạng thái Retrieve (mức Chunk)                                                                                                                                      | Precision Top-3 (gold string)             | Chunk Coherence (độ toàn vẹn)                                                                                                                                                                                                    |
| -------- | ----------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q1       | Số liệu           | `huong-dan-gui-yeu-cau-tra-hang-hoan-tien.md`       | Đúng doc nhưng SAI chunk — Top-1 là đoạn mở đầu (`chunk_idx=0`), số liệu thật ("3 - 5 ngày làm việc", "1 - 14 ngày làm việc") nằm ở `chunk_idx=8,9`, không lọt Top-3 | 0/3                                       | Con số/đơn vị được giữ nguyên vẹn trong đúng 1 chunk (không bị cắt giữa số và đơn vị), nhưng chunk đó không được xếp hạng cao                                                                                                    |
| Q2       | Điều kiện         | `huong-dan-su-dung-voucher-shopeefood-shopeevip.md` | Không lọt Top-3 — Top-1 lệch sang tài liệu theo dõi đơn hàng không liên quan                                                                                         | 0/3                                       | Câu điều kiện đầy đủ ("số điện thoại đăng ký tài khoản Shopee và tài khoản ShopeeFood giống nhau") nằm nguyên trong 1 chunk (`chunk_idx=2`, 285 ký tự) — chunker giữ toàn vẹn câu, vấn đề nằm ở xếp hạng chứ không phải chunking |
| Q3       | Quy trình         | `huong-dan-gui-yeu-cau-tra-hang-hoan-tien.md`       | Bị cắt ngang quy trình — Top-1 sai hẳn chủ đề, Top-2 đúng doc nhưng là đoạn "Lưu ý" cuối bài (không phải quy trình 8 bước)                                           | 0/3                                       | **Bị vỡ:** quy trình 8 bước gốc bị `RecursiveChunker` cắt thành 4 chunk rời (`chunk_idx=1,2,3,4`), không chunk nào chứa trọn quy trình                                                                                           |
| Q4       | Liệt kê           | `kho-voucher-shopee-la-gi.md`                       | Không lọt Top-3                                                                                                                                                      | 0/3                                       | Danh sách 7 loại Voucher bị cắt làm 2 chunk (`chunk_idx=2`: 5 loại đầu; `chunk_idx=3`: "Scan & Pay"/"Từ đối tác") — liệt kê không trọn vẹn trong 1 chunk                                                                         |
| Q5       | Ngoại lệ / Filter | `theo-doi-tinh-trang-tra-hang-hoan-tien.md`         | Đúng doc khi CÓ filter (Top-1, Top-2); SAI hoàn toàn khi KHÔNG filter (toàn bộ Top-3 là tài liệu`customer_role=buyer`)                                               | 1/3 (có filter) so với 0/3 (không filter) | Chunk "Mục Thông báo" (`chunk_idx=3`) chứa đúng kênh theo dõi, được giữ toàn vẹn (1 đoạn Markdown hoàn chỉnh)                                                                                                                    |

### 6.3. Phân tích A/B Metadata Filter (Query Q5)

**Khi KHÔNG dùng filter (`store.search()`):**
Top-3 = `huong-dan-gui-yeu-cau-tra-hang-hoan-tien` (0.2893), `kho-voucher-shopee-la-gi` (0.2280), `huong-dan-su-dung-voucher-shopeefood-shopeevip` (0.1882) — **cả 3 đều `customer_role=buyer`**, không có tài liệu nào áp dụng cho seller. Agent sẽ trả lời đúng "trend" chủ đề (trả hàng/hoàn tiền) nhưng sai đối tượng (không phải kênh dành cho người bán).

**Khi CÓ dùng filter (`store.search_with_filter(..., metadata_filter={"customer_role": "both"})`):**
Không gian tìm kiếm giảm từ **53 → 20 chunk** (chỉ giữ 2/5 tài liệu có `customer_role=both`). Top-3 gồm 2 chunk đúng nguồn (`theo-doi-tinh-trang-tra-hang-hoan-tien`, score 0.1832 & 0.1735) — Top-2 chứa đúng câu trả lời ("Mục Thông báo trên Ứng dụng Shopee").

**Kết luận:** Lọc metadata trước (filter-first) loại bỏ đúng 33/53 chunk sai đối tượng _trước khi_ vector search chạy, nên dù `MockEmbedder` yếu (không hiểu ngữ nghĩa), kết quả vẫn cải thiện rõ rệt (từ 0/3 gold-hit lên có chunk đúng ở Top-2). Đây là bằng chứng thực nghiệm cho thấy **metadata filter bù đắp được một phần chất lượng embedding kém** — quan trọng hơn cả việc chọn chiến lược chunking trong trường hợp này.

### 6.4. Failure Case & Nguyên nhân (Query Q3 — Quy trình)

**Hiện tượng (verified bằng cách in trực tiếp output `RecursiveChunker(chunk_size=350)` trên `huong-dan-gui-yeu-cau-tra-hang-hoan-tien.md`):**
Khối "Cách 1: Gửi yêu cầu trực tiếp tại trang đơn hàng" (8 bước liên tục) dài hơn nhiều so với `chunk_size=350`, bị cắt thành **4 chunk rời**:

- `chunk[1]` (254 ký tự): Bước 1–3 (thiếu 2 lựa chọn con của Bước 3)
- `chunk[2]` (296 ký tự): tiếp tục 2 lựa chọn của Bước 3
- `chunk[3]` (313 ký tự): Bước 4–7
- `chunk[4]` (205 ký tự): tiếp tục Bước 7 + Bước 8

Vì `top_k=3` không đủ để gom lại cả 4 chunk, Agent chỉ nhận được một phần quy trình (hoặc — như benchmark thật ở trên cho thấy — thậm chí không chunk nào trong 4 chunk này lọt vào Top-3 vì bị các chunk chủ đề khác (Voucher) xếp hạng cao hơn).

**Nguyên nhân sâu xa:**

1. `chunk_size=350` quá nhỏ so với độ dài trung bình một quy trình nhiều bước trong help center Shopee (~800–900 ký tự cho quy trình 8 bước).
2. `RecursiveChunker` trong codebase **không hỗ trợ `overlap`** (khác `FixedSizeChunker`) → mất hoàn toàn phần nối ngữ cảnh giữa 2 chunk liên tiếp, không có cơ chế "cầu nối" như overlap mang lại.
3. Xếp hạng theo toàn văn chunk khiến chunk chứa "Bước 4–7" (nhiều từ hành động) và chunk chứa "Bước 1–3" (nhiều từ bối cảnh mở đầu) cạnh tranh điểm số không đều, dù cùng thuộc 1 quy trình.

**Đề xuất cải tiến:**

- Tăng `chunk_size` lên khoảng 600–700 cho các tài liệu dạng hướng dẫn nhiều bước (loại tài liệu phổ biến nhất trong domain Shopee help center).
- Bổ sung cơ chế overlap cho `RecursiveChunker` (hiện chưa có trong code) để giữ một phần ngữ cảnh nối giữa 2 chunk liên tiếp.
- Cân nhắc chunk theo heading Markdown (`### Cách 1`, `### Cách 2`) thay vì thuần túy theo dòng/khoảng trắng, để gom trọn 1 "Cách" thực hiện thành 1 đơn vị chunk.

### 6.5. Đóng góp vào `REPORT_NHOM.md`

**So sánh Strategy:** `RecursiveChunker` (`chunk_size=350`, không overlap) tôn trọng ranh giới đoạn/dòng/câu tốt hơn cắt cứng thuần túy (không bao giờ cắt giữa từ), nhưng với các quy trình nhiều bước dài hơn `chunk_size`, nó vẫn bị vỡ tính toàn vẹn (coherence) tương tự `FixedSizeChunker` — vì thiếu overlap để bù đắp. Khuyến nghị nhóm: (1) tăng `chunk_size` cho tài liệu dạng quy trình, (2) đánh giá lại toàn bộ benchmark bằng `EMBEDDING_PROVIDER=local` thay vì Mock trước khi chốt kết luận "chiến lược nào tốt nhất", vì với Mock, sai số ngữ nghĩa lấn át gần như hoàn toàn ảnh hưởng thật của chunking (Q1–Q4 đều 0/3 bất kể coherence chunk tốt hay xấu).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Khởi động (Warm-up)                             | 5 / 5                                                                                                                                    |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10                                                                                                                                  |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30 (42/42 test pass)                                                                                                                |
| Dự đoán độ tương tự (Similarity Predictions)    | 4 / 5 (làm đủ, nhưng 3/5 dự đoán sai do đặc thù`MockEmbedder` — cần chạy lại bằng embedding thật)                                        |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 (chạy đủ 5 query thật, nhưng chỉ 1/5 có chunk liên quan trong Top-3 vì`MockEmbedder`; đã bù bằng phân tích sâu mức-chunk ở mục 6) |
| **Tổng phần cá nhân**                           | **55 / 60**                                                                                                                              |
