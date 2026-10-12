# Kết quả tìm kiếm các nâng cấp khả thi — 12/10/2026

## Kết luận

Chưa tìm được cấu hình mới đủ bằng chứng để thay FTI hiện tại. Đã chạy đủ CIRCO validation cho 12 cấu hình mới trong ba đợt. Không cấu hình nào vượt FTI rõ rệt. Không thay đổi demo hoặc thuật toán mặc định; LinCIR gốc, gated, FTI và các demo trước được giữ nguyên.

Ứng viên gần nhất là FTI + mở rộng truy vấn: mAP@10 tăng 0,3155 điểm phần trăm (+1,66% tương đối), mAP@50 tăng 0,3254 điểm phần trăm (+1,50%). Tuy nhiên khoảng tin cậy paired bootstrap 95% cho chênh lệch AP@10 là [-0,5182; +1,0935] điểm phần trăm, còn chứa 0. Vì vậy chưa đủ bằng chứng rằng cải thiện này ổn định hoặc rõ rệt trên demo.

## Điều kiện và cách kiểm tra

- Điều kiện tốc độ của người dùng: chậm hơn LinCIR gốc tối đa 10%, không phải chỉ mất 10% thời gian của bản gốc.
- Không train lại. Có thể dùng checkpoint công khai đã được tác giả huấn luyện.
- CIRCO validation: 220 truy vấn, 123.403 ảnh, trả Top-50, loại ảnh tham chiếu theo ID chính thức. Không loại ảnh khác ID chỉ vì giống pixel.
- Nhãn đúng chỉ dùng tính metric sau truy hồi, không đưa vào thuật toán tìm ảnh.
- Giới hạn cứng 1.200 giây mỗi đợt; có watchdog ngắt tiến trình con. Cả ba đợt đều hoàn tất trong giới hạn.
- Các cấu hình/tham số được ghi trước trong protocol.json. Mã nguồn các bản đang dùng được đối chiếu SHA-256 trước/sau.
- Ngưỡng chọn bảo thủ trong thử nghiệm: cả mAP@10 và mAP@50 tăng ít nhất 10% tương đối so với FTI, paired CI dương và không suy giảm lớn ở nhóm ngữ nghĩa. Đây là ngưỡng thao tác để diễn giải “rõ rệt”, không phải giới hạn tốc độ 10% người dùng yêu cầu.
- Nếu vượt điều kiện chất lượng mới kiểm tra độc lập tốc độ tìm kiếm thực tế: khi chưa có cache và khi có cache, trung vị và P95 so với baseline. Không cấu hình mới nào qua điều kiện chất lượng, nên không có bản mới được công nhận đạt toàn bộ điều kiện.

## Điểm benchmark đo được

Điểm là phần trăm. Điểm baseline và FTI trong bảng được đo lại ở đợt này; gated lấy từ mốc đầy đủ trước. Mọi phép so sánh chất lượng mới đều dùng cùng 220 truy vấn và toàn bộ gallery.

| Cấu hình | mAP@10 | mAP@50 | Quyết định |
|---|---:|---:|---|
| LinCIR gốc | 14.0374 | 16.2586 | Giữ làm đối chứng |
| FTI hiện tại | 18.9948 | 21.7146 | Giữ bản đang dùng |
| SEARLE-XL | 13.3001 | 15.7768 | Không chọn: điểm giảm |
| SEARLE + gated | 14.6553 | 17.0303 | Không chọn: điểm giảm |
| FTI: truy vấn rút gọn | 15.9752 | 18.4413 | Không chọn: điểm giảm |
| FTI: chỉ token chủ thể | 6.3005 | 7.6557 | Không chọn: điểm giảm |
| FTI + PDV-T (0,8) | 17.8348 | 20.3227 | Không chọn: điểm giảm |
| FTI + PDV-T (1,2) | 16.3196 | 18.6630 | Không chọn: điểm giảm |
| FTI + PDV-T (1,4) | 10.5017 | 12.7884 | Không chọn: điểm giảm |
| FTI + PDV-F | 16.5359 | 18.8695 | Không chọn: điểm giảm |
| FTI: trừ trung bình vector | 9.5126 | 11.4623 | Không chọn: điểm giảm |
| FTI + mở rộng truy vấn | 19.3103 | 22.0401 | Tăng nhỏ, chưa đủ bằng chứng |
| BASIC thích nghi + FTI | 8.3453 | 10.2072 | Không chọn: điểm giảm |
| BASIC thích nghi + text trực tiếp | 13.6294 | 15.4037 | Không chọn: điểm giảm |
| gated (mốc trước) | 16.6649 | 19.0203 | Giữ bản đang dùng |

