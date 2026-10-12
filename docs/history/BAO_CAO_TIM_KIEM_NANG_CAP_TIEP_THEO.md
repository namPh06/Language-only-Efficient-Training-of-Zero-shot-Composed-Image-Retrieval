# Báo cáo tìm kiếm và kiểm chứng nâng cấp tiếp theo

Ngày: 11/10/2026. Project thực tế nằm trên ổ D.

## 1. Kết luận và trạng thái triển khai

Đã sàng lọc **136 cấu hình trong 11 đợt**, chưa kể hai biến thể định tuyến thăm dò. Không có cấu hình nào vượt qua toàn bộ tiêu chí chất lượng nghiêm ngặt. Không tuyên bố đã tìm được bản vượt trội hoàn toàn.

Hai thay đổi đã được cung cấp:

- **Mặc định:** tối ưu mã hóa phần văn bản bằng tiền tố đến EOT. Ba lượt đo sạch cho mức giảm thời gian khoảng 48–50%; toàn bộ Top-50 của 220 truy vấn giữ nguyên. Một lượt kiểm tra riêng sau tích hợp cũng giữ nguyên toàn bộ thứ hạng.
- **Tùy chọn:** `Thử nghiệm — kết hợp điểm có giới hạn`, slug benchmark `gated`. mAP@10 tăng tương đối **8.89%** trên toàn CIRCO validation; điểm mAP@10 trung bình tăng ở cả 9 nhóm chính thức. Ba lượt đo đầy đủ cho thời gian trung vị tăng khoảng 2–7% so với bản mặc định đã tối ưu, đạt giới hạn tốc độ đã đặt ra.

Chế độ `Tìm nhanh — truy vấn thích ứng` vẫn là mặc định. Chế độ mới có nhãn thử nghiệm vì bằng chứng thống kê chưa đạt yêu cầu, chưa được kiểm chứng trên dữ liệu độc lập và không bảo đảm mọi truy vấn riêng lẻ đều tốt hơn.

## 2. Phạm vi và giao thức

Bản đối chiếu là **bản ổn định focused đang có trước lượt nâng cấp này**, không phải số liệu nguyên văn trong bài báo LinCIR. Các số dưới đây là đo thực tế trên máy hiện tại, CIRCO validation: 123.403 ảnh, 220 truy vấn, Top-50; CPU, một luồng tính toán, FP32. Checkpoint CLIP và Phi giữ nguyên, không huấn luyện thêm, không mã hóa lại gallery.

Mỗi đợt cố định tập cấu hình rồi chọn bằng 40 truy vấn đầu, với điều kiện mAP@5, mAP@50 và Recall@10 trên tập này không thấp hơn bản ổn định. Chỉ ứng viên được chọn mới được kiểm tra trên 180 truy vấn còn lại. Hai biến thể định tuyến thăm dò được ghi riêng, không coi là kiểm chứng độc lập.

Tiêu chí nghiêm ngặt đã đặt: mAP@10 trên 180 truy vấn tăng ít nhất 10% tương đối; khoảng tin cậy ghép cặp 95% của mức tăng phải nằm trên 0; các mAP/Recall chính và mAP@10 của các nhóm chính thức không giảm. Tốc độ trung vị không quá 1,15 lần và P95 không quá 1,25 lần bản đối chiếu, qua ba lượt đầy đủ.

**CIRCO validation đã được dùng nhiều lần trong phát triển.** 180 truy vấn là phần ngoài tập chọn của từng đợt, không phải một tập kiểm thử mới chưa từng xem. Khoảng tin cậy bootstrap 10.000 mẫu ghép cặp có tính thăm dò, chưa hiệu chỉnh cho toàn bộ các lần lựa chọn. Ground truth và `semantic_aspects` chỉ được dùng để tính chỉ số, không truyền vào thuật toán tìm kiếm hoặc định tuyến câu nhập.

## 3. Các hướng đã thử

