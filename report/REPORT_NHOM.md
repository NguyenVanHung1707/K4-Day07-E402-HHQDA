# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Hướng dẫn xử lý quy trình Trả hàng/Hoàn tiền, chuẩn bị bằng chứng khiếu nại, theo dõi tiến độ đơn hàng và hướng dẫn sử dụng Kho Voucher / ShopeeFood.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | [Trả hàng/Hoàn tiền] Hướng dẫn chuẩn bị bằng chứng khi yêu cầu Trả hàng/ Hoàn tiền | https://help.shopee.vn/s/article/Huong-dan-chuan-bi-bang-chung-khi-yeu-cau-tra-hang-hoan-tien | 2026-08-03 / 2026.1 | 4,662 | `doc_id: huong-dan-chuan-bi-bang-chung`, `customer_role: both`, `category: gui-yeu-cau` |
| 2 | [Trả hàng/ Hoàn tiền] Hướng dẫn gửi yêu cầu Trả hàng/ Hoàn tiền | https://help.shopee.vn/s/article/Huong-dan-gui-yeu-cau-Tra-hang-Hoan-tien | 2026-08-03 / 2026.1 | 3,335 | `doc_id: huong-dan-gui-yeu-cau-tra-hang-hoan-tien`, `customer_role: buyer`, `category: gui-yeu-cau` |
| 3 | [ShopeeVIP] Hướng dẫn sử dụng Mã ưu đãi (Voucher) ShopeeFood trong gói ShopeeVIP | https://help.shopee.vn/s/article/Huong-dan-su-dung-Voucher-ShopeeFood-trong-goi-ShopeeVIP | 2026-08-03 / 2026.1 | 4,670 | `doc_id: huong-dan-su-dung-voucher-shopeefood-shopeevip`, `customer_role: buyer`, `category: voucher-khuyen-mai` |
| 4 | [Voucher/Mã giảm giá] Kho Voucher trên Shopee là gì? | https://help.shopee.vn/s/article/Kho-Voucher-tren-Shopee-la-gi | 2026-08-03 / 2026.1 | 2,718 | `doc_id: kho-voucher-shopee-la-gi`, `customer_role: buyer`, `category: voucher-khuyen-mai` |
| 5 | [Trả hàng/ Hoàn tiền] Theo dõi tình trạng Trả hàng/ Hoàn tiền trên Shopee | https://help.shopee.vn/s/article/Theo-doi-tinh-trang-Tra-hang-Hoan-tien-tren-Shopee | 2026-08-03 / 2026.1 | 2,256 | `doc_id: theo-doi-tinh-trang-tra-hang-hoan-tien`, `customer_role: both`, `category: theo-doi-yeu-cau` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `huong-dan-chuan-bi-bang-chung` | Mã tài liệu duy nhất, trùng tên file giúp truy vết nguồn và dùng cho xóa/lọc tài liệu. |
| `source_url` | `str` | `https://help.shopee.vn/...` | Đường dẫn minh bạch đến trang chính thức của Shopee. |
| `retrieved_at` | `str` | `2026-08-03` | Ngày thu thập dữ liệu nhằm đánh giá tính cập nhật của tài liệu. |
| `document_version` | `str` | `2026.1` | Phiên bản văn bản quy định. |
| `customer_role` | `str` | `buyer` / `both` | Phân vai đối tượng áp dụng (`buyer` / `seller` / `both`) để lọc chính xác ngữ cảnh truy xuất K4. |
| `category` | `str` | `gui-yeu-cau`, `voucher-khuyen-mai` | Phân loại mảng nội dung hỗ trợ để pre-filter danh mục trước khi tìm kiếm vector. |


