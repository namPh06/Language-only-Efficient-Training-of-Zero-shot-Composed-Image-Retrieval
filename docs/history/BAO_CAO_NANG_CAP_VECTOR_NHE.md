# Nâng cấp nhẹ: giữ đặc điểm đối tượng bằng vector ảnh tham chiếu

## Kết luận

Đã tìm một ứng viên có mức tăng nhỏ trên CIRCO validation, tốc độ gần như ngang bản hiện tại trong ba lượt đo. Tích hợp thành chế độ thử nghiệm; không thay mặc định focused. Chưa đủ cơ sở tuyên bố tốt hơn mọi trường hợp hoặc hiểu mọi thuộc tính.

## Đối chiếu nguyên lý

| Phần | Bản hiện tại | Nhánh thử nghiệm |
|---|---|
| Tạo truy vấn | LinCIR với cách diễn đạt thích ứng | Giữ truy vấn đó, bổ sung nhẹ ảnh tham chiếu |
| Chấm ảnh | g · q | g · (q + 0,05r) |
| Gallery | Vector CLIP đã lưu | Cùng vector đó, không mã hóa lại |
| Model | CLIP và Phi hiện có | Cùng model, không nạp model bổ sung |
| Tìm kiếm | Một lần chấm toàn kho, Top-K chính xác | Một lần chấm toàn kho, Top-K chính xác |
| Thuộc tính | Biểu diễn ngữ nghĩa toàn ảnh | Vẫn biểu diễn toàn ảnh; chưa có kiểm chứng hoa văn/vùng |

q là vector truy vấn LinCIR đã chuẩn hóa, r là vector ảnh tham chiếu CLIP đã chuẩn hóa, g là vector gallery. Không chuẩn hóa lại q + 0,05r vì độ dài chung của truy vấn không đổi thứ tự ảnh. Điểm hiển thị là tương đồng kết hợp, không phải xác suất hoặc xác nhận thuộc tính. Đặc trưng ảnh tham chiếu là đặc trưng đã dùng để tạo pseudo-token; không chạy thêm vision encoder.

## Cách chọn và kiểm chứng

Thử 11 biến thể: hiệu chỉnh tâm vector, loại 1 hoặc 4 thành phần PCA, giảm/tăng nhẹ ảnh hưởng ảnh tham chiếu. 40 truy vấn đầu dùng chọn cấu hình theo mAP@10 với điều kiện Recall@10 không giảm; 180 truy vấn còn lại dùng đánh giá sau chọn. Không chọn lại cấu hình theo kết quả 180 truy vấn. Các phương án hiệu chỉnh tâm không thắng trên nhóm chọn. Ứng viên được chọn là bổ sung ảnh tham chiếu với hệ số cố định 0,05.

Cả 220 truy vấn tìm trên toàn bộ gallery 123403 ảnh. Ba lượt đo cùng process, CPU một luồng; trước mỗi nhánh cung cấp cùng đặc trưng ảnh tham chiếu ngoài bộ đếm thời gian và xóa cache truy vấn. Luân phiên thứ tự hai nhánh. Tất cả thứ hạng khớp với phép tính vector độc lập và lặp lại giống nhau; 660/660 lượt thực sự áp dụng hiệu chỉnh, không tự quay về kết quả cũ.

## Kết quả trên 220 truy vấn

| Chỉ số (%) | Hiện tại | Thử nghiệm | Tăng (điểm %) |
|---|---:|---:|---:|
| mAP@5 | 14.2975 | 15.1136 | +0.8162 |
| mAP@10 | 15.3040 | 16.0903 | +0.7863 |
| mAP@25 | 16.9389 | 17.7426 | +0.8038 |
| mAP@50 | 17.6129 | 18.5211 | +0.9082 |
| Recall@5 | 26.3636 | 29.5455 | +3.1818 |
| Recall@10 | 38.1818 | 39.0909 | +0.9091 |
| Recall@25 | 51.8182 | 54.0909 | +2.2727 |
| Recall@50 | 63.1818 | 63.1818 | +0.0000 |
| GTRecall@10 | 28.8918 | 30.0033 | +1.1115 |

Không gộp ba lần lặp thành 660 truy vấn độc lập để tính độ tin cậy; đó vẫn là 220 truy vấn lặp lại.

| Lượt | Trung vị hiện tại (s) | Thử nghiệm (s) | Tỷ lệ thời gian | P95 hiện tại (s) | Thử nghiệm (s) |
|---|---:|---:|---:|---:|---:|
| 1 | 0.1999 | 0.1994 | 0.9976 | 0.2087 | 0.2097 |
| 2 | 0.1993 | 0.1989 | 0.9976 | 0.2076 | 0.2069 |
| 3 | 0.1994 | 0.1994 | 0.9996 | 0.2083 | 0.2077 |

Chênh lệch thời gian dưới 1% trong ba lượt; coi là tương đương tốc độ, không coi là chứng minh nhanh hơn. Thời gian nạp model, kiểm tra dữ liệu và chuẩn bị đặc trưng được ghi riêng; không so trực tiếp các con số này với lượt FG-CLIP khác phiên.

## Độ chắc chắn trên 180 truy vấn đánh giá riêng

| Chỉ số | Tăng (điểm %) | Bootstrap ghép cặp 95% |
|---|---:|---|
| AP@5 | +0.7627 | [-0.18241898148148147, 1.8452353395061727] |
| AP@10 | +0.7733 | [-0.09617072677836559, 1.777606692754262] |
| AP@50 | +0.9533 | [0.10166979122601219, 1.9480448473403937] |
| Recall@10 | +1.1111 | [0.0, 2.7777777777777777] |
| GTRecall@10 | +0.8624 | [-0.013227513227513261, 1.8571428571428572] |

