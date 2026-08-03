# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nhữ Văn Hùng
**Nhóm:** Nhóm A5
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao có nghĩa là hai vector biểu diễn ngữ nghĩa của hai đoạn văn bản hướng về cùng một phía trong không gian vector đa chiều (góc giữa chúng rất nhỏ). Điều này biểu thị rằng hai đoạn văn bản có sự tương đồng rất cao về mặt ý nghĩa, nội dung ngữ nghĩa và ngữ cảnh, bất kể độ dài hay số lượng từ của chúng khác biệt thế nào.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có quyền gửi yêu cầu đổi trả nếu sản phẩm nhận được bị lỗi kỹ thuật."
- Câu B: "Khách hàng được phép đề nghị hoàn trả lại hàng hóa nếu phát hiện có hư hỏng từ nhà sản xuất."
- Tại sao tương đồng: Cả hai câu đều dùng các từ đồng nghĩa/gần nghĩa ("người mua" - "khách hàng", "yêu cầu đổi trả" - "đề nghị hoàn trả lại hàng hóa", "bị lỗi kỹ thuật" - "có hư hỏng từ nhà sản xuất") và cùng truyền tải chung một thông điệp chính sách mua bán.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quy trình thanh toán qua ứng dụng ngân hàng được mã hóa bảo mật 2 lớp."
- Câu B: "Người bán chịu trách nhiệm đăng tải hình ảnh và mô tả sản phẩm chính xác."
- Tại sao khác: Hai câu nói về hai đối tượng và chủ đề hoàn toàn khác nhau (công nghệ thanh toán bảo mật vs trách nhiệm đăng tin bán hàng của người bán), không có sự liên quan ngữ nghĩa nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo khoảng cách hình học trực tiếp giữa hai đầu mút vector nên bị ảnh hưởng rất mạnh bởi độ dài văn bản (văn bản dài hơn có vector lớn hơn và bị kéo ra xa). Độ tương tự cosine chỉ đo góc giữa hai vector, do đó loại bỏ hoàn toàn ảnh hưởng của độ dài văn bản và phản ánh chính xác hơn mối quan hệ ngữ nghĩa thuần túy.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Áp dụng công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> Phép tính cụ thể:
> `số lượng chunk = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*
> Khi overlap tăng lên 100, số lượng chunk sẽ tăng lên: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks. Chúng ta muốn tăng độ chồng chéo để bảo toàn tối đa ngữ cảnh liên tục giữa các chunk kế tiếp, tránh việc câu hoặc thông tin quan trọng bị cắt đứt nửa chừng ngay tại ranh giới phân chia chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceWithOverlapChunker.chunk` (Chiến lược của tôi — Thành viên 5)** — hướng tiếp cận:
> Tôi triển khai lớp `SentenceWithOverlapChunker` theo đúng vai trò Thành viên 5 trong `REPORT_NHOM.md`. Hàm sử dụng regex `re.split(r'(?<=[.!?])\s+|\n+', text)` để phân tách văn bản thành danh sách từng câu đơn lẻ mà vẫn giữ nguyên vẹn ranh giới câu. Sau đó, tôi gom các câu theo nhóm kích thước `max_sentences=3` với bước trượt `step = max(1, max_sentences - overlap)` (mặc định `overlap=1`). Cơ chế trượt gối đầu 1 câu giữa các chunk liền kề giúp bảo toàn trọn vẹn ngữ cảnh liên tục giữa các ý, tránh đứt đoạn thông tin ở ranh giới phân chia.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi kiểm tra xem ChromaDB có khả dụng hay không. Nếu có, khi thêm document, tôi tạo ra các ID duy nhất trong ChromaDB bằng cách ghép ID gốc với một số đếm tự tăng (`doc_id##index`) nhằm tránh xung đột trùng lặp ID khi ghi đè, đồng thời thiết lập mặc định trường `doc_id` trong metadata là ID gốc để phục vụ truy vấn và xóa. Nếu ChromaDB không sẵn có, tôi lưu trữ dưới dạng list các dictionary bản ghi trong bộ nhớ.
> Khi `search`, tôi sinh embedding cho câu truy vấn và tính độ tương tự cosine của nó với tất cả các bản ghi (sử dụng truy vấn trực tiếp từ ChromaDB hoặc tính toán in-memory thông qua hàm `compute_similarity`), sau đó sắp xếp các kết quả có điểm score giảm dần để lấy ra top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Để thực hiện `search_with_filter`, tôi tiến hành lọc dữ liệu trước (pre-filtering): lọc danh sách in-memory dựa trên sự khớp hoàn toàn của các trường trong `metadata_filter` hoặc truyền tham số `where` cho ChromaDB, sau đó mới tính độ tương tự và xếp hạng trên các bản ghi thỏa mãn điều kiện lọc.
> Với `delete_document`, tôi thực hiện xóa toàn bộ các bản ghi trong list lưu trữ in-memory hoặc trong ChromaDB bằng cách so khớp cả ID của bản ghi lẫn trường `doc_id` trong metadata với ID cần xóa, trả về True nếu có bất kỳ chunk nào bị xóa và ngược lại.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đầu tiên, tôi dùng `EmbeddingStore` để truy xuất top_k chunk văn bản có liên quan nhất với câu hỏi. Tiếp theo, tôi nối nội dung các chunk này lại làm phần ngữ cảnh (context) và đưa vào cấu trúc prompt RAG mẫu rõ ràng (chỉ dẫn ngữ cảnh, câu hỏi và chỗ trống trả lời) rồi gọi hàm `llm_fn` để nhận được câu trả lời từ LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

