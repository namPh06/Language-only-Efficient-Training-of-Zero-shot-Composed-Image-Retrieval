# Kết quả chọn và rút gọn phiên bản — 11/10/2026

**Giữ lại LinCIR gốc và bản nâng cấp truy vấn thích ứng + kết hợp điểm (`gated`).** Các nhánh nâng cấp khác, bản sao quay lui, model/cache riêng và file kiểm thử tạm đã được loại. Ảnh, vector CIRCO, checkpoint LinCIR, mã huấn luyện/đánh giá gốc và báo cáo lịch sử được giữ.

## Giao thức chọn

Rà soát 10 chế độ đang có và 2 biến thể thử nghiệm trên CIRCO validation: 220 truy vấn, toàn bộ 123.403 ảnh, Top-50. Chạy tuần tự CPU một luồng, cùng checkpoint và dữ liệu. Chỉ so chất lượng từ lượt đủ 220 truy vấn và xác nhận snapshot. Ưu tiên mAP@10, phụ mAP@50; mọi mAP/Recall ở K=5,10,25,50 không thấp hơn gốc, trung vị truy vấn không quá 1,25 lần gốc.

Mỗi phiên bản có watchdog cứng 1.800 giây gồm khởi động. Theo yêu cầu trước đó bỏ bản chậm nhiều lần, các nhánh quá 10 lần gốc được dừng sớm sau ít nhất 3 truy vấn, bỏ truy vấn đầu khi xét trung vị. Không bản nào được phép tiếp tục quá 30 phút. Các bản dừng sớm không có kết luận chất lượng toàn bộ benchmark.

## Tất cả phương án đã đo

| Phiên bản | Truy vấn | mAP@10 (%) | mAP@50 (%) | Trung vị (giây) | Kết luận |
|---|---:|---:|---:|---:|---|
| LinCIR gốc | 220/220 | 14.0374 | 16.2586 | 0.2107 | Giữ bản gốc |
| Truy vấn thích ứng | 220/220 | 15.3040 | 17.6129 | 0.1795 | Loại: không đứng đầu theo tiêu chí |
| Truy vấn thích ứng + kết hợp điểm | 220/220 | 16.6649 | 19.0203 | 0.1940 | Giữ bản nâng cấp |
| Cân bằng điểm | 220/220 | 16.0903 | 18.5211 | 0.1738 | Loại: không đứng đầu theo tiêu chí |
| Vector ngữ nghĩa nhanh | 220/220 | 14.5403 | 16.6424 | 0.1835 | Loại: không đứng đầu theo tiêu chí |
| Sắp hạng ngữ nghĩa | 220/220 | 14.0288 | 16.2955 | 0.2148 | Loại: không đứng đầu theo tiêu chí |
| FG-CLIP chi tiết | 220/220 | 15.3040 | 17.6129 | 0.1808 | Loại: 220/220 tự quay về focused, FG-CLIP không thực sự áp dụng |
| Kiểm chứng đối tượng/thuộc tính | 3/220 | — | — | 257.230 | Dừng vì quá chậm; không so chất lượng chạy dở |
| Kiểm chứng từng đối tượng | 3/220 | — | — | 261.227 | Dừng vì quá chậm; không so chất lượng chạy dở |
| Lọc nhiều tầng | 3/220 | — | — | 254.299 | Dừng vì quá chậm; không so chất lượng chạy dở |
| Kết hợp hai truy vấn | 220/220 | 16.5441 | 19.1082 | 0.2051 | Loại: không đứng đầu theo tiêu chí |
| Hai truy vấn + đồng thuận tham chiếu | 220/220 | 17.7761 | 20.4476 | 0.2438 | Loại: điểm cao nhất nhưng bản tích hợp chậm hơn gốc 28,7%, vượt giới hạn 25% |

Bảng trên ghi trung vị các lượt riêng ban đầu. Quyết định tốc độ cuối dựa trên lượt chạy cặp trong demo thật. Bản Harris riêng ban đầu đạt giới hạn tốc độ nhưng sau tích hợp đầy đủ kiểm tra đầu vào, hiển thị và ánh xạ kết quả đạt 0,2653 giây so với gốc 0,2062 giây; vì vậy bị loại. Bản ensemble có mAP@50 hơi cao hơn gated nhưng mAP@10 thấp hơn; không có phương án thắng mọi chỉ số ở mọi truy vấn.

## Kiểm chứng hai bản giữ lại

| Chỉ số (%) | Gốc | Nâng cấp | Chênh lệch điểm phần trăm |
|---|---:|---:|---:|
| mAP@5 | 12.5292 | 15.6292 | +3.1000 |
| mAP@10 | 14.0374 | 16.6649 | +2.6275 |
| mAP@25 | 15.5834 | 18.2758 | +2.6924 |
| mAP@50 | 16.2586 | 19.0203 | +2.7617 |
| Recall@5 | 23.6364 | 31.8182 | +8.1818 |
| Recall@10 | 37.2727 | 40.4545 | +3.1818 |
| Recall@25 | 51.8182 | 53.1818 | +1.3636 |
| Recall@50 | 62.7273 | 63.1818 | +0.4545 |

