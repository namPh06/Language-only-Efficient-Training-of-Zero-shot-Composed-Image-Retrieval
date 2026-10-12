# Kết quả thử nâng cấp mở rộng — 12/10/2026

Giữ nguyên bản gốc LinCIR và gated. Chưa có biến thể mới đáp ứng đồng thời yêu cầu chất lượng và tốc độ để thay gated. Không thêm chế độ vào demo.

## 1. Lượt benchmark đầy đủ

CIRCO validation: đủ 220 truy vấn, kho đủ 123.403 ảnh. Snapshot dữ liệu đã xác minh. CPU một thread, luân phiên thứ tự ba chế độ, cache truy vấn RAM độc lập. Nhãn đáp án chỉ được dùng sau suy luận để tính metrics. Dự đoán baseline/gated trùng toàn bộ với mốc đã lưu trước đó.

| Bản | mAP@5 | mAP@10 | mAP@50 | Recall@10 | Thời gian trung vị/truy vấn |
|---|---:|---:|---:|---:|---:|
| Bản gốc | 12.53% | 14.04% | 16.26% | 37.27% | 0.202 giây |
| Gated | 15.63% | 16.66% | 19.02% | 40.45% | 0.182 giây |
| Truy vấn chú ý vùng, đã có cache | 14.82% | 15.83% | 18.21% | 41.36% | 0.213 giây |

Biến thể vùng tốt hơn bản gốc về mAP, nhưng kém gated 0.83 điểm phần trăm mAP@10 và 0.81 điểm phần trăm mAP@50. Recall@10 nhỉnh hơn gated, nhưng không đạt tiêu chí cải thiện hai chỉ số mAP chính. Do đó không chọn. Mức chậm so với bản gốc khoảng 5,0%; so với gated khoảng 17.0% trong lượt đo này.

Toàn lượt gồm cả đối chứng mất 13.25 phút, dưới 20 phút. Timer truy vấn bên trên giả định đặc trưng tham chiếu đã chuẩn bị. Riêng tạo/lấy cache vùng tốn 590.81 giây tổng cộng, khoảng 2.69 giây mỗi ảnh; cache thử nghiệm 173.04 MB. Vì vậy không được suy ra ảnh mới chưa cache cũng chỉ tốn 0,21 giây.

Bootstrap AP@10 so với gated: trung bình -0,833 điểm phần trăm, khoảng 95% có điều kiện trên validation [-1,808; +0,041]. Có 39 truy vấn tốt hơn, 48 kém hơn, 133 bằng nhau. Khoảng này chứa 0: không tuyên bố mức suy giảm có ý nghĩa thống kê chắc chắn; kết luận là chưa có bằng chứng cải thiện để thay gated. Validation đã được dùng trong phát triển, không phải đánh giá test độc lập.

## 2. Sàng lọc tốc độ trên benchmark thật

| Biến thể | Số truy vấn đã chạy | Thời gian trung vị | So với baseline cùng lượt | Quyết định |
|---|---:|---:|---:|---|
| patch_rerank | 10 | 13.11 giây | 65.1 lần | Dừng sớm, loại về tốc độ |
| crop_rerank | 10 | 13.22 giây | 67.5 lần | Dừng sớm, loại về tốc độ |
| Vùng tham chiếu tính trực tiếp, chưa cache | 46 | 2.87 giây | 14.5 lần | Dừng sớm, chuyển sang thử cache |

Hai cách xếp lại chỉ mã hóa 5 ứng viên đầu nhưng vẫn chậm nhiều lần. Dừng sau 10 truy vấn theo điều kiện sàng lọc tốc độ đã ghi trong protocol và yêu cầu trước đó loại bản chậm nhiều lần. Mỗi lượt có watchdog cứng 1200 giây gồm startup và chuẩn bị; không lượt nào vượt 20 phút. Hai kết quả 10 truy vấn là một phần: không dùng mAP của chúng để kết luận chất lượng toàn tập. Chỉ giữ dữ liệu đo làm bằng chứng.

## 3. Những phương pháp từ bài báo chưa benchmark được

- RTD: đã kiểm tra README, cây mã, releases, issues và tìm kiếm checkpoint; chưa tìm thấy trọng số bộ mã hóa text đã train tương thích. Có mã huấn luyện và dữ liệu text, nhưng chưa chạy được đúng phương pháp khi thiếu checkpoint. Nguồn: https://github.com/jaeseokbyun/RTD .
- ConText-CIR: đã kiểm tra kho và trang dự án; chưa tìm thấy link checkpoint khả dụng. Issue đề nghị phát hành artifacts chưa có phản hồi; tác giả mô tả thí nghiệm thường dùng một GPU 80GB. Nguồn: https://github.com/mvrl/ConText-CIR và https://ericx003.github.io/proj/context_cir/ .
- DistillCIR: kho trang dự án nhánh master có HTML/tài nguyên trình bày, chưa tìm thấy mã suy luận và checkpoint tương thích; URL trang trả 404 lúc kiểm tra. Nguồn: https://github.com/distillcir/distillcir.github.io .
- Reranker đa phương thức lớn: chưa có trọng số trong cache hiện tại. Không có benchmark hợp lệ cho phương án này trong lượt thử; không kết luận nhanh/chậm/đúng sai từ mô hình chưa chạy.

Đây là tình trạng thiếu điều kiện chuẩn bị trong những nguồn đã kiểm tra, không phải khẳng định các phương pháp không tốt hoặc không có checkpoint ở bất cứ đâu. Cần checkpoint đã train đúng, hoặc môi trường/dữ liệu huấn luyện phù hợp, rồi mới đo được. Không dùng heuristic CLIP để gán thành kết quả của RTD/ConText-CIR/DistillCIR.

## 4. Nguyên lý thử nghiệm và hạn chế

Các biến thể CLIP vùng/crop là thuật toán thử riêng do trợ lý xây dựng, không tái hiện ba bài báo. Chi tiết tham số có ở outputs/expansion_trials_20261012/method_description.md, protocol.json và trial_source_sha256.json.

CLIP có sẵn được huấn luyện theo biểu diễn toàn ảnh; chiếu patch sang không gian text không tự tạo khả năng hiểu từng thuộc tính. Chú ý vào text mong muốn có thể chọn sai vùng nếu thuộc tính chưa tồn tại trong ảnh gốc. Ảnh cắt giữa không bảo đảm chứa đối tượng. Đây là các khả năng giải thích lỗi, không phải kết luận nhân quả đã được kiểm chứng bằng ablation.

## 5. Bảo toàn và dọn dẹp

Mã, checkpoint bản gốc/gated được đối chiếu SHA256 trước/sau; tất cả không đổi. Kho ảnh, cache vector gallery và cache tham chiếu cũ giữ nguyên. Mã test tạm và cache vùng của biến thể bị loại được xóa sau khi các tiến trình kết thúc. Dữ liệu benchmark JSON/log, mô tả phương pháp và bằng chứng kiểm tra nguồn được giữ lại.

Tiếp tục dùng gated làm mốc. Hướng có cơ sở tiếp theo là lấy checkpoint mô hình truy vấn đã học CIR/hiểu lệnh, hoặc huấn luyện trên dữ liệu độc lập với nhãn đánh giá; chưa thể thay gated chỉ dựa trên tên phương pháp hoặc điểm trong bài báo.
