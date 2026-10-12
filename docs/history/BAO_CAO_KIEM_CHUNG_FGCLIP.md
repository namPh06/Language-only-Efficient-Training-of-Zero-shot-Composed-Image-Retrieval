# Kiểm chứng FG-CLIP so với bản hiện tại

Chưa đáp ứng đầy đủ tiêu chí để thay bản hiện tại; giữ focused mặc định.

Lượt đánh giá: 3; đủ 220 truy vấn mọi lượt: True; thứ hạng lặp lại: True; bản hiện tại giữ nguyên thứ hạng: True.

| Chỉ số (%) | Hiện tại focused | FG-CLIP | Chênh lệch (điểm %) | Khoảng tin cậy 95% |
|---|---:|---:|---:|---|
| mAP@5 | 14.2975 | 14.2975 | +0.0000 | [0.0, 0.0] |
| mAP@10 | 15.3040 | 15.3040 | +0.0000 | [0.0, 0.0] |
| mAP@50 | 17.6129 | 17.6129 | +0.0000 | [0.0, 0.0] |
| Recall@10 | 38.1818 | 38.1818 | +0.0000 | [0.0, 0.0] |
| GTRecall@10 | 28.8918 | 28.8918 | +0.0000 | [0.0, 0.0] |

| Lượt | Trung vị focused (s) | FG (s) | Tỷ lệ | P95 focused (s) | FG (s) | FG thực sự áp dụng |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.3793 | 0.3733 | 0.984 | 0.4430 | 0.4412 | 0/220 |
| 2 | 0.3702 | 0.3681 | 0.994 | 0.4473 | 0.4446 | 0/220 |
| 3 | 0.3559 | 0.3544 | 0.996 | 0.4347 | 0.4389 | 0/220 |

## So sánh từng nhóm

| Nhóm | Số truy vấn | Delta mAP@10 (điểm %) | Khoảng tin cậy 95% |
|---|---:|---:|---|
| all | 220 | +0.0000 | [0.0, 0.0] |
| held_out_after_first_10 | 210 | +0.0000 | [0.0, 0.0] |
| official:addition | 80 | +0.0000 | [0.0, 0.0] |
| official:cardinality | 37 | +0.0000 | [0.0, 0.0] |
| official:comparative_statement | 50 | +0.0000 | [0.0, 0.0] |
| official:compare_change | 86 | +0.0000 | [0.0, 0.0] |
| official:direct_addressing | 119 | +0.0000 | [0.0, 0.0] |
| official:negation | 21 | +0.0000 | [0.0, 0.0] |
| official:spatial_relations_background | 100 | +0.0000 | [0.0, 0.0] |
| official:statement_with_conjunction | 164 | +0.0000 | [0.0, 0.0] |
| official:viewpoint | 54 | +0.0000 | [0.0, 0.0] |
| caption_keyword:color | 53 | +0.0000 | [0.0, 0.0] |
| caption_keyword:clothing | 10 | +0.0000 | [0.0, 0.0] |
| caption_keyword:background | 46 | +0.0000 | [0.0, 0.0] |
| caption_keyword:pattern | 3 | +0.0000 | [0.0, 0.0] |

## Giới hạn

- Validation đã được dùng trong các lần phát triển trước; 210 truy vấn sau 10 truy vấn đầu chỉ là kiểm tra bổ sung, không phải test set độc lập.
- Khoảng tin cậy bootstrap theo truy vấn; nhóm nhỏ và nhiều phép so sánh không đủ kết luận chắc chắn.
- Nhóm màu/trang phục/nền/hoa văn lấy từ từ khóa câu truy vấn, không phải nhãn thuộc tính được kiểm chứng.
- Không chứng minh hiểu mọi hoa văn, thuộc tính hay tổng quát ngoài CIRCO.
- Đo trên CPU với vector ảnh tham chiếu chuẩn bị chung và cache gallery; không bao gồm khởi động hoặc mã hóa ảnh mới.

Không đổi thuật toán, trọng số hoặc chế độ mặc định trong quá trình kiểm chứng. Không tự động công nhận nâng cấp chỉ vì điểm trung bình tăng.
Dữ liệu và số liệu chi tiết: outputs/detail_verification/summary.json.