| Lượt chạy cặp | Trung vị gốc (s) | Trung vị nâng cấp (s) | Tỷ lệ nâng cấp/gốc | P95 gốc (s) | P95 nâng cấp (s) |
|---|---:|---:|---:|---:|---:|
| 1 | 0.2077 | 0.1856 | 0.894 | 0.2500 | 0.2377 |
| 2 | 0.1388 | 0.1253 | 0.903 | 0.2483 | 0.2253 |
| 3 | 0.2448 | 0.2169 | 0.886 | 0.2939 | 0.2722 |

Lượt 1 trước xóa nhánh, lượt 2–3 sau xóa. Cả ba lượt đủ 220 truy vấn, không partial, snapshot đúng, Top-50 từng truy vấn khớp hoàn toàn trước/sau rút gọn. Mỗi truy vấn trả 50 ID khác nhau và loại ID tham chiếu. Thời gian phụ thuộc tần số CPU/cache nên so tỷ lệ trong cùng lượt, không lấy một con số cố định làm cam kết.

Phép đo chuẩn bị vector ảnh tham chiếu ngoài bộ đếm cho cả hai bản; thời gian nạp model/index và chuẩn bị tham chiếu báo riêng trong JSON. Đây là thời gian truy vấn sau có vector, chưa phải thời gian từ mở chương trình đến hiển thị kết quả đầu tiên. Không chạy detector/VQA theo từng ảnh.

Theo mAP@10 từng truy vấn: 80 tốt hơn, 45 kém hơn, 95 ngang gốc. Bootstrap cặp 10.000 mẫu cho chênh lệch trung bình +2.6275 điểm, khoảng 95% [0.6301, 4.7629]. Đây chỉ là thống kê trên validation đã dùng để phát triển, không thay cho test độc lập.

## Thuật toán giữ lại

Giữ nguyên CLIP → Phi → pseudo-token → text encoder của LinCIR và checkpoint gốc. Truy vấn tối đa 10 từ dùng `$ , mô tả`; truy vấn dài giữ `a photo of $ that mô tả`; prompt có `$` được giữ theo người dùng. Với điểm LinCIR s và điểm tương đồng ảnh tham chiếu r: truy vấn thông thường dùng `s + 0,4 * sigmoid((s−t)/0,01) * r`, trong đó t là điểm thứ 50 trên kho. Truy vấn có dấu hiệu phủ định dùng `s + 0,1*r`.

Giới hạn trên của tích vô hướng giúp bỏ tính bổ sung ở ứng viên không thể lọt Top-K, nhưng giữ kết quả đúng như tính đầy đủ của công thức. Đây là cắt giảm tính toán có căn cứ, không phải lọc cứng tất cả thuộc tính. Hệ thống vẫn chấm điểm vector trên toàn bộ kho cho lượt tìm đầu tiên. Không dùng ground truth, shared concept hoặc ảnh đích để tính điểm.

## Dọn dẹp và kiểm tra chức năng

Đã xóa 66 mục được liệt kê trong cleanup_execution.json, khoảng 2.51 GB. Bao gồm module nâng cấp bị loại, launcher quay lui, bản sao source, model FG-CLIP/kiểm chứng và cache nghiên cứu không còn dùng. Giữ vector gallery/reference, 123.403 ảnh CIRCO, gallery riêng và số liệu/báo cáo cũ.

Đã kiểm tra: tái sử dụng vector sau khởi động lại; chỉ mã hóa ảnh mới; tải trùng không tạo thêm ảnh; loại ảnh tham chiếu; tìm bối cảnh/trang phục/phủ định; từ chối mô tả rỗng/quá dài, nhiều pseudo-token, ảnh hỏng và Top-K sai; giao diện đúng hai lựa chọn và một khu kết quả. File ảnh thử và script test được xóa sau kiểm tra.

Bộ duyệt tự động từ chối xóa `demo_laion.py` và `pretrained_models/pic2word_large.pt` vì là tệp của dự án gốc, ngoài phạm vi xóa nâng cấp. Hai tệp được giữ, không thử xóa lại. Demo/CIRCO hiện tại chỉ có baseline và gated; không có nhánh nâng cấp dư hoạt động.

## Sử dụng và giới hạn

Chạy `python demo.py`; chọn bản gốc để đối chiếu hoặc quay lại hành vi gốc. Hướng dẫn benchmark: `HUONG_DAN_CIRCO.md`. Vẫn phải giữ ảnh gốc trên ổ đĩa; vector không thay được file ảnh.

Không bảo đảm mọi truy vấn tốt hơn: phủ định, chi tiết nhỏ, nhiều thuộc tính hoặc quan hệ có thể sai. Đây là nâng cấp truy hồi, không sinh/chỉnh sửa ảnh và không xác nhận tất cả thuộc tính bằng một hệ thống hiểu cảnh đầy đủ. Kết quả CIRCO validation này không đồng nhất kết quả test ẩn trong bài báo; LAION online không được kiểm chứng bởi benchmark local. Không thể kết luận hệ thống không còn bất kỳ lỗi nào.

## Bằng chứng

- [Tổng hợp lựa chọn](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/selection_summary.json)
- [Danh sách xóa](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/cleanup_execution.json)
- [Kiểm tra chức năng](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/final_functional_checks.json)
- [Benchmark hai bản, lượt 1](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/final_gated_run1.json)
- [Benchmark hai bản, lượt 2](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/final_gated_run2.json)
- [Benchmark hai bản, lượt 3](D:/Ki I 2025-2026/Ki I 2025-2026/Xử lý ảnh/BTL/XLA-/Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval/outputs/version_selection_20261011/final_gated_run3.json)
