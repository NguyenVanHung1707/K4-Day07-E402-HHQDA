# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đặng Minh Quang
**Nhóm:** A5
**Ngày:** 03/08/2026
**Chiến lược chunking cá nhân:** `FAQPairChunker`

> Báo cáo này trình bày phần thực hiện cá nhân trên bộ tài liệu hỗ trợ khách hàng Shopee của nhóm.

## 1. Khởi động (Warm-up) — 5 điểm

### 1.1. Độ tương tự cosine

Độ tương tự cosine đo góc giữa hai vector: `cos(A,B)=(A·B)/(|A|×|B|)`. Giá trị gần 1 thường biểu diễn nội dung gần nghĩa; gần 0 là ít liên quan; gần -1 là ngược hướng.

Ví dụ cao: “Python là ngôn ngữ lập trình bậc cao” và “Python là một ngôn ngữ lập trình cấp cao” diễn đạt cùng nội dung. Ví dụ thấp: câu về Python và câu về thời tiết thuộc hai chủ đề không liên quan.

Cosine similarity phù hợp với text embeddings vì tập trung vào hướng vector thay vì độ lớn tuyệt đối.

### 1.2. Bài toán chunking

Với 10.000 ký tự, `chunk_size=500`, `overlap=50`: `ceil((10.000-50)/(500-50))=23` chunks. Nếu overlap tăng lên 100: `ceil((10.000-100)/(500-100))=25` chunks. Overlap lớn giữ ngữ cảnh ranh giới tốt hơn nhưng tăng lưu trữ và chi phí xử lý.

## 2. Hướng tiếp cận của tôi — 10 điểm

### 2.1. FAQPairChunker

Tôi chọn `FAQPairChunker` vì tài liệu hỗ trợ Shopee có cấu trúc câu hỏi–trả lời như `### Q1:`. Chunker dùng regex đa dòng để nhận diện câu hỏi dạng `### Q1:`, `Q2:` và tiêu đề `##`. Positive lookahead giữ tiêu đề ở đầu chunk, nhờ đó câu hỏi luôn đi cùng toàn bộ câu trả lời đến trước mốc tiếp theo.

Quy trình: kiểm tra đầu vào rỗng; chuẩn hóa hai đầu; tách theo mốc FAQ/heading; loại phần ngắn theo `min_length`; nếu không có phần phù hợp thì giữ nguyên tài liệu để tránh mất dữ liệu.

Ưu điểm là chunk độc lập, đúng ngữ cảnh hỏi–đáp và phù hợp truy vấn hỗ trợ khách hàng. Hạn chế là tài liệu không có FAQ có thể tạo chunk lớn, còn `min_length` quá cao có thể loại nội dung ngắn.

### 2.2. Các thành phần còn lại

- `FixedSizeChunker` chia theo ký tự và overlap, nhanh nhưng có thể cắt giữa câu.
- `SentenceChunker` tách theo dấu kết thúc câu và gom theo số câu tối đa.
- `RecursiveChunker` thử ranh giới đoạn, dòng, câu, từ rồi ký tự.
- `ChunkingStrategyComparator` so sánh `fixed_size`, `by_sentences`, `recursive` và `faq_pair`.
- `EmbeddingStore` lưu nội dung, vector và metadata; hỗ trợ search, metadata filter và xóa theo `doc_id`.
- `KnowledgeBaseAgent` truy xuất top-k, ghép Context và yêu cầu LLM chỉ trả lời từ ngữ cảnh.

Pipeline ingest mặc định đã chuyển sang `FAQPairChunker`. Mỗi chunk giữ `doc_id`, `chunk_index`, `customer_role`, `category`, `source_url`, `retrieved_at` và `document_version`.

## 3. Hoàn thiện code — 30 điểm

Tôi đã hoàn thiện chunking, cosine similarity, vector store, metadata filter, xóa tài liệu, agent và tích hợp `FAQPairChunker`.

Lệnh `python -m pytest tests -q` cho kết quả:

```text
42 passed, 2 warnings in 0.07s
```

**Số test vượt qua: 42/42.** Hai warning chỉ do pytest không tạo được cache, không phải lỗi chức năng.

Kiểm tra riêng trên tài liệu Voucher ShopeeVIP tạo **8 chunks**; Q1, Q2, Q3 và Q4 đều thành chunk riêng. Toàn corpus `data/data_shopee` tạo **25 chunks**.

## 4. Dự đoán độ tương tự — 5 điểm