FTI hiện tại cao hơn baseline khoảng 35,32% tương đối ở mAP@10 và 33,56% ở mAP@50. Đây là kết quả trung bình trên validation này; không có nghĩa mọi truy vấn đều tốt hơn.

FTI + mở rộng truy vấn có 54 truy vấn AP@10 cao hơn FTI, 34 thấp hơn và 132 bằng nhau. Cấu hình dùng Top-10 không nhãn để tạo vector phản hồi và trộn 10% vào vector truy vấn. Không chọn cấu hình này làm mặc định vì lợi ích trung bình nhỏ và CI còn chứa 0.

## Thời gian và giới hạn phép đo

| Đợt | Cấu hình mới | Hoàn tất | Thời gian worker |
|---|---:|---:|---:|
| SEARLE và biến thể FTI | 4 | 220/220 | 14 phút 5.5 giây |
| PDV thích nghi với FTI | 4 | 220/220 | 14 phút 31.4 giây |
| Phép chiếu, centering và query expansion | 4 | 220/220 | 3 phút 31.8 giây |

Thời gian worker bao gồm khởi tạo, xử lý dữ liệu riêng của thử nghiệm và kiểm tra snapshot. Đây không phải độ trễ một lần tìm ảnh trong demo.

Ở hai đợt đầu, vector ảnh tham chiếu được chuẩn bị chung; ở đợt cuối, vector truy vấn được lưu từ đợt PDV và chỉ đo phần xếp hạng. Baseline ở đợt đầu còn đọc lại ảnh trong lời gọi search. Vì vậy không dùng các median nội bộ này để kết luận bản mới nhanh hơn baseline hoặc đạt giới hạn +10%. Các phần tính trước được ghi riêng trong JSON. Việc không kiểm tra tiếp tốc độ end-to-end của cấu hình đã không đạt chất lượng là quyết định dừng thử, không phải kết luận chúng đã đạt tốc độ.

## Độ trung thực với thuật toán gốc

- SEARLE-XL: checkpoint ViT-L/14 chính thức; Phi nhận vector ảnh thô; thay pseudo-token đầu tiên vào prompt của tác giả. Đây là SEARLE, không phải iSEARLE.
- Tiền xử lý giữ CLIP center crop 224 đang dùng. Không nhận là tái hiện đúng targetpad của các bài báo.
- PDV: lấy hiệu vector FTI có/không có text thay đổi, thử alpha 0,8/1,2/1,4 và fusion beta=0,85, alphaI=1,4, alphaT=1,2. Vector không có text dùng prompt FTI rỗng còn từ “but”. Đây là thích nghi PDV với FTI, không phải tái hiện PDV-SEARLE trong bài báo.
- BASIC thích nghi: dùng corpus đối tượng/phong cách công khai, contrastive PCA 250 thành phần dương, trọng số corpus âm 0,2, mở rộng ảnh tham chiếu Top-25, Harris 0,1. Dùng trung bình gallery thay LAION mean; không dùng synthetic score calibration hoặc contextualization text với 100 corpus words. Không nhận là tái hiện đầy đủ BASIC.
- Các kết quả giảm điểm không chứng minh thuật toán gốc trong bài báo kém. Chúng chỉ loại cấu hình đã thực sự chạy trong hệ thống/môi trường này.

## Các hướng khác và lý do chưa chọn

Không đánh đồng “chưa thử được” với “đã benchmark và thất bại”.

