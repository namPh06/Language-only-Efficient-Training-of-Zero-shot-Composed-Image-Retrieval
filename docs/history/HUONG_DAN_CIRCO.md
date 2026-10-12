# CIRCO — đánh giá hai phiên bản hiện tại

Bộ validation có 220 truy vấn trên toàn bộ gallery 123.403 ảnh. Ground truth chỉ dùng chấm kết quả, không dùng tính điểm truy vấn.

Kiểm tra dữ liệu:
```powershell
..\.venv\Scripts\python.exe -X utf8 prepare_circo.py --check
```
Chỉ đánh giá đầy đủ khi `ready: true`. Giữ ảnh CIRCO và `outputs/circo_index`; vector có sẵn được tái sử dụng.

Đánh giá:
```powershell
..\.venv\Scripts\python.exe -B -X utf8 benchmark_circo.py --modes baseline gated --batch-size 1 --cpu-threads 1 --independent-latency --prepared-reference-latency --output outputs/circo_current.json
```
Hoặc dùng `RUN_CIRCO.cmd` với các tùy chọn trên. Chỉ còn `baseline` (gốc) và `gated` (nâng cấp truy vấn thích ứng và kết hợp điểm có giới hạn).

Mỗi lần gọi có giới hạn cứng 30 phút gồm cả khởi động; quá hạn ngắt cây tiến trình. Muốn giới hạn riêng từng bản thì chạy mỗi chế độ với output riêng. Lưu sau từng truy vấn hoàn chỉnh; chạy lại cùng lệnh tiếp tục nếu mã/cấu hình giữ nguyên. Sau thay đổi dùng output mới. Kết quả chạy dở không phải benchmark đầy đủ.

- `mAP@K`: độ chính xác trung bình có xét thứ hạng và nhiều ảnh đúng, theo CIRCO.
- `Recall@K`: tỷ lệ truy vấn có `target_img_id` trong Top-K.
- `GTRecall@K`: tỷ lệ các ảnh thuộc `gt_img_ids` tìm được.
- `median_seconds`: trung vị thời gian truy vấn. Lệnh trên chuẩn bị vector tham chiếu ngoài bộ đếm; thời gian chuẩn bị và nạp model/index báo riêng. Muốn đo gồm mã hóa tham chiếu, bỏ `--prepared-reference-latency`; không so hai giao thức như cùng phép đo.
- Lượt đầy đủ phải có `snapshot_verified: true`, `partial: false`, `completed_queries: 220`.

Cả hai bản dùng cùng checkpoint/gallery/vector, thứ tự chạy luân phiên. `--independent-latency` xóa cache truy vấn trong RAM để tránh lợi thế bản chạy sau.

Validation đã dùng trong phát triển: chưa phải xác nhận trên test độc lập hoặc tái lập toàn bộ thiết lập bài báo. CIRCO test có ground truth ẩn; nộp dự đoán theo quy trình chính thức là bước đánh giá độc lập tiếp theo. Số liệu các bản cũ chỉ có ý nghĩa lịch sử.