#### Bảng tóm tắt kết quả kiểm thử (Test Summary Table)

| Nhóm Kiểm Thử (Test Suite) | Số Lượng Test (Count) | Trạng Thái (Status) | Mô Tả |
|----------------------------|------------------------|---------------------|-------|
| `TestProjectStructure`     | 2                      | ✅ PASSED           | Cấu trúc thư mục dự án và package `src` |
| `TestClassBasedInterfaces` | 2                      | ✅ PASSED           | Kiểm tra sự tồn tại của các class giao diện và MockEmbedder |
| `TestFixedSizeChunker`     | 7                      | ✅ PASSED           | Cơ chế chia văn bản theo kích thước cố định và overlap |
| `TestSentenceChunker`      | 4                      | ✅ PASSED           | Chia nhỏ văn bản theo ranh giới câu thực tế |
| `TestSentenceWithOverlapChunker` | 3               | ✅ PASSED           | Tách nhóm câu trượt gối đầu theo vai trò Thành viên 5 |
| `TestRecursiveChunker`     | 4                      | ✅ PASSED           | Cơ chế chia nhỏ đệ quy theo các dấu phân cách ưu tiên |
| `TestEmbeddingStore`       | 8                      | ✅ PASSED           | Đọc ghi, tính toán tương tự và tìm kiếm vector store |
| `TestKnowledgeBaseAgent`   | 2                      | ✅ PASSED           | Tác tử RAG sử dụng kho cơ sở tri thức |
| `TestComputeSimilarity`    | 4                      | ✅ PASSED           | Công thức cosine similarity và cơ chế chống chia cho 0 |
| `TestCompareChunkingStrategies` | 3                 | ✅ PASSED           | Trình so sánh và thống kê các chiến lược chunking |
| `TestEmbeddingStoreSearchWithFilter` | 3            | ✅ PASSED           | Tìm kiếm vector kết hợp bộ lọc siêu dữ liệu (metadata) |
| `TestEmbeddingStoreDeleteDocument`   | 3            | ✅ PASSED           | Xóa document và dọn dẹp các chunk trong kho lưu trữ |
| **Tổng cộng (Total)**      | **45 / 45**            | **✅ 100% PASSED**  | **Tất cả các bài test đều vượt qua xuất sắc** |

<details>
<summary><b>Chi tiết log chạy test (Click vào đây để mở rộng log)</b></summary>

```text
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- D:\VinAI\LABS\Day07_2A202601372_NhuVanHung\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\VinAI\LABS\Day07_2A202601372_NhuVanHung
configfile: pyproject.toml
collecting ... collected 45 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  6%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  8%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 13%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 15%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 17%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 20%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 22%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 24%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 31%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 33%]
tests/test_solution.py::TestSentenceWithOverlapChunker::test_empty_text PASSED [ 35%]
tests/test_solution.py::TestSentenceWithOverlapChunker::test_overlap_creates_overlapping_chunks PASSED [ 37%]
tests/test_solution.py::TestSentenceWithOverlapChunker::test_returns_list PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 44%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 46%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 48%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 51%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 53%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 55%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 60%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 62%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 64%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 68%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 75%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 77%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 82%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 84%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 86%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 91%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 93%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 45 passed in 0.07s ==============================
```
</details>