| Hướng | Trạng thái trên môi trường hiện tại |
|---|---|
| MagicLens | Có checkpoint công khai, nhưng cần môi trường JAX/Flax/Scenic và tạo lại gallery vector bằng encoder tương ứng. Chưa benchmark CPU tại đây. |
| LamRA | Setup chính thức dùng Qwen2-VL-7B và flash-attn; môi trường CPU hiện tại chưa có pipeline/weights tương ứng. Chưa đo độ trễ. |
| WISER | Cấu hình CIRCO dùng BAGEL-7B-MoT, Qwen2.5-VL-7B, caption gallery và ảnh đã chỉnh sửa, có lựa chọn GPT-4o. Chưa sẵn sàng để thử dưới ngân sách này. |
| SoFT | Cần MLLM trích ràng buộc. Bản parser điều kiện cũ không phải toàn bộ SoFT. Chưa thử nguyên bản. |
| RTD, ConText-CIR | Chưa tìm được checkpoint dùng ngay trong các nguồn chính thức đã kiểm tra. Không kết luận checkpoint không tồn tại ở mọi nơi. |
| AdaST | Tìm thấy bài viết, nhưng PDF nguồn bị bước xác minh truy cập và chưa tìm được repo chạy được trong lần tìm này. Chưa đủ thông tin để tái hiện. |

Với những nhánh nhẹ, có thể triển khai ngay và đã kiểm tra, chưa có ứng viên mới đáng thay bản hiện tại. Tạm dừng vòng mở rộng này. Đây là kết luận có giới hạn về các nguồn/nhánh đã rà soát và máy hiện tại, không phải bằng chứng rằng thế giới không có thuật toán CIR tốt hơn.

## Tính nhất quán và dữ liệu bằng chứng

- Ba đợt đều exit code 0, snapshot_verified=true, đủ 220 truy vấn.
- Top-50 của FTI giống hệt nhau ở cả ba đợt. Baseline và FTI ở đợt đầu cũng giống hệt cả 220 danh sách Top-50 của mốc trước.
- Các file demo.py, demo_fti.py, fti_retrieval.py, benchmark_circo.py, upgraded_retrieval.py, retrieval_utils.py, models.py, encode_with_pseudo_tokens.py giữ nguyên SHA-256.
- Benchmark validation đã được dùng trong nhiều vòng lựa chọn. Bootstrap ở đây là mô tả trên cùng tập này, không phải xác nhận trên một tập test độc lập; không nhận điểm này là CIRCO hidden-test hay điểm bài báo.
- Giữ benchmark.json, protocol.json, exit.json, decision.json, log, catalog nguồn và final_verification.json. Xóa file script test tạm sau khi hoàn tất.

Các thư mục bằng chứng:

- outputs/feasible_trials_20261012/
- outputs/pdv_trials_20261012/
- outputs/basic_trials_20261012/

## Nguồn chính thức

- [SEARLE](https://github.com/miccunifi/SEARLE)
- [PDV — mã và công thức](https://github.com/neouyghur/PDV); [bài báo](https://arxiv.org/html/2502.07215v3)
- [BASIC / i-CIR](https://github.com/billpsomas/icir)
- [MagicLens](https://github.com/google-deepmind/magiclens)
- [LamRA](https://github.com/Code-kunkun/LamRA)
- [WISER — cấu hình CIRCO](https://github.com/Physicsmile/WISER/blob/main/config/start_config_circo.json)
- [SoFT](https://arxiv.org/abs/2512.20781)
- [RTD](https://github.com/jaeseokbyun/RTD); [ConText-CIR](https://github.com/mvrl/ConText-CIR)
- [AdaST — nguồn tìm được](https://openreview.net/pdf?id=CQ2n2H5x6c)

Đã dọn checkpoint SEARLE chỉ phục vụ thử nghiệm và cache vector trung gian của hai đợt mới; giữ metadata nguồn/checksum và toàn bộ kết quả. Không xóa gallery ảnh, cache vector CIRCO của hệ thống, hoặc checkpoint FTI/LinCIR đang dùng.