| Cặp | Câu A | Câu B | Dự đoán | Điểm mock | Đúng? |
| --- | --- | --- | --- | ---: | :---: |
| 1 | Python là ngôn ngữ lập trình. | Python được dùng để viết phần mềm. | Cao | 0,1186 | Có |
| 2 | Mô hình học máy học từ dữ liệu. | Machine learning sử dụng dữ liệu để học. | Cao | -0,0022 | Không |
| 3 | Chính sách đổi trả áp dụng trong 30 ngày. | Khách hàng có thể hoàn hàng trong vòng 30 ngày. | Cao | -0,0673 | Không |
| 4 | Trời hôm nay có mưa. | Vector database lưu trữ embeddings. | Thấp | 0,0973 | Không |
| 5 | Tôi thích uống cà phê. | Máy chủ cần được bảo mật. | Thấp | -0,0609 | Có |

Cặp 2 và 3 bất ngờ nhất vì gần nghĩa nhưng score gần 0 hoặc âm. `MockEmbedder` chỉ tạo vector xác định để test code, không học ngữ nghĩa. Cần embedding đa ngữ thực để đánh giá retrieval chính xác.

## 5. Kết quả truy xuất của tôi — 10 điểm

Cấu hình: 5 tài liệu trong `data/data_shopee`, `FAQPairChunker(min_length=40)`, 25 chunks, `MockEmbedder`, `top_k=3`, dùng đúng 5 câu hỏi trong báo cáo nhóm.

| # | Câu hỏi rút gọn | Top-1 | Score | Kết quả top-3 |
| --- | --- | --- | ---: | --- |
| 1 | Giới hạn dung lượng ảnh/video và cách xử lý? | Tiêu đề tài liệu theo dõi hoàn tiền | 0,3166 | Không có đúng mục dung lượng |
| 2 | Thời gian xử lý và hoàn tiền? | FAQ Q2 về Voucher ShopeeFood | 0,3123 | Không có chunk liên quan |
| 3 | Điều kiện dùng Voucher ShopeeFood ShopeeVIP? | Lưu ý trước khi dùng Voucher | 0,1146 | **Có, top-1** |
| 4 | Số Voucher tối đa có thể lưu? | Khiếu nại hàng có vấn đề | 0,1663 | Không có chunk liên quan |
| 5 | Kênh theo dõi ngoài Đơn Mua? | Trên ứng dụng Shopee | 0,1906 | **Có; mục Ngoài ứng dụng ở top-3** |

**Số câu có chunk liên quan trong top-3: 2/5.**

Agent có thể trả lời đúng câu 3: hai tài khoản phải liên kết và dùng cùng số điện thoại. Với câu 5, Agent có đủ ngữ cảnh để nêu Thông báo/Cập nhật đơn hàng, thông báo điện thoại, email và Trò Chuyện Với Shopee. Ba câu còn lại phải báo ngữ cảnh không đủ.

Theo rubric tái lập bằng mock: câu 3 và 5 đạt 2 điểm/câu; câu 1, 2, 4 đạt 0 điểm. **Tổng retrieval: 4/10.**

Kết quả chứng minh chunking đúng chưa đủ nếu embedding không biểu diễn ngữ nghĩa. Hướng cải thiện là dùng embedding đa ngữ, kết hợp thêm `category` trong filter, tìm kiếm lai BM25–vector, rerank top-k và đưa tiêu đề/category vào nội dung embedding.

## 6. Bài học và tự đánh giá

Tôi học được rằng chunker nên theo cấu trúc tài liệu: FAQPairChunker phù hợp hỏi–đáp, HeadingBasedChunker phù hợp mục chính sách, RecursiveChunker phù hợp văn bản hỗn hợp. Hệ thống thực tế nên chọn chunker theo loại tài liệu thay vì dùng một chiến lược duy nhất.

| Tiêu chí | Điểm |
| --- | ---: |
| Khởi động | 5/5 |
| Hướng tiếp cận | 10/10 |
| Hoàn thiện code | 30/30 |
| Dự đoán độ tương tự | 5/5 |
| Truy xuất tái lập bằng MockEmbedder | 4/10 |
| **Tổng phần cá nhân** | **54/60** |

## Kết luận

Tôi đã hoàn thiện toàn bộ code bắt buộc và bổ sung `FAQPairChunker` phù hợp dữ liệu Shopee. Chunker tách đúng Q1–Q4 và giữ trọn cặp hỏi–đáp. Hạn chế chính của lần đánh giá hiện tại là `MockEmbedder`; bước tiếp theo là chạy cùng benchmark bằng embedding đa ngữ thực.
