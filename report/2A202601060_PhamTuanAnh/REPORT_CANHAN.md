# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Tuấn Anh  
**Nhóm:** Nhóm HHQDA  
**Ngày:** 2026-08-03  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao thể hiện hai vector biểu diễn văn bản chỉ về cùng một hướng trong không gian đa chiều. Điều này chứng tỏ hai đoạn văn bản có sự đồng nhất cao về nội dung ngữ nghĩa và chủ đề, bất chấp độ dài hay số lượng từ của hai đoạn văn đó có sự khác biệt.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Shopee hỗ trợ trả hàng hoàn tiền trong vòng 3 ngày làm việc."
- Câu B: "Thời gian xử lý yêu cầu hoàn tiền và trả sản phẩm trên Shopee là 3 ngày."
- Tại sao tương đồng: Cùng diễn đạt quy định thời gian xử lý quy trình trả hàng/hoàn tiền của Shopee với các từ khóa ngữ nghĩa tương đương.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hướng dẫn cài đặt ứng dụng Shopee trên điện thoại Android."
- Câu B: "Cách làm bánh kem dâu tây thơm ngon tại nhà."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (ứng dụng thương mại điện tử vs công thức nấu ăn), không chia sẻ điểm chung nào về mặt ngữ cảnh.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector (hướng ngữ nghĩa) mà bỏ qua độ dài (norm) của chúng. Ngược lại, khoảng cách Euclid chịu ảnh hưởng lớn bởi độ dài văn bản (văn bản dài chứa nhiều từ hơn sinh ra vector có độ dài lớn hơn), dẫn đến việc đánh giá sai lệch giữa hai đoạn văn bản cùng nội dung nhưng khác nhau về độ dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy giữa các chunk: $\text{step} = \text{chunk\_size} - \text{overlap} = 500 - 50 = 450$ ký tự.  
> Vị trí bắt đầu của chunk thứ $i$: $\text{start}_i = i \times 450$.  
> Chunk cuối cùng bắt đầu tại vị trí $\text{start} = 9450$ (phủ đoạn $9450 \rightarrow 9950$), phần còn lại $9900 \rightarrow 10000$ sinh ra chunk cuối cùng.  
> Phép tính số lượng chunk: $N = \lceil \frac{10000 - 500}{450} \rceil + 1 = \lceil \frac{9500}{450} \rceil + 1 = 21.11 \rightarrow 22 + 1 = 22$.  
> *Đáp án:* **22 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm xuống $\text{step} = 500 - 100 = 400$, số lượng chunk tăng lên thành $\lceil \frac{9500}{400} \rceil + 1 = 24 + 1 = 25$ chunks.  
> Việc tăng độ chồng chéo giúp đảm bảo không bị đứt gãy ngữ cảnh hay mất từ ngữ ở phần ranh giới giữa hai chunk liền kề, giúp mô hình nhúng (Embedding) và Vector Store giữ lại toàn vẹn thông tin ngữ nghĩa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`FixedSizeChunker.chunk`** — hướng tiếp cận:
> Tách văn bản thành các khối có độ dài cố định `chunk_size` ký tự với bước dịch chuyển $\text{step} = \text{chunk\_size} - \text{overlap}$. Xử lý trường hợp chuỗi ngắn hơn `chunk_size` bằng cách trả về ngay `[text]`, và dừng vòng lặp trượt khi điểm bắt đầu cộng `chunk_size` vượt quá độ dài văn bản.

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\.\n', text)` để nhận diện ranh giới các câu văn. Sau đó gom từng nhóm tối đa `max_sentences_per_chunk` câu liền kề thành một chunk và loại bỏ các khoảng trắng thừa ở đầu/cuối câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng chiến thuật đệ quy dựa trên danh sách ưu tiên các dấu phân tách `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản có độ dài $\le \text{chunk\_size}$ hoặc khi không còn dấu phân tách nào, hàm sẽ ngắt chuỗi trực tiếp theo kích thước `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Danh sách `Document` được lưu giữ trong store kèm với danh sách các vector nhúng (embeddings) 384 chiều được tính toán bởi mô hình `paraphrase-multilingual-MiniLM-L12-v2`. Hàm `search` chuyển câu hỏi thành vector embedding, tính độ tương tự cosine với từng vector document trong kho, sắp xếp giảm dần theo điểm score và cắt lấy `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Hàm `search_with_filter` thực hiện tiền lọc (pre-filtering): duyệt qua kho tài liệu và chỉ chọn những chunk có `metadata` chứa đầy đủ các cặp khóa-giá trị trùng khớp với `metadata_filter` trước khi tính điểm tương đồng. Hàm `delete_document` tìm và xóa tất cả các chunk có `doc_id` khớp trong kho, trả về `True` nếu xóa thành công và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tiếp nhận truy vấn từ người dùng, gọi `store.search(question, top_k)` để trích xuất các đoạn văn bản liên quan nhất. Nối các đoạn văn bản này thành chuỗi `Context` và đưa vào mẫu Prompt RAG: `"Context:\n{context}\n\nQuestion: {question}\nAnswer:"`, sau đó chuyển Prompt cho mô hình `llm_fn` để tổng hợp câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.4, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\lab7\individual\DAY07_2A202601060_Pham-Tuan-Anh
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

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Chạy thực tế với mô hình nhúng đa ngôn ngữ **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều)**:

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (AI Model) | Đúng? |
|------|-----------|-----------|---------|--------------------------|-------|
| 1 | Trả hàng hoàn tiền Shopee | Yêu cầu hoàn trả sản phẩm Shopee | cao | **0.8344** | Đúng |
| 2 | Mã giảm giá ShopeeFood | Voucher ăn uống Shopee VIP | cao | **0.6034** | Đúng |
| 3 | Thời gian hoàn tiền qua thẻ tín dụng | Dung lượng video tối đa 100MB | thấp | **0.1587** | Đúng |
| 4 | Quy trình khiếu nại người bán | Hướng dẫn nấu ăn món phở | thấp | **0.1861** | Đúng |
| 5 | Số điện thoại đăng ký tài khoản | Tổng đài hỗ trợ Shopee | trung bình | **0.4080** | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số của Cặp 1 (**0.8344**) và Cặp 2 (**0.6034**) thể hiện rõ sức mạnh của mô hình AI thực sự (`paraphrase-multilingual-MiniLM-L12-v2`). Mô hình đã nhận diện được sự đồng nhất ngữ nghĩa tuyệt vời giữa các từ đồng nghĩa tiếng Việt như *"Trả hàng"* $\leftrightarrow$ *"Hoàn trả"*, hay *"Mã giảm giá"* $\leftrightarrow$ *"Voucher"*. Điều này khẳng định vector embedding thật sự biểu diễn chính xác không gian ngữ nghĩa tự nhiên vượt xa thuật toán băm (hash) cơ bản.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mô hình AI `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều) với chiến lược `FixedSizeChunker(chunk_size=300, overlap=50)` trên bộ dữ liệu `data/data_shopee`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Dung lượng tối đa đối với bằng chứng ảnh/video khi yêu cầu Trả hàng/Hoàn tiền là bao nhiêu? Nếu vượt quá dung lượng thì làm thế nào? (`filter: customer_role="both"`) | `huong-dan-chuan-bi-bang-chung`: Mục 4 Quy định về bằng chứng (Ảnh <= 5MB/ảnh; Video <= 100MB/video). Nếu quá dung lượng tải lên Youtube/Drive. | **0.6766** | Có | Hình ảnh không quá 5MB/ảnh, video không quá 100MB/video. Nếu vượt quá dung lượng thì tải lên YouTube hoặc Google Drive rồi gửi đường dẫn. |
| 2 | Thời gian xử lý yêu cầu Trả hàng/Hoàn tiền và thời gian hoàn tiền trên Shopee mất bao lâu? (`filter: customer_role="buyer"`) | `huong-dan-gui-yeu-cau-tra-hang-hoan-tien`: Xử lý yêu cầu trong 3 - 5 ngày làm việc, hoàn tiền trong 1 - 14 ngày làm việc. | **0.8192** | Có | Yêu cầu xử lý trong 3-5 ngày làm việc, thời gian hoàn tiền từ 1-14 ngày làm việc tùy thuộc phương thức thanh toán. |
| 3 | Điều kiện bắt buộc về thông tin tài khoản để sử dụng Voucher ShopeeFood trong gói ShopeeVIP là gì? (`filter: category="voucher-khuyen-mai"`) | `huong-dan-su-dung-voucher-shopeefood-shopeevip`: Liên kết chỉ thành công khi số điện thoại đăng ký tài khoản Shopee và ShopeeFood trùng khớp. | **0.7215** | Có | Điều kiện bắt buộc là số điện thoại đăng ký tài khoản Shopee và tài khoản ShopeeFood phải hoàn toàn trùng khớp với nhau. |
| 4 | Số lượng mã giảm giá tối đa có thể lưu vào Kho Voucher trên ứng dụng Shopee là bao nhiêu? | `kho-voucher-shopee-la-gi`: Lưu ý: Số lượng các mã giảm giá có thể lưu vào Kho Voucher hoàn toàn không bị giới hạn. | **0.7225** | Có | Số lượng mã giảm giá có thể lưu vào Kho Voucher trên ứng dụng Shopee là hoàn toàn không bị giới hạn. |
| 5 | Người dùng có thể theo dõi trạng thái xử lý Trả hàng/Hoàn tiền qua những kênh nào ngoài mục Đơn Mua? (`filter: customer_role="both"`) | `theo-doi-tinh-trang-tra-hang-hoan-tien`: Theo dõi qua Mục Thông báo trên app, Email liên kết, Banner thông báo, và Chatbot Tép Thám Tử. | **0.4748** | Có | Người dùng có thể theo dõi qua các kênh: Mục Thông báo trên app, Email liên kết, Banner thông báo và Chatbot Tép Thám Tử. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Các thành viên sử dụng chiến lược tách theo cấu trúc như `HeadingBasedChunker` và `RecursiveChunker` đạt được độ trích xuất ngữ cảnh tự nhiên và trọn vẹn hơn so với `FixedSizeChunker`. Việc dùng `FixedSizeChunker` đôi khi cắt đôi một câu quy định ở ranh giới 300 ký tự, tuy nhiên bù lại `FixedSizeChunker` với overlap 50 ký tự tạo ra các vector 384 chiều có kích thước cực kỳ đồng đều, giúp hệ thống Vector Store truy xuất và tính toán điểm tương đồng AI rất ổn định.

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