| Đợt | Hướng thử | Cấu hình | mAP@10 toàn 220 | mAP@50 toàn 220 | Kết luận |
|---|---|---:|---:|---:|---|
| 2 | Mở rộng truy vấn/ảnh tham chiếu | 21 | 16.0582 | 18.6534 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 3 | Kết hợp các cách diễn đạt | 15 | 16.5441 | 19.1082 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 4 | PCA/chuẩn hóa phổ vector | 8 | 15.3166 | 17.7280 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 5 | Trọng số ảnh gốc thích ứng | 12 | 15.9293 | 18.4471 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 6 | Kết hợp điểm phi tuyến | 22 | 17.7761 | 20.4476 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 7 | Harris + xử lý phủ định | 9 | — | — | Không qua vòng phát triển 40 truy vấn |
| 8 | Cổng điểm + xử lý phủ định | 12 | 16.6649 | 19.0203 | Chưa qua tiêu chí chất lượng nghiêm ngặt |
| 9 | Prompt/pseudo-token một lần mã hóa | 8 | — | — | Không qua vòng phát triển 40 truy vấn |
| 10 | Hiệu chỉnh mật độ gallery | 11 | — | — | Không qua vòng phát triển 40 truy vấn |
| 11 | Caption thuần + ảnh tham chiếu | 9 | — | — | Không qua vòng phát triển 40 truy vấn |
| 12 | Trộn Harris và cổng điểm | 9 | 16.5418 | 18.9555 | Chưa qua tiêu chí chất lượng nghiêm ngặt |

Đợt 6 có điểm trung bình cao hơn nhưng nhóm phủ định giảm và cần hai cách diễn đạt ở ứng viên được chọn. Đợt 8 được chọn để cung cấp thử nghiệm vì cân bằng giữa chất lượng các nhóm và tốc độ. Không chọn cấu hình bằng đáp án của từng truy vấn; không coi số điểm tốt nhất sau nhiều lần thử là bằng chứng tổng quát hóa.

## 4. Tối ưu mã hóa văn bản giữ nguyên nguyên lý

Trước đây CLIP xử lý đủ 77 vị trí, gồm phần đệm sau token kết thúc EOT. Vector truy vấn được lấy tại EOT; mặt nạ nhân quả ngăn vị trí này nhìn các vị trí phía sau. Nay chỉ xử lý đến EOT cuối cùng cần thiết trong batch, giữ nguyên nội dung trước EOT, vị trí token, pseudo-token, trọng số và FP32.

Sai khác vector lớn nhất đã đo trên 220 truy vấn: **3,8743 × 10⁻⁷**. Đây là sai khác làm tròn FP32 nhỏ, không phải vector đồng nhất tuyệt đối. Toàn bộ thứ hạng Top-50 đã kiểm tra giữ nguyên. Câu gần đủ 77 token có thể hưởng ít lợi ích tốc độ hơn.

Ba lượt đo sạch (lượt 1, 2, 4):

| Lượt | Cách cũ, giây | Tiền tố EOT, giây |
|---|---:|---:|
| 1 | 0.329702 | 0.170621 |
| 2 | 0.328016 | 0.162752 |
| 4 | 0.339540 | 0.169854 |

Lượt 3 được giữ để kiểm tra thứ hạng nhưng loại khỏi bằng chứng tốc độ vì có một phép tính vector chạy đồng thời. Lượt 4 được đo lại riêng để thay thế. Sau tích hợp, lượt kiểm tra trực tiếp đạt 0,331857 giây so với 0,167109 giây.

Cache truy vấn vẫn được giữ, khóa cache phân biệt cách cũ và cách tối ưu. Vector gallery và cache tham chiếu tiếp tục tái sử dụng.

## 5. Nguyên lý chế độ gated

Gọi `gᵢ` là vector ảnh gallery, `q` là vector LinCIR focused và `v` là vector ảnh tham chiếu đã chuẩn hóa. `sᵢ = gᵢ·q`, `rᵢ = gᵢ·v`. `t` là điểm thứ 50 của vector điểm ban đầu trên gallery, trước bước loại ảnh tham chiếu; gallery nhỏ dùng số ảnh hiện có.

