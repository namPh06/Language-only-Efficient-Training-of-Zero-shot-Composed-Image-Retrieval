# Benchmark CIRCO: bản cũ và bản tìm nhanh

Chạy ngày 10/10/2026 trên máy hiện tại: đủ 220 truy vấn validation, gallery 123.403 ảnh, Top-50, pool 100, CPU 1 luồng, batch 1. Dùng cùng checkpoint LinCIR và vector gallery. Không train lại hoặc lựa chọn tham số theo đáp án.

## Kết quả

| Chỉ số | Bản cũ | Bản nhanh | Chênh lệch nhanh - cũ |
|---|---:|---:|---:|
| mAP@5 (%) | 12.529 | 13.016 | +0.487 điểm phần trăm |
| mAP@10 (%) | 14.037 | 14.424 | +0.387 điểm phần trăm |
| mAP@25 (%) | 15.583 | 15.817 | +0.234 điểm phần trăm |
| mAP@50 (%) | 16.259 | 16.518 | +0.259 điểm phần trăm |
| Recall@5 (%) | 23.636 | 22.727 | -0.909 điểm phần trăm |
| Recall@10 (%) | 37.273 | 37.273 | +0.000 điểm phần trăm |
| Recall@25 (%) | 51.818 | 50.000 | -1.818 điểm phần trăm |
| Recall@50 (%) | 62.727 | 61.364 | -1.364 điểm phần trăm |
| GTRecall@10 (%) | 28.653 | 28.022 | -0.631 điểm phần trăm |
| GTRecall@25 (%) | 41.795 | 39.675 | -2.120 điểm phần trăm |
| GTRecall@50 (%) | 51.776 | 50.273 | -1.504 điểm phần trăm |
| Trung vị giây/truy vấn | 3.619 | 0.415 | -3.205 giây |
| Trung bình giây/truy vấn | 3.638 | 0.419 | -3.219 giây |
| P95 giây/truy vấn | 4.339 | 0.521 | -3.818 giây |
| Tổng giây tìm kiếm 220 truy vấn | 800.438 | 92.288 | -708.150 giây |

## Cách đọc tốc độ và chi phí lần đầu

Tỷ số trung vị trong giao thức này: 8.73 lần. Cache RAM ảnh/truy vấn được xóa trước mỗi chế độ; bản nhanh dùng cache đĩa ảnh tham chiếu và mô tả đã chuẩn bị, còn bản cũ mã hóa lại ảnh tham chiếu. Vì vậy tỷ số này đo lợi ích của cả cache và cách tìm kiếm, không tách riêng hiệu quả thuật toán và không phải so sánh hai bản đều đã có cache RAM.

Chuẩn bị đủ 220 cặp đầu vào mất 754.65 giây (12.58 phút), tạo ngân hàng 379 vector mô tả. Đây là thời gian phiên chuẩn bị này, đã có sẵn cache của 10 truy vấn thử trước đó; không phải phép đo hoàn toàn từ cache rỗng. Chỉ sử dụng ảnh tham chiếu và mô tả, không sử dụng ảnh đích hoặc nhãn đúng để suy luận.

Tải model và kiểm tra/nạp chỉ mục trong phiên benchmark: 68.93 giây. Tổng thời gian tìm kiếm được ghi ở bảng trên; không bao gồm chuẩn bị, tải model, kiểm tra cuối phiên hoặc ghi file. Vector gallery đã có đủ nên không cần mã hóa lại 123.403 ảnh. Khi chạy lại có thể tái sử dụng cache; ảnh/mô tả mới vẫn phát sinh chi phí mã hóa lần đầu.

## Kết luận và giới hạn

Bản nhanh cải thiện nhẹ mAP ở cả bốn mức K, nhưng Recall@5, @25, @50 và GTRecall@10, @25, @50 giảm. Recall@10 giữ nguyên. Do đó chưa thể khẳng định tốt hơn bản cũ về mọi tiêu chí; mức tăng mAP nhỏ, chưa có kiểm định ý nghĩa thống kê và đây là tập validation.

Bằng chứng CLIP toàn ảnh vẫn có thể sai về phủ định, vật thể nhỏ và quan hệ. Fast dùng Top-K chính xác và hiệu chỉnh có giới hạn; chưa dùng chỉ mục ANN và không có bước xác nhận thuộc tính bằng detector/VQA.

## Theo nhóm yêu cầu

| Nhóm (có thể chồng lấp) | mAP@10 bản cũ (%) | mAP@10 bản nhanh (%) | Chênh lệch |
|---|---:|---:|---:|
| addition | 12.911 | 12.746 | -0.165 |
| cardinality | 19.187 | 19.100 | -0.086 |
| comparative_statement | 9.435 | 8.806 | -0.629 |
| compare_change | 12.718 | 13.428 | +0.710 |
| direct_addressing | 14.955 | 16.060 | +1.104 |
| negation | 6.928 | 5.565 | -1.362 |
| spatial_relations_background | 15.331 | 14.945 | -0.386 |
| statement_with_conjunction | 12.589 | 13.022 | +0.433 |
| viewpoint | 9.295 | 9.735 | +0.441 |

## Xác minh

- Đủ 220/220 truy vấn, mỗi chế độ có 50 kết quả mỗi truy vấn.
- snapshot_verified=true, partial=false: dữ liệu được xác minh cuối phiên.
- Toàn bộ 220 thứ tự Top-50 baseline khớp hoàn toàn benchmark lịch sử.
- Không ghi đè kết quả cũ. Không sửa thuật toán hoặc tham số trong phiên chạy.

Dữ liệu chi tiết: outputs/circo_fast_full_v1.json. Chi phí chuẩn bị: outputs/fast_preparation.json.
