# Kết quả nâng cấp FTI4CIR — 12/10/2026

## Kết luận

Giữ FTI4CIR thuần làm bản thử nghiệm mới. LinCIR gốc và gated không bị sửa; demo cũ vẫn hoạt động như trước. Demo mới mặc định vẫn chọn gated. Không giữ biến thể FTI4CIR + gated trong giao diện vì điểm thấp hơn FTI4CIR thuần.

## Benchmark đầy đủ

CIRCO validation: 220 truy vấn, toàn bộ 123.403 ảnh, loại ảnh tham chiếu, 50 kết quả/truy vấn. Chạy CPU, một luồng, luân phiên thứ tự bốn phương pháp. Hoàn thành 14.06 phút, giới hạn cứng 20 phút. Đã xác nhận kho ảnh không thay đổi trong khi chạy.

| Phiên bản | mAP@10 | mAP@50 | Trung vị phần truy vấn khi đặc trưng tham chiếu đã chuẩn bị |
|---|---:|---:|---:|
| baseline | 14.0374 | 16.2586 | 0.1969 s |
| gated | 16.6649 | 19.0203 | 0.1722 s |
| fti_clip | 18.9948 | 21.7146 | 0.1149 s |
| fti_clip_gated | 18.6395 | 21.2445 | 0.1223 s |

FTI4CIR tăng 2,3299 điểm mAP@10 (+13,98%) và 2,6943 điểm mAP@50 (+14,17%) so với gated. So với LinCIR gốc, tăng khoảng 35,32% và 33,56% tương ứng. Điểm baseline/gated khớp mốc benchmark trước.

## Độ trễ sử dụng thực tế

Kiểm tra bổ sung năm ảnh, xóa cache RAM trước mỗi lần ảnh mới; ép gated trích xuất lại đặc trưng để mô phỏng ảnh chưa từng xuất hiện. Với ảnh dùng lại, giữ token/đặc trưng nhưng xóa cache truy vấn để không chỉ trả lại kết quả cũ. Không bao gồm khởi động mô hình và dựng kho.

| Phiên bản | Ảnh mới | Ảnh dùng lại trong phiên |
|---|---:|---:|
| baseline | 2.9204 s | 0.2074 s |
| gated | 2.7501 s | 0.1577 s |
| fti_clip | 3.0789 s | 0.1777 s |

Ảnh mới: FTI4CIR chậm hơn baseline khoảng 5,43%, chậm hơn gated khoảng 11,96%. Ảnh dùng lại: nhanh hơn baseline trong phép đo này, nhưng chậm hơn gated khoảng 12,66%. Đây là phép đo năm ảnh, chưa đủ để kết luận phân bố độ trễ/p95 cho mọi ảnh.

## Cải tiến thuật toán

LinCIR dùng pseudo-token biểu diễn toàn ảnh. FTI4CIR bổ sung 24 mẫu thuộc tính được học, transformer ba lớp đọc 257 token thị giác, chọn tối đa 12 thuộc tính theo trọng số và ngưỡng 0,05; hai mạng ánh xạ biến chủ thể và thuộc tính thành pseudo-token văn bản. Truy vấn gồm chủ thể, thuộc tính và mô tả thay đổi được mã hóa trong không gian CLIP rồi so với vector kho.

Tối ưu CPU: lấy vector toàn ảnh và token vùng trong cùng một lượt CLIP; rút chuỗi văn bản đến EOT khi dùng causal attention; chọn top-k chính xác; lưu token của 16 ảnh tham chiếu gần nhất trong RAM. Không đọc và kiểm chứng lần lượt 123.403 ảnh khi tìm.

## Kiểm chứng bổ sung

- Demo adapter khớp toàn bộ top-50 của benchmark cho năm truy vấn kiểm tra, cả khi có và không có cache.
- Encoder rút ngắn và encoder đủ 77 token có sai số tuyệt đối tối đa 2.24e-07.
- Mô tả chứa ký hiệu * vẫn được mã hóa đúng; giới hạn token được báo rõ trong demo.
- Giao diện ba chế độ dựng thành công. Chưa chạy kiểm thử tương tác browser.
- Mã băm bảy file/mô hình bảo vệ đều không thay đổi.

## Các nhóm mô tả

| Nhóm | gated mAP@10 | FTI4CIR mAP@10 |
|---|---:|---:|
| addition | 15.720 | 17.245 |
| cardinality | 21.871 | 23.072 |
| comparative_statement | 10.607 | 14.058 |
| compare_change | 15.249 | 16.020 |
| direct_addressing | 16.471 | 20.171 |
| negation | 8.933 | 9.136 |
| spatial_relations_background | 16.974 | 21.973 |
| statement_with_conjunction | 14.207 | 18.271 |
| viewpoint | 11.766 | 13.148 |

## Giới hạn và cách hiểu kết quả

- Đây là biến thể FTI4CIR dùng center-crop CLIP để tái sử dụng vector kho hiện tại. Mã chính thức mặc định targetpad 1,25. Không coi số trên là tái lập nguyên vẹn kết quả bài báo FTI4CIR.
- Kho vector cũ được giữ nguyên; không cần mã hóa lại 123.403 ảnh. Có thêm checkpoint khoảng 217 MB.
- Token thuộc tính hiện lưu RAM, tối đa 16 ảnh. Đổi ảnh hoặc khởi động lại có thể cần trích xuất lại khoảng ba giây. Không có cache thuộc tính bền vững trên đĩa.
- Cải thiện trên validation không bảo đảm đúng từng truy vấn, mọi thuộc tính nhỏ hoặc chữ/hoa văn. Đây là mô hình truy hồi ảnh có sẵn, không tạo ảnh.
- Bootstrap theo cặp 10.000 lượt: khoảng tin cậy 95% của tăng mAP@10 là [-0,2303; 4,9303] điểm, vẫn chứa 0; mAP@50 [0,2293; 5,1905] điểm. Vì vậy bằng chứng thống kê mAP@50 rõ hơn mAP@10.
- Validation đã được dùng để chọn phương pháp qua nhiều thử nghiệm. Cần test độc lập hoặc nộp CIRCO test trước khi tuyên bố khả năng tổng quát hay vượt trội tuyệt đối.
- Paracosm: đặc trưng công bố có 800 truy vấn test, không có ID truy vấn trong dictionary đặc trưng đã đọc. Không dùng chúng làm 220 truy vấn validation và không tuyên bố đã benchmark Paracosm. DiCE-CIR chưa có checkpoint xác minh; LamRA chưa chạy trong lượt này.

## Chạy và quay lại

Trong thư mục project trên ổ D, chạy:

```powershell
..\.venv\Scripts\python.exe -B -X utf8 demo_fti.py
```

Mở http://127.0.0.1:8013, nhấn So sánh cả ba phiên bản để xem LinCIR gốc, gated và FTI4CIR cạnh nhau. Xem HUONG_DAN_DEMO_SO_SANH.md. demo.py và lệnh chạy cũ không đổi.

## Nguồn và bằng chứng

- Mã và checkpoint chính thức: https://github.com/iLearn-Lab/SIGIR24-FTI4CIR ; https://huggingface.co/iLearn-Lab/SIGIR24-FTI4CIR
- Commit nguồn lưu tại experiments/fti4cir/source_commit.txt.
- SHA256 checkpoint: aa1acd03fba4e70f77b6afbf296f849e58dddcb899f05e613bf677435ff1a967.
- Bằng chứng: outputs/fti_trial_20261012/benchmark.json, verification.json, protocol.json, run_status.json và các log.
- File test tạm được xóa sau kiểm tra; giữ báo cáo và kết quả để đối chiếu.