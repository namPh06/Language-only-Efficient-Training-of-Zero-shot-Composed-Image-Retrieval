# Kiểm chứng đầy đủ nhánh giữ đặc điểm đối tượng

So sánh với bản hiện tại `focused`; bản mới `balanced` giữ hệ số 0,05 cố định trong suốt kiểm chứng. Không điều chỉnh thuật toán theo kết quả lần chạy này.

## Phạm vi và tính công bằng

- Lượt 1 hoàn tất 220 truy vấn; lượt 2 tự dừng sau 11 truy vấn vì vượt ngân sách tốc độ 15%. Không chạy lượt 3. Toàn bộ kho 123.403 ảnh, bỏ đúng ảnh tham chiếu khi tìm kiếm.
- Cả hai nhánh dùng cùng mô hình, vector kho và điều kiện CPU; thứ tự được đảo giữa truy vấn và lượt chạy.
- 231/231 lần đã thực thi áp dụng bản mới thực sự; không lấy kết quả fallback để tính là cải tiến.
- Thứ hạng của những truy vấn đã chạy khớp giữa các lượt và lần tích hợp trước. Nhánh hiện tại giữ nguyên kết quả.

## Chất lượng

| Chỉ số | Bản hiện tại | Bản mới | Chênh lệch điểm % |
|---|---:|---:|---:|
| mAP@5 | 14.297 | 15.114 | +0.816 |
| mAP@10 | 15.304 | 16.090 | +0.786 |
| mAP@25 | 16.939 | 17.743 | +0.804 |
| mAP@50 | 17.613 | 18.521 | +0.908 |
| Recall@5 | 26.364 | 29.545 | +3.182 |
| Recall@10 | 38.182 | 39.091 | +0.909 |
| Recall@25 | 51.818 | 54.091 | +2.273 |
| Recall@50 | 63.182 | 63.182 | +0.000 |
| GTRecall@10 | 28.892 | 30.003 | +1.111 |
| GTRecall@50 | 51.969 | 53.276 | +1.307 |

Không coi các lần chạy lặp cùng truy vấn là các mẫu chất lượng độc lập. Khoảng tin cậy được bootstrap theo cặp truy vấn, 10.000 lần.

## Tốc độ truy vấn đã chuẩn bị vector tham chiếu

| Lượt | Median hiện tại / mới (s) | P95 hiện tại / mới (s) | Chậm nhất hiện tại / mới (s) | Tỷ lệ median |
|---|---:|---:|---:|---:|
| 1 (220 truy vấn) | 0.3346 / 0.3396 | 0.4216 / 0.4154 | 0.4834 / 0.4676 | 1.015× |
| 2 (11 truy vấn) | 0.3106 / 0.3637 | 0.3745 / 0.3877 | 0.3940 / 0.4001 | 1.171× |

Đây là thời gian tìm kiếm khi vector tham chiếu đã chuẩn bị. Bao gồm chuyển kết quả thành ID benchmark; không phải thời gian đầu tiên khởi động model hoặc mã hóa ảnh mới. P99, trung bình, tổng và chi phí chuẩn bị lưu trong JSON.

## Thống kê trên 180 truy vấn ngoài tập chọn phương án

- AP@5: thay đổi +0.763 điểm %; CI95 [-0.192, +1.855].
- AP@10: thay đổi +0.773 điểm %; CI95 [-0.073, +1.824].
- AP@50: thay đổi +0.953 điểm %; CI95 [+0.114, +1.965].
- Recall@10: thay đổi +1.111 điểm %; CI95 [+0.000, +2.778].
- GTRecall@10: thay đổi +0.862 điểm %; CI95 [-0.013, +1.888].

mAP@10 trên 180 truy vấn chưa có khoảng tin cậy hoàn toàn dương. mAP@50 có bằng chứng cải thiện. 180 truy vấn này đã từng nằm trong tập validation dùng cho phát triển trước đây; chưa phải kiểm chứng độc lập trên test kín.

## Nhóm ngữ nghĩa chính thức