---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Dung lượng tối đa đối với bằng chứng ảnh/video khi yêu cầu Trả hàng/Hoàn tiền là bao nhiêu? Nếu vượt quá dung lượng thì làm thế nào? (`filter: customer_role="both"`) | Hình ảnh không quá 5MB/ảnh; Video không quá 100MB/video (tối đa 1 phút). Nếu dung lượng lớn hơn quy định, tải lên YouTube hoặc Google Drive (chế độ công khai) rồi gửi đường dẫn trong phần chú thích khi gửi yêu cầu. | `huong-dan-chuan-bi-bang-chung` (Mục 4: Quy định về bằng chứng) |
| 2 | Thời gian xử lý yêu cầu Trả hàng/Hoàn tiền và thời gian hoàn tiền trên Shopee mất bao lâu? (`filter: customer_role="buyer"`) | Thời gian xử lý yêu cầu thường từ 3 - 5 ngày làm việc. Nếu yêu cầu được chấp nhận, thời gian hoàn tiền là 1 - 14 ngày làm việc tùy thuộc vào phương thức thanh toán. | `huong-dan-gui-yeu-cau-tra-hang-hoan-tien` (Mục 2: Lưu ý) |
| 3 | Điều kiện bắt buộc về thông tin tài khoản để sử dụng Voucher ShopeeFood trong gói ShopeeVIP là gì? (`filter: category="voucher-khuyen-mai"`) | Việc liên kết tài khoản Shopee và ShopeeFood chỉ thành công khi số điện thoại đăng ký tài khoản Shopee và tài khoản ShopeeFood trùng khớp (giống nhau). Nếu khác số điện thoại thì Voucher ShopeeFood sẽ không hiển thị và không sử dụng được. | `huong-dan-su-dung-voucher-shopeefood-shopeevip` (Mục 1: Lưu ý trước khi sử dụng) |
| 4 | Số lượng mã giảm giá tối đa có thể lưu vào Kho Voucher trên ứng dụng Shopee là bao nhiêu? | Số lượng mã giảm giá có thể lưu vào Kho Voucher trên Ứng dụng Shopee hoàn toàn không bị giới hạn. | `kho-voucher-shopee-la-gi` (Mục 4 & Lưu ý) |
| 5 | Người dùng có thể theo dõi trạng thái xử lý Trả hàng/Hoàn tiền qua những kênh nào ngoài mục Đơn Mua? (`filter: customer_role="both"`) | Theo dõi qua mục Thông báo (Cập nhật Đơn hàng) trên app, biểu ngữ thông báo trên điện thoại, Email liên kết, hoặc mục Trò Chuyện Với Shopee (hỗ trợ bởi trợ lý ảo Tép Thám Tử). | `theo-doi-tinh-trang-tra-hang-hoan-tien` (Mục 1.2, 2.1, 2.2, 3) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Dung lượng tối đa đối với bằng chứng ảnh/video và cách xử lý khi vượt dung lượng? | `RecursiveChunker` + Filter (`customer_role="both"`) | Có (Top-1) | Truy xuất chính xác mục quy định 5MB/ảnh và 100MB/video kèm giải pháp link Youtube/Drive. |
| 2 | Thời gian xử lý yêu cầu Trả hàng/Hoàn tiền và thời gian hoàn tiền? | `SentenceChunker` + Filter (`customer_role="buyer"`) | Có (Top-1) | Truy xuất đúng khung thời gian 3-5 ngày xử lý và 1-14 ngày hoàn tiền. |
| 3 | Điều kiện bắt buộc về số điện thoại liên kết ShopeeFood ShopeeVIP? | `FixedSizeChunker` + Filter (`category="voucher-khuyen-mai"`) | Có (Top-1) | Trích xuất chính xác điều kiện trùng khớp SĐT giữa 2 tài khoản. |
| 4 | Số lượng mã giảm giá tối đa lưu vào Kho Voucher Shopee? | `RecursiveChunker` (Unfiltered) | Có (Top-1) | Tìm thấy chunk khẳng định không giới hạn số lượng lưu. |
| 5 | Các kênh theo dõi trạng thái Trả hàng/Hoàn tiền ngoài mục Đơn Mua? | `SentenceChunker` + Filter (`customer_role="both"`) | Có (Top-1) | Truy xuất đầy đủ các kênh: Thông báo app, email, banner điện thoại và chatbot Tép Thám Tử. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata giúp ích rất rõ rệt ở các câu hỏi 1, 2, 3 và 5. Cụ thể, việc dùng `metadata_filter={"customer_role": "both"}` hoặc `{"customer_role": "buyer"}` và `{"category": "voucher-khuyen-mai"}` giúp khoanh vùng tập ứng viên ngay từ đầu, loại bỏ các chunk nhiễu thuộc các chủ đề khác trước khi tính điểm tương đồng vector.


---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