Nếu câu có dấu hiệu phủ định/loại bỏ thuộc tính theo quy tắc cố định trên văn bản nhập:

```text
Sᵢ = gᵢ · (q + 0,1v)
```

Với các câu còn lại:

```text
wᵢ = sigmoid((sᵢ − t) / 0,01)
Sᵢ = sᵢ + 0,4wᵢrᵢ
```

Ảnh vốn gần truy vấn được bổ sung thông tin giữ đặc điểm ảnh tham chiếu mạnh hơn. Ảnh xa truy vấn nhận ít bổ sung. Các từ phủ định được nhận bằng quy tắc; không dùng nhãn nhóm phủ định của benchmark. Quy tắc có thể bỏ sót câu hoặc hiểu sai ý định.

### Giới hạn điểm để giảm chi phí

Vẫn tính `sᵢ` cho **toàn bộ gallery** như bản gốc. Để tránh tính `rᵢ` cho mọi ảnh, dùng bất đẳng thức Cauchy–Schwarz:

```text
rᵢ ≤ max_norm_gallery × ||v||
Uᵢ = sᵢ + 0,4wᵢ × max_norm_gallery × ||v||
```

Chấm chính xác một nhóm ban đầu để có cận dưới `L` cho điểm Top-K. Nếu `Uᵢ < L`, ảnh đó chắc chắn không thể lọt Top-K theo chính công thức này; có thể bỏ phép tính tham chiếu của nó. Thêm biên nhỏ 10⁻⁵ để xử lý làm tròn FP32 một cách thận trọng.

Trung bình chỉ **88.30 ứng viên** cần chấm bổ sung trong các truy vấn không phủ định trên CIRCO, thay vì 123.403. Đây là lọc bằng giới hạn điểm số, không phải loại ảnh bằng phán đoán “có mèo/có áo”. Mọi Top-50 của bước lọc đã khớp cách chấm toàn kho trong thử nghiệm; không khẳng định con số 88 áp dụng cho mọi gallery/câu nhập.

Nhánh phủ định trộn vector trước nên vẫn chỉ cần một phép chấm toàn kho. Nhánh mới không chạy detector/VQA trên từng ảnh và không tải thêm mô hình.

## 6. Chất lượng bản đã tích hợp

Đơn vị điểm là %, chênh lệch là điểm phần trăm.

| Chỉ số | Focused ổn định | Gated | Chênh lệch |
|---|---:|---:|---:|
| mAP@5 | 14.2975 | 15.6292 | +1.3317 |
| mAP@10 | 15.3040 | 16.6649 | +1.3609 |
| mAP@25 | 16.9389 | 18.2758 | +1.3369 |
| mAP@50 | 17.6129 | 19.0203 | +1.4074 |
| Recall@5 | 26.3636 | 31.8182 | +5.4545 |
| Recall@10 | 38.1818 | 40.4545 | +2.2727 |
| Recall@25 | 51.8182 | 53.1818 | +1.3636 |
| Recall@50 | 63.1818 | 63.1818 | +0.0000 |
| GTRecall@10 | 28.8918 | 30.4277 | +1.5359 |
| GTRecall@50 | 51.9694 | 52.3860 | +0.4165 |

`Recall@K` đo việc ảnh đích chính có nằm trong K kết quả hay không. `GTRecall@K` đo tỷ lệ các ảnh liên quan đã gán nhãn được tìm thấy. mAP tính độ chính xác thứ hạng theo nhiều ảnh liên quan; mẫu số AP@K dùng `min(K, số ảnh ground truth)`.

### mAP@10 theo nhóm chính thức

