# Báo cáo cải tiến truy vấn thích ứng và kiểm chứng tốc độ

Ngày thực hiện: 10/10/2026. Mục tiêu: tăng chất lượng truy hồi so với LinCIR gốc, không đánh đổi bằng việc kiểm chứng nặng từng ảnh.

## 1. Bản cũ và bản được chọn

| Thành phần | LinCIR cũ | Truy vấn thích ứng mới |
|---|---|---|
| Bộ mã hóa ảnh, văn bản và mạng Phi | CLIP ViT-L/14 và checkpoint LinCIR hiện có | Giữ nguyên |
| Câu chứa pseudo-token ảnh | `a photo of $ that {description}` | Yêu cầu tối đa 10 từ: `$ , {description}`; dài hơn: giữ cách cũ |
| Câu người dùng đã có `$` | Giữ câu tùy chỉnh | Giữ nguyên, vẫn kiểm tra token hợp lệ và độ dài |
| Chấm điểm | Cosine với toàn bộ vector gallery, sắp thứ tự | Cosine với toàn bộ gallery, chọn Top-K chính xác |
| Xử lý ảnh tham chiếu | Có thể mã hóa lại khi chưa có cache | Dùng lại đặc trưng ảnh gốc trong RAM/đĩa; ảnh mới vẫn phải mã hóa lần đầu |
| Mã hóa câu mới | Một lượt | Một lượt, không thêm detector/VQA hay câu kiểm chứng |
| Loại ảnh theo điều kiện cứng | Không | Không; tránh mất ảnh đúng vì kiểm chứng sai |

Số từ tính bằng biểu thức `\b\w+\b`; dấu gạch nối tách từ. Ngưỡng 10 là quy tắc thực nghiệm, không phải một định luật ngữ nghĩa. Quy tắc giữ đầy đủ mô tả và không dùng đáp án benchmark khi tìm ảnh. Đây là cải tiến cách tạo truy vấn và thực thi của hệ thống, không phải huấn luyện một mô hình mới hay nâng cấp khả năng hiểu từng vật thể.

## 2. Các hướng đã thử và loại bỏ

Tham số trong từng họ được chọn trên nhóm phát triển 110 truy vấn; nhóm còn lại gồm 110 truy vấn dùng để xem mức ổn định. Chia nhóm cố định bằng seed 20261010.

| Hướng | Phạm vi thử | Kết luận |
|---|---|---|
| Trộn vector mô tả, trừ vector tham chiếu | 64 cấu hình | Có tăng nhỏ, chưa đủ rõ; không đưa vào chế độ mới |
| Định tâm gallery và mở rộng truy vấn bằng ảnh gần nhất | 68 cấu hình | Tăng ở nhóm phát triển nhưng giảm trên nhóm đối chiếu; loại |
| Đổi mẫu câu truy vấn | 24 cấu hình | Câu ngắn có triển vọng, thời gian mã hóa gần như cũ |
| Thay độ lớn pseudo-token | 42 cấu hình | Tham số tốt ở nhóm phát triển giảm trên nhóm đối chiếu; loại |
| Chọn mẫu câu theo độ dài đầu vào | Các quy tắc từ số từ/liên từ/phủ định | Chọn ngưỡng 10 từ; mAP@10 tăng ở cả hai nhóm |

Với quy tắc được chọn, mAP@10 nhóm phát triển tăng 15,047 → 15,949; nhóm đối chiếu tăng 13,028 → 14,659. Các hướng có dấu hiệu giảm chất lượng được loại bỏ dù nhanh. Không đưa kiểm chứng vùng/quan hệ nặng vào chế độ mặc định này.

**Giới hạn thiết kế thực nghiệm:** đây vẫn là khảo sát trên validation CIRCO. Validation đã được dùng trong những lần thử trước; nhóm đối chiếu cũng được xem qua nhiều họ phương pháp. Vì vậy không gọi đây là test độc lập chưa từng nhìn thấy, và chưa chứng minh khả năng khái quát trên test chính thức.

## 3. Benchmark thực tế toàn bộ validation

Gallery chính thức: 123.403 ảnh; 220 truy vấn. Loại ảnh tham chiếu khỏi ứng viên theo giao thức hiện có. Không dùng nhãn đáp án hay shared_concept trong suy luận. Kết quả native đã hoàn tất, `snapshot_verified=true`, `partial=false`. Tất cả 220 thứ tự Top-50 baseline khớp kết quả baseline lịch sử.

| Chỉ số (%) | Bản cũ | Bản mới | Chênh lệch điểm phần trăm |
|---|---:|---:|---:|
| mAP@5 | 12,529 | 14,297 | +1,768 |
| mAP@10 | 14,037 | 15,304 | +1,267 |
| mAP@25 | 15,583 | 16,939 | +1,356 |
| mAP@50 | 16,259 | 17,613 | +1,354 |
| Recall@5 | 23,636 | 26,364 | +2,727 |
| Recall@10 | 37,273 | 38,182 | +0,909 |
| Recall@25 | 51,818 | 51,818 | 0 |
| Recall@50 | 62,727 | 63,182 | +0,455 |
| GTRecall@25 | 41,795 | 41,709 | -0,086 |
| GTRecall@50 | 51,776 | 51,969 | +0,193 |

mAP@5 tăng khoảng 14,1% tương đối; mAP@10 tăng khoảng 9,0% tương đối. Không nhầm các tỷ lệ này với mức tăng điểm phần trăm. Bản nhanh trước đó đạt mAP@10 14,424 và mAP@50 16,518 trên cùng validation; bản thích ứng nâng tiếp lên 15,304 và 17,613. Không phải mọi chỉ số đều tăng: GTRecall@25 giảm rất nhẹ, Recall@25 giữ nguyên.

