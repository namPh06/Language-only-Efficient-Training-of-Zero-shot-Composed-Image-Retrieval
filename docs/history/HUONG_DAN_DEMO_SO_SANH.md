# Demo so sánh ba phiên bản

Trong thư mục project trên ổ D, chạy:

```powershell
..\.venv\Scripts\python.exe -B -X utf8 demo_fti.py
```

Mở http://127.0.0.1:8013. Nếu đang chạy phiên bản giao diện cũ tại cổng này, dừng bằng Ctrl+C rồi chạy lại lệnh.

1. Chuẩn bị kho có các ảnh dễ nhầm: cùng chủ thể nhưng khác trang phục, màu hoặc nền. Có thể thêm ảnh bằng mục Kho ảnh.
2. Chọn ảnh tham chiếu và nhập mô tả bằng tiếng Anh. Ba ví dụ có sẵn chỉ điền mô tả; không bảo đảm trong kho có ảnh phù hợp.
3. Chọn số kết quả và chế độ đo. Ảnh mới bỏ qua cache tham chiếu của cả ba bản; Ảnh dùng lại chuẩn bị đặc trưng trước khi đo. Cache truy vấn được bỏ qua trong cả hai chế độ.
4. Có thể chọn ảnh đối chiếu đã tồn tại trong kho. Giao diện hiển thị thứ hạng của đúng ảnh đó theo nội dung ảnh. Đây là đối chiếu do người trình bày chọn, không phải hệ thống tự xác nhận thuộc tính.
5. Nhấn So sánh cả ba phiên bản. Ba cột hiển thị Top 1 lớn, danh sách có số thứ hạng và thời gian riêng. Các bản chạy tuần tự, thứ tự được luân phiên để giảm thiên lệch đo.
6. Mục Bằng chứng benchmark hiển thị số đã lưu từ CIRCO validation; tách biệt với kết quả trên kho demo.

Thời gian chuẩn bị mô hình/kho/cache được ghi riêng. Lần đầu nạp FTI4CIR có thể chậm hơn các lượt tiếp theo. Thời gian của ba bản cộng lại là thời gian buổi so sánh, không phải độ trễ sử dụng một bản.

Đổi đầu vào sẽ xóa kết quả cũ. Nếu đổi đầu vào khi phép so sánh đang chạy, kết quả cũ không được hiển thị lại sau khi hoàn thành.

Để trình bày công bằng, giữ cùng kho, cùng mô tả và số kết quả. Chọn một vài trường hợp thành công và cả trường hợp thất bại; dùng benchmark đầy đủ để chứng minh kết quả tổng thể. Không so trực tiếp số điểm cosine giữa các bản.

Demo gốc vẫn chạy bằng demo.py. Thuật toán LinCIR, gated, FTI4CIR và vector kho không bị sửa trong lần nâng cấp giao diện này.
