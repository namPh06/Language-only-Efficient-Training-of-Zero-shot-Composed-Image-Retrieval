# Kết quả thử chấm điều kiện và vùng ảnh — 12/10/2026

Không thay thế bản đang sử dụng. LinCIR, gated, FTI4CIR và demo_fti.py được giữ nguyên, đã đối chiếu SHA256.

## CIRCO validation

Đủ 220 truy vấn, kho 123.403 ảnh; loại ảnh tham chiếu theo ID. Thời gian toàn lượt 744.3 giây (giới hạn cứng 1.200 giây). Snapshot ảnh được kiểm tra. Thứ hạng FTI4CIR trùng kết quả trước.

| Phương pháp | mAP@10 (%) | mAP@50 (%) | Trung vị tìm kiếm (giây) |
|---|---:|---:|---:|
| FTI4CIR hiện tại | 18.9948 | 21.7146 | 0.1513 |
| Chấm lại theo điều kiện | 16.3580 | 18.9716 | 0.2312 |

Thời gian trung vị tính khi đặc trưng tham chiếu đã chuẩn bị, không bao gồm khởi động và chuẩn bị ảnh. Không tương đương tốc độ toàn bộ yêu cầu lạnh.

## Thay đổi đã thử

- Tách điều kiện tiếng Anh đơn giản thành thêm/loại; câu so sánh hoặc logic phức tạp quay về FTI.
- Bảo toàn ngữ cảnh bằng truy vấn FTI; chưa có bộ suy luận bảo toàn thuộc tính riêng.
- Chấm mềm 100 ứng viên bằng vector CLIP có sẵn, trọng số 0,025; không loại cứng.
- Trọng số cố định trước lượt kiểm tra; không dùng đáp án để tạo truy vấn.
- Demo riêng demo_conditions.py có đối chiếu trước/sau, bật/tắt vùng; không sửa demo hiện tại.

## Quyết định

Nhánh điều kiện không đạt tiêu chí chất lượng. Giữ nó dưới dạng thử nghiệm có cảnh báo, không dùng để trình bày rằng đã cải thiện mô hình. Kết quả gợi ý phép khớp điều kiện chữ toàn cục có thể lấn át ngữ cảnh tham chiếu; đây là giả thuyết, chưa chứng minh nguyên nhân bằng ablation.

## Nhánh vùng

RegionBank chuẩn bị trước bốn vùng của mỗi ảnh trong kho demo tối đa 100 ảnh, lưu trên ổ đĩa và kiểm tra danh sách/đường dẫn/kích thước/mtime trước sử dụng. Kết hợp 80% tương đồng toàn ảnh và 20% tương đồng vùng tốt nhất trong tín hiệu điều kiện.

Vector vùng là trung bình patch qua post-layernorm và projection của CLIP. Đây là đặc trưng gần đúng, không phải detector đầu/thân/áo, không bảo đảm hiểu hoa văn hoặc vị trí đúng. Center crop có thể bỏ chi tiết ở rìa. Chưa có benchmark CIRCO đầy đủ cho nhánh vùng: không gán kết quả global ở trên cho vùng. Không triển khai đầy đủ TAPR và không có LLM tách thuộc tính.

## Chạy và quay lại

Trong thư mục project:
- Bản hiện tại: ..\.venv\Scripts\python.exe -B -X utf8 demo_fti.py
- Bản thử riêng: ..\.venv\Scripts\python.exe -B -X utf8 demo_conditions.py (cổng 8014)

Giữ công tắc vùng tắt để xem nhánh đã kiểm tra CIRCO; muốn thử vùng, bấm chuẩn bị trước rồi bật công tắc. Không khuyến nghị bản thử làm bản chính. Quay lại bằng cách đóng demo thử và chạy demo_fti.py; không cần đổi file hay checkpoint.

Bằng chứng: outputs/condition_trial_20261012/benchmark.json, protocol.json, decision.json, demo_checks.json.
Validation đã dùng trong phát triển nhiều lần; không phải kết quả test độc lập của bài báo.

## Kiểm tra chức năng kho demo

14 ảnh, tensor vùng 14×4×768; cache nạp lại giống hệt; kho không đúng identity bị vô hiệu hóa; tìm khi đã chuẩn bị không gọi encoder ảnh lại. Một lượt tìm lặp mất 0.1331 giây. Giao diện dựng cấu hình thành công; chưa kiểm tra trình duyệt trực tiếp. Đây không phải kiểm tra độ chính xác.