## 4. Tốc độ và cách đo công bằng

Lượt hoàn chỉnh đầu tiên (`circo_focused_full_v1.json`): trung vị bản cũ 0,3584 giây/truy vấn; bản mới 0,3375 giây/truy vấn, giảm khoảng 5,8%. Cả hai được cấp cùng đặc trưng tham chiếu gốc đã chuẩn bị trước, xóa cache truy vấn trước mỗi lượt; thứ tự hai chế độ luân phiên. Chi phí nạp model/index và chuẩn bị đặc trưng được ghi riêng. Vì vậy đây là tốc độ tìm kiếm khi đã có vector tham chiếu, không phải thời gian mở chương trình hoặc xử lý ảnh mới lần đầu.

Không dùng số baseline khoảng 3,6 giây từ giao thức cũ để tuyên bố nhanh hơn 8–9 lần: phép đo cũ có lợi thế cache không đồng đều. Ảnh tham chiếu mới vẫn cần mã hóa ảnh ở cả hai bản; chưa có bằng chứng rằng tốc độ lạnh giảm mạnh.

Runner có giới hạn `--max-latency-ratio 1.25`: từ 10 truy vấn trở đi, nếu trung vị bản nâng cấp vượt 1,25 lần baseline, dừng và lưu kết quả chưa hoàn tất. Ngưỡng này áp dụng trong lượt benchmark; đây không phải bảo đảm từng truy vấn riêng lẻ luôn nằm dưới ngưỡng. Bộ vector gallery cũ được dùng lại, không mã hóa lại 123.403 ảnh.

## 5. Độ chắc chắn và hạn chế

Bootstrap cặp 10.000 lần, seed 20261010, cho chênh lệch mAP@5 khoảng tin cậy 95% [0,171; 3,489] điểm; mAP@10 [-0,147; 2,784]; mAP@50 [-0,0003; 2,829]. Các khoảng này chưa điều chỉnh việc thử nhiều cấu hình; không dùng chúng để tuyên bố phương pháp chắc chắn tốt hơn trên mọi tập. mAP@10 và mAP@50 còn khoảng chứa 0.

Mô hình vẫn có thể sai về phủ định, quan hệ, đếm số lượng và vật thể nhỏ. Quy tắc độ dài không trực tiếp hiểu ảnh hay kiểm tra tất cả yêu cầu. Những trường hợp khó vẫn cần dữ liệu đánh giá bổ sung; không đảm bảo mỗi câu mèo mặc áo/ở bãi biển sẽ đúng. Muốn kết luận nghiên cứu mạnh hơn cần chốt cấu hình rồi đánh giá tập mới hoặc test chính thức, không tiếp tục chọn ngưỡng theo nhãn validation.

## 6. Tích hợp và sử dụng

`demo.py` mặc định chọn **Tìm nhanh — truy vấn thích ứng**. Kết quả nằm trong ô cùng tên; chế độ mới không chạy thêm baseline để hiển thị song song, tránh nhân đôi thời gian. Có thể chọn **Bản cũ** để so sánh thủ công. Các chế độ kiểm chứng nặng trước đó được giữ để người dùng chủ động chọn.

Chạy demo bằng môi trường hiện có. Không cần train lại, cài thêm gói hay tải lại ảnh/vector. Nếu web đang chạy phiên bản cũ, dừng và mở lại demo. File trước nâng cấp được sao lưu tại `outputs/focused_upgrade_backup`.

Lệnh benchmark lặp lại với cùng giao thức:

```powershell
..\.venv\Scripts\python.exe -B -X utf8 benchmark_circo.py --modes baseline focused --pool-size 100 --cpu-threads 1 --batch-size 1 --prepared-reference-latency --max-latency-ratio 1.25 --output outputs/circo_focused_repeat.json
```

Các kiểm tra cú pháp, ranh giới 10/11 từ, giữ câu tùy chỉnh, câu về mũ/áo/bãi biển/phủ định/đen trắng, chuyển chế độ và cấu hình giao diện đã thực hiện. Kiểm tra câu ở đây xác nhận đường đi xử lý không bị bỏ qua hay mất mô tả, không chứng minh chất lượng tìm ảnh của từng câu. File test và script thử nghiệm tạm đã xóa; số liệu JSON/NPZ giữ lại để đối chiếu.


## 7. Lượt xác nhận sau khi hoàn tất giao diện

File `outputs/circo_focused_full_v2.json` hoàn tất 220/220 truy vấn, `snapshot_verified=true`, `partial=false`. Mã nguồn hiện tại khớp code_hash của lượt này. Toàn bộ Top-50 của cả hai chế độ khớp lượt v1, vì sửa cuối chỉ liên quan hiển thị giao diện.

Trung vị bản cũ 0.3761 giây; bản mới 0.3388 giây, giảm 9.9% theo cùng giao thức vector tham chiếu đã chuẩn bị. Thời gian có dao động giữa các lượt, không coi mức giảm nhỏ này là lợi thế đảm bảo trên mọi máy. Chất lượng lặp lại chính xác các số ở bảng phía trên.

| Thời gian (giây/truy vấn) | Bản cũ | Bản mới |
|---|---:|---:|
| Trung vị | 0.3761 | 0.3388 |
| Trung bình | 0.3748 | 0.3371 |
| Phân vị 95% | 0.4448 | 0.4067 |
