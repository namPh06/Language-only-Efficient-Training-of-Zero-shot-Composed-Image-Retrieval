# Demo hiện tại — hai phiên bản

Mở terminal trong thư mục project, chạy `python demo.py`. Demo tự dùng `.venv` ở thư mục cha, không cần train lại. Trình duyệt mở http://127.0.0.1:8000. Cổng bận: `python demo.py --port 8001`.

1. Chép ảnh vào `gallery`, hoặc chọn file rồi nhấn **Thêm ảnh vào kho**.
2. Chọn ảnh tham chiếu, nhập tiếng Anh: `wearing a blue shirt`, `is on a beach`, `without a hat`.
3. Chọn **Bản gốc LinCIR** hoặc **Bản nâng cấp — truy vấn thích ứng + kết hợp điểm**.
4. Nhấn **Tìm ảnh**. Đổi phiên bản sẽ xóa kết quả cũ; nhấn lại để tìm.

Bản nâng cấp mặc định chọn cách diễn đạt theo độ dài truy vấn và kết hợp điểm với ảnh tham chiếu; dùng cùng CLIP/Phi và vector kho với bản gốc. Nó không kiểm chứng từng ảnh bằng detector/VQA. Điểm kết hợp không phải cosine thuần hay xác suất. Ảnh giống hệt ảnh tham chiếu được loại khỏi kết quả.

Vector kho được lưu trên ổ đĩa và dùng lại khi chạy tiếp. Chỉ ảnh mới/thay đổi cần mã hóa. Phải giữ ảnh để hiển thị và mã hóa truy vấn: vector không thay thế file ảnh.

Hệ thống tìm ảnh có sẵn, không tạo/chỉnh sửa ảnh. Có thể xếp hạng sai với chi tiết nhỏ, phủ định hay nhiều thuộc tính; không bảo đảm mọi ảnh kết quả đáp ứng từng điều kiện.

Tùy chọn: `python demo.py --gallery "D:\KhoAnh"`, `python demo.py --no-browser`, `python demo.py --source laion`. LAION chỉ dùng gốc và phụ thuộc dịch vụ online; kết nối chưa được xác nhận bởi benchmark local. Demo gửi vector, không gửi ảnh gốc.

Checkpoint: `pretrained_models/lincir_large.pt`. Cache CLIP/tokenizer: `C:/hf_cache`, đổi bằng `--cache_dir`. Máy đang chạy CPU. Thông báo CLIPImageProcessor dùng PIL hoặc UNEXPECTED khi nạp riêng nhánh CLIP có thể xuất hiện khi khởi động; xem lỗi cuối nếu giao diện không mở.

Xem `HUONG_DAN_CIRCO.md` và `KET_QUA_CHON_PHIEN_BAN_TOT_NHAT.md`. Các nhánh cũ đã loại không còn hỗ trợ; giữ báo cáo/số liệu lịch sử để đối chiếu.