| Nhóm | Focused | Gated | Chênh lệch |
|---|---:|---:|---:|
| Thêm thuộc tính | 14.4469 | 15.7197 | +1.2728 |
| Số lượng | 20.5709 | 21.8707 | +1.2998 |
| Phát biểu so sánh | 10.2956 | 10.6069 | +0.3114 |
| Thay đổi khi so sánh | 13.3588 | 15.2486 | +1.8898 |
| Chỉ định trực tiếp | 15.6226 | 16.4708 | +0.8482 |
| Phủ định | 8.4805 | 8.9335 | +0.4530 |
| Quan hệ không gian/bối cảnh | 15.4008 | 16.9743 | +1.5736 |
| Câu kết hợp điều kiện | 13.0179 | 14.2074 | +1.1896 |
| Góc nhìn | 10.7870 | 11.7658 | +0.9788 |

Các nhóm có thể giao nhau. Tăng điểm trung bình của nhóm không có nghĩa mọi truy vấn trong nhóm đều tốt hơn hoặc hệ thống đã hiểu đầy đủ thuộc tính đó.

## 7. Tốc độ so với bản gốc đã tối ưu

Cùng gallery, cùng cache tham chiếu chuẩn bị trước, đổi thứ tự chạy các chế độ để giảm lợi thế của thứ tự. Thời gian bao gồm tìm kiếm, bước giới hạn điểm, chấm bổ sung và chuyển 50 đường dẫn thành ID benchmark. Không bao gồm tải mô hình, tạo vector lần đầu hay mã hóa ảnh tham chiếu chưa có cache.

| Lượt đầy đủ | Focused median, giây | Gated median, giây | Tăng median | Focused P95, giây | Gated P95, giây |
|---|---:|---:|---:|---:|---:|
| 1 | 0.168304 | 0.180146 | +7.04% | 0.235690 | 0.252911 |
| 2 | 0.156664 | 0.159646 | +1.90% | 0.253910 | 0.252089 |
| 3 | 0.112040 | 0.117094 | +4.51% | 0.125640 | 0.133037 |

Lượt qua đường benchmark đã tích hợp: focused **0.112249 giây**, gated **0.118613 giây**; tăng **5.67%**. Gallery snapshot được xác nhận, đủ 220 truy vấn và thứ hạng khớp công thức.

Thời gian tuyệt đối thay đổi giữa các lượt do trạng thái CPU/hệ thống; dùng tỷ lệ ghép cặp trong cùng lượt để đánh giá. Không suy ra cùng mức thời gian cho GPU, máy khác, mô tả dài hoặc ảnh tham chiếu mới.

## 8. Vì sao chưa được gọi là vượt trội hoàn toàn

Trên 180 truy vấn ngoài tập chọn của đợt 8, mAP@10 tăng **0.9626 điểm phần trăm**, khoảng tin cậy 95% **[-0.6256; 2.5393]**. Khoảng này còn chứa 0; mức tăng tương đối trên phần này cũng chưa đạt ngưỡng 10%. Do đó tiêu chí nghiêm ngặt chưa qua dù số trung bình toàn 220 đẹp hơn.

Các giới hạn còn lại:

- Recall@50 toàn bộ giữ nguyên, không tăng.
- Một số truy vấn riêng lẻ có thể xấu hơn; 9 nhóm tăng trung bình không đồng nghĩa từng truy vấn tăng.
- Dữ liệu validation đã dùng nhiều lần nên chưa có bằng chứng độc lập về tổng quát hóa.
- CLIP vẫn dùng đặc trưng toàn ảnh; chưa chứng minh đọc được mọi hoa văn, thuộc tính nhỏ, quan hệ hay phủ định phức tạp.
- Bộ quy tắc phủ định chưa hiểu mọi cách diễn đạt hoặc ngôn ngữ.
- Tốc độ đã đo trên CPU một luồng và cache chuẩn bị trước; lần khởi động/ảnh mới vẫn có chi phí.

Không tiếp tục lựa chọn theo đáp án từng truy vấn để ép điểm tăng. Muốn kết luận mạnh hơn cần kiểm chứng độc lập bằng benchmark/tập dữ liệu chưa dùng phát triển hoặc kết quả test chính thức, với cấu hình cố định trước khi xem đáp án.