mAP@50 có khoảng tin cậy hoàn toàn dương. mAP@10 có khoảng tin cậy cắt 0, nên chưa đạt điều kiện tăng mAP@10 rõ ràng trên nhóm đánh giá riêng. Khoảng tin cậy mAP@10 trên toàn bộ 220 truy vấn dương nhưng có gồm 40 truy vấn chọn cấu hình; không dùng riêng kết quả đó để bỏ qua giới hạn này.

## Theo nhóm yêu cầu

| Nhóm CIRCO | Hiện tại mAP@10 (%) | Thử nghiệm (%) | Tăng (điểm %) |
|---|---:|---:|---:|
| addition | 14.4469 | 14.4437 | -0.0032 |
| cardinality | 20.5709 | 22.1772 | +1.6063 |
| comparative_statement | 10.2956 | 11.0766 | +0.7810 |
| compare_change | 13.3588 | 14.6007 | +1.2419 |
| direct_addressing | 15.6226 | 16.3171 | +0.6945 |
| negation | 8.4805 | 8.5750 | +0.0945 |
| spatial_relations_background | 15.4008 | 16.2951 | +0.8944 |
| statement_with_conjunction | 13.0179 | 14.1526 | +1.1347 |
| viewpoint | 10.7870 | 12.5730 | +1.7860 |

Các nhóm chồng lấn nhau. Nhóm addition giảm rất nhỏ; không phải mọi nhóm đều tăng. Đây là so sánh mô tả, không phải bảo đảm có ý nghĩa thống kê cho từng nhóm.

## Giới hạn và cách dùng

- CIRCO validation đã được dùng trong các lần phát triển trước. Nhóm 180 ở đây không phải test set độc lập chưa từng được biết.
- Mức tăng còn nhỏ; một số truy vấn riêng vẫn có thể yếu đi.
- Giữ đặc điểm ảnh tham chiếu có thể giữ cả nền hoặc trang phục cũ mà người dùng muốn thay.
- Không phát hiện, phân vùng hay đối chiếu từng hoa văn; không thay thế kiểm chứng thuộc tính.
- Không cam kết mức tăng trên kho local hoặc benchmark khác.
- Không train thêm và không thay checkpoint LinCIR.

Khởi động lại demo, chọn **Thử nghiệm — giữ đặc điểm đối tượng**. Không cần chạy chuẩn bị FG-CLIP hay tạo thêm vector ảnh. Đổi về **Tìm nhanh — truy vấn thích ứng** để dùng nguyên cách hiện tại.

Dừng demo rồi chạy `ROLLBACK_BALANCED.cmd` để khôi phục mã trước nhánh này. Công cụ kiểm tra SHA-256 và từ chối ghi đè file người dùng đã sửa thêm; không xóa ảnh/vector/model. Bản sao ở `outputs/rollback_before_balanced_v1`. Nếu muốn khôi phục xa hơn về trước cả FG-CLIP, khôi phục balanced trước rồi dùng công cụ rollback FG-CLIP cũ; không cần dùng --force.

## Tái chạy

```powershell
..\.venv\Scripts\python.exe -B -X utf8 benchmark_circo.py --modes focused balanced --cpu-threads 1 --batch-size 1 --prepared-reference-latency --latency-reference focused --max-latency-ratio 1.15 --output outputs/vector_research/balanced_repeat_new.json
```

Chọn tên output mới khi mã/cấu hình thay đổi. Báo cáo gốc của thử nghiệm vector, ba lượt native và lượt xác nhận tích hợp nằm trong `outputs/vector_research`.

## Nghiên cứu tham khảo

- BASIC/i-CIR: https://github.com/billpsomas/icir (hiệu chỉnh đặc trưng, phép chiếu và phối trộn; nhánh này không triển khai đầy đủ BASIC).
- WeiMoCIR: https://arxiv.org/abs/2409.04918 (hướng phối trộn vector ảnh/văn bản; nhánh này là hiệu chỉnh riêng trên truy vấn LinCIR, không tái hiện đầy đủ WeiMoCIR).

## Xác nhận sau tích hợp

Đã chạy đủ 220 truy vấn bằng `benchmark_circo.py --modes focused balanced`, snapshot gallery hợp lệ. Toàn bộ thứ hạng hai nhánh khớp với ba lượt prototype; 220/220 lượt dùng hiệu chỉnh thật. Nhánh focused không áp dụng hiệu chỉnh.

| Chỉ số thời gian | Hiện tại | Nhánh mới |
|---|---:|---:|
| Trung vị (s) | 0.305887 | 0.305765 |
| P95 (s) | 0.411942 | 0.422247 |

Ba lượt prototype đo trực tiếp hàm tìm ảnh, còn benchmark tích hợp đo cả bước chuyển đường dẫn kết quả thành ID benchmark trong `run_mode`. Vì phạm vi đo khác nhau, không so tuyệt đối khoảng 0,20 giây prototype với khoảng 0,31 giây benchmark tích hợp; chỉ so hai nhánh trong cùng lượt. Cả hai phép đo đều cho tốc độ tương đương.

Đã kiểm tra giao diện giữ focused mặc định, không tự nạp FG-CLIP khi mở demo, kiểm tra công thức vector và khôi phục thật trong thư mục tạm. Thư mục test đã được xóa.