| Nhóm | n | mAP10 hiện tại | mAP10 mới | Chênh lệch |
|---|---:|---:|---:|---:|
| addition | 80 | 14.447 | 14.444 | -0.003 |
| cardinality | 37 | 20.571 | 22.177 | +1.606 |
| comparative_statement | 50 | 10.296 | 11.077 | +0.781 |
| compare_change | 86 | 13.359 | 14.601 | +1.242 |
| direct_addressing | 119 | 15.623 | 16.317 | +0.695 |
| negation | 21 | 8.480 | 8.575 | +0.094 |
| spatial_relations_background | 100 | 15.401 | 16.295 | +0.894 |
| statement_with_conjunction | 164 | 13.018 | 14.153 | +1.135 |
| viewpoint | 54 | 10.787 | 12.573 | +1.786 |

Các nhóm chồng lấn. Có nhóm giảm nhẹ; không kết luận mọi truy vấn đều tốt hơn.

## Nhóm từ khóa thuộc tính (tham khảo)

| Nhóm | n | mAP10 hiện tại | mAP10 mới | Chênh lệch |
|---|---:|---:|---:|---:|
| color | 53 | 14.213 | 15.631 | +1.419 |
| clothing | 10 | 15.336 | 19.717 | +4.381 |
| background | 46 | 10.804 | 12.293 | +1.489 |
| pattern | 3 | 15.159 | 15.050 | -0.109 |

Nhóm này chọn bằng từ khóa caption, không phải nhãn đúng/sai từng thuộc tính ảnh. Chưa đủ mẫu để chứng minh hiểu mọi hoa văn, logo và chi tiết áo.

## Kiểm thử chức năng

- fresh_index_encodes_two_images: PASS.
- unchanged_gallery_skips_encoding: PASS.
- disk_cache_survives_restart: PASS.
- adding_image_encodes_only_new_image: PASS.
- removed_image_disappears_without_reencoding: PASS.
- corrupt_index_rebuilds: PASS.
- corrupt_image_skipped: PASS.
- invalid_inputs_rejected: PASS.
- unsupported_source_rejected: PASS.
- zero_weight_preserves_query: PASS.
- formula_matches_reference: PASS.
- reference_scale_invariant: PASS.
- invalid_weight_rejected: PASS.
- invalid_vectors_rejected: PASS.
- actual_rollback_hash_verified: PASS.
- rollback_protects_later_edits: PASS.
- stable_modules_unchanged: PASS.
- temporary_fixture_removed: PASS.
- missing_reference_and_token_overflow_rejected: PASS.
- empty_gallery_explained: PASS.
- ui_default_preserved_and_new_mode_available: PASS.
- ui_does_not_load_extra_model: PASS.
- ui_new_result_panel_visible: PASS.

Kiểm thử cache dùng encoder giả để đếm chính xác ảnh cần mã hóa; chất lượng encoder thật được kiểm chứng riêng bằng benchmark. Phục hồi được thực thi trong thư mục tạm, không phục hồi đè lên bản đang dùng. Dữ liệu và script kiểm thử tạm đã xóa; giữ log và kết quả làm bằng chứng.

## Kết luận theo điều kiện

Lượt 2 có median bản mới/bản hiện tại vượt 1,15× chỉ trên 11 mẫu. Đây chưa đủ để khẳng định chi phí thuật toán thật tăng 17%, nhưng đủ kích hoạt cơ chế dừng đã cấu hình. Không coi tốc độ đã ổn định hoặc hoàn tất ba lượt.

- Chức năng cache, đầu vào lỗi và khả năng quay lại: đạt trong các ca đã kiểm thử.
- Tốc độ median không vượt ngân sách 15%: False.
- Cải thiện chất lượng tổng thể: nhỏ nhưng có; còn truy vấn/nhóm giảm.
- Bằng chứng chắc chắn mAP10 trên tập giữ lại: chưa đạt.
- Hiểu đầy đủ hoa văn và tổng quát trên dữ liệu mới: chưa đủ bằng chứng.
- Giữ `focused` làm mặc định; `balanced` tiếp tục là nhánh thử nghiệm có thể chọn và quay lại.

Bằng chứng chi tiết: `outputs/balanced_acceptance/acceptance_summary.json` và các file `circo_run_*.json` (lượt 2 là kết quả một phần).