**Số lượng bài test vượt qua (pass):** 45 / 45

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có quyền yêu cầu đổi trả hàng lỗi. | Khách hàng có thể trả lại sản phẩm nếu bị hỏng. | cao | 0.8241 | Đúng |
| 2 | Người bán phải chịu trách nhiệm đăng thông tin chính xác. | Nhà bán hàng cần cung cấp mô tả sản phẩm đúng sự thật. | cao | 0.8035 | Đúng |
| 3 | Chính sách bảo hành sản phẩm kéo dài 12 tháng. | Chúng tôi hỗ trợ giao hàng miễn phí toàn quốc. | thấp | 0.1584 | Đúng |
| 4 | Quy trình thanh toán qua thẻ tín dụng. | Đăng bán sản phẩm bị cấm sẽ bị khóa tài khoản. | thấp | 0.1102 | Đúng |
| 5 | Chính sách đổi trả hàng áp dụng cho người mua. | Quy định đăng bán sản phẩm áp dụng cho người bán. | trung bình/thấp | 0.3846 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*
> Kết quả thực tế hoàn toàn khớp với dự đoán định tính về mặt ngữ nghĩa, điều này không gây bất ngờ vì mô hình nhúng của OpenAI (`text-embedding-3-small`) hoạt động rất hiệu quả. Các cặp câu đồng nghĩa (như Cặp 1 và Cặp 2) có điểm tương tự cosine trên 0.8 dù cách viết và từ vựng khác nhau, trong khi các cặp câu khác biệt chủ đề chỉ có điểm quanh mức 0.1. Điều này chứng minh embeddings thực sự biểu diễn được mối quan hệ ý nghĩa cốt lõi của câu dựa trên ngữ cảnh đã học, giúp phân tách rõ ràng mức độ tương quan thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` sử dụng chiến lược `SentenceWithOverlapChunker` (Thành viên 5). **5 câu hỏi này trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Dung lượng tối đa đối với bằng chứng ảnh/video khi yêu cầu Trả hàng/Hoàn tiền là bao nhiêu? Nếu vượt quá dung lượng thì làm thế nào? (`filter: customer_role="both"`) | Quy định 5MB/ảnh, 100MB/video. Vượt quá dung lượng tải lên Youtube/Drive công khai... (`huong-dan-chuan-bi-bang-chung`) | 0.8415 | Có | Dung lượng tối đa là 5MB cho hình ảnh và 100MB cho video (tối đa 1 phút). Nếu vượt quá, tải lên YouTube/Google Drive rồi gửi link. |
| 2 | Thời gian xử lý yêu cầu Trả hàng/Hoàn tiền và thời gian hoàn tiền trên Shopee mất bao lâu? (`filter: customer_role="buyer"`) | Xử lý từ 3-5 ngày làm việc. Hoàn tiền từ 1-14 ngày làm việc tùy phương thức thanh toán... (`huong-dan-gui-yeu-cau-tra-hang-hoan-tien`) | 0.8120 | Có | Thời gian xử lý từ 3 - 5 ngày làm việc; thời gian hoàn tiền từ 1 - 14 ngày làm việc tùy thuộc phương thức thanh toán. |
| 3 | Điều kiện bắt buộc về thông tin tài khoản để sử dụng Voucher ShopeeFood trong gói ShopeeVIP là gì? (`filter: category="voucher-khuyen-mai"`) | Việc liên kết chỉ thành công khi số điện thoại đăng ký Shopee và ShopeeFood trùng khớp... (`huong-dan-su-dung-voucher-shopeefood-shopeevip`) | 0.8350 | Có | Số điện thoại đăng ký tài khoản Shopee và ShopeeFood phải trùng khớp hoàn toàn với nhau. |
| 4 | Số lượng mã giảm giá tối đa có thể lưu vào Kho Voucher trên ứng dụng Shopee là bao nhiêu? | Số lượng mã giảm giá có thể lưu vào Kho Voucher trên Ứng dụng Shopee không bị giới hạn... (`kho-voucher-shopee-la-gi`) | 0.7985 | Có | Số lượng mã giảm giá lưu trong Kho Voucher hoàn toàn không bị giới hạn. |
| 5 | Người dùng có thể theo dõi trạng thái xử lý Trả hàng/Hoàn tiền qua những kênh nào ngoài mục Đơn Mua? (`filter: customer_role="both"`) | Theo dõi qua Thông báo app, Email liên kết, Banner thông báo hoặc Tép Thám Tử... (`theo-doi-tinh-trang-tra-hang-hoan-tien`) | 0.8260 | Có | Ngoài mục Đơn Mua, người dùng có thể theo dõi qua Thông báo ứng dụng, Email, Banner điện thoại và Trò chuyện với Tép Thám Tử. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5
*(Lưu ý: Bộ tài liệu gồm 5 file hướng dẫn Shopee sau khi chia bằng `SentenceWithOverlapChunker` (nhóm 3 câu, overlap 1 câu) tạo ra tổng cộng 94 chunks. Nhờ gối đầu ngữ cảnh giữa các câu liền kề và kết hợp bộ lọc siêu dữ liệu metadata filter, cả 5/5 câu hỏi đều tìm thấy đúng chunk liên quan ở vị trí Top-1).*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua việc trao đổi và chạy thử nghiệm, tôi nhận ra rằng việc định cấu trúc metadata tốt và kết hợp các trường thông tin lọc (metadata filtering) có vai trò vô cùng lớn giúp giải quyết vấn đề truy xuất sai lệch khi sử dụng các câu truy vấn chung chung. Ngoài ra, việc thiết kế các chiến lược chunking linh hoạt như `SentenceWithOverlapChunker` (gối đầu ranh giới câu) hoặc `HeadingBasedChunker` (gom theo tiêu đề Markdown) giúp cho các chunk truy xuất được mạch lạc và chứa trọn vẹn ngữ cảnh hơn so với chia theo độ dài ký tự cố định.

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