## 9. Sử dụng và quay lại

Khởi động lại demo bằng môi trường project:

```powershell
..\.venv\Scripts\python.exe -B -X utf8 demo.py
```

Chọn `Thử nghiệm — kết hợp điểm có giới hạn` để dùng nhánh mới. Chọn `Tìm nhanh — truy vấn thích ứng` để dùng bản ổn định đã tăng tốc. Không cần train lại hoặc tạo lại 123.403 vector.

Đánh giá lại qua công cụ chính thức của project:

```powershell
..\.venv\Scripts\python.exe -B -X utf8 benchmark_circo.py --modes focused gated --batch-size 1 --cpu-threads 1 --independent-latency --prepared-reference-latency --latency-reference focused --max-latency-ratio 1.15 --output outputs\circo_gated_new_run.json
```

Dùng tên output mới để tránh ghép kết quả cũ. `ROLLBACK_GATED.cmd` bỏ tích hợp gated, giữ phần tăng tốc. Nếu muốn quay về cả cách mã hóa cũ, thực hiện hoàn tác gated trước rồi `ROLLBACK_COMPACT.cmd`. Chuỗi này đã được kiểm tra trên bản sao tạm. Công cụ từ chối ghi đè nếu có chỉnh sửa mới phát sinh sau nâng cấp. Ảnh, checkpoint và vector lưu sẵn không bị xóa.

Có thể tạm dùng đường mã hóa đủ 77 vị trí với biến môi trường `LINCIR_FULL_TEXT_CONTEXT=1`; tắt biến này để trở lại tối ưu. Nếu đã có cache truy vấn, hai đường dùng khóa riêng.

## 10. Bằng chứng và kiểm tra chức năng

- `outputs/compact_acceptance/run_1.json`, `run_2.json`, `run_4.json`: ba lượt đo sạch của tối ưu văn bản.
- `outputs/compact_production/summary.json`: kiểm tra bản tích hợp, cache và hoàn tác.
- `outputs/search_round2` đến `outputs/search_round12`: giao thức, sàng lọc và kết quả các hướng thử.
- `outputs/gated_acceptance/summary.json`, ba file `run_*.json`: ba lượt đầy đủ; kết quả mỗi truy vấn đều khớp công thức.
- `outputs/gated_production/circo.json`: lượt đầy đủ qua API đã tích hợp, snapshot đúng.
- `outputs/gated_production/functional_checks.json`: 14 kiểm tra đều đạt, gồm Top-50, giao diện, chế độ mặc định, đăng ký benchmark, hoàn tác và bảo vệ chỉnh sửa mới.

Các thư mục kiểm thử tạm đã tự xóa. Ba script kiểm chứng tạm cũng đã xóa sau khi dùng; giữ kết quả đo, công cụ benchmark chính, các công cụ nghiên cứu có thể tái sử dụng và mã thực hiện nâng cấp.

Một phép thử điểm phi tuyến ban đầu bị kiểm tra toàn vẹn từ chối vì mã demo được tích hợp trong lúc nó chạy; phép thử đã chạy lại với mã cố định. Lỗi nhận tuple từ hàm tạo prompt trong công cụ nghiên cứu được sửa rồi chạy lại. Không dùng các lượt lỗi làm bằng chứng đạt tiêu chí.

## 11. Tham khảo phương pháp

Một số hướng mở rộng truy vấn, phép biến đổi gallery và kết hợp điểm phi tuyến tham khảo [mã nguồn BASIC chính thức](https://github.com/billpsomas/icir), đặc biệt [utils_retrieval.py](https://raw.githubusercontent.com/billpsomas/icir/main/utils_retrieval.py). Các nhánh đã thử là thành phần/biến thể riêng, **không phải tái hiện đầy đủ BASIC**. Bộ mã hóa và checkpoint nền vẫn của project LinCIR hiện tại.
