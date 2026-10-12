# Rà soát hệ thống ngày 04/10/2026

Phạm vi chính: project `Language-only-Efficient-Training-of-Zero-shot-Composed-Image-Retrieval`, demo local, năm chế độ tìm kiếm, cache, kiểm chứng vùng/quan hệ, lọc nhiều tầng, công cụ đánh giá và script chạy checkpoint. Nhánh huấn luyện gốc được đọc mã nguồn nhưng chưa chạy huấn luyện. Đây là kiểm tra chức năng và các tình huống lỗi, không phải chứng nhận không còn bug hoặc đánh giá độ chính xác trên benchmark.

## Các lỗi và điểm chưa tối ưu đã sửa

| Hạng mục | Trước đợt rà soát | Sau khi sửa |
|---|---|---|
| Lọc nhiều tầng | Chạy thêm phép so sánh CLIP của chế độ cải tiến dù bỏ kết quả | Bỏ bước xếp hạng lại không sử dụng; vẫn giữ đối chiếu LinCIR |
| Bộ nhớ model | Chia sẻ model chỉ khi cả detector và VQA đã nạp; truy vấn chỉ có cảnh có thể gây nạp trùng khi đổi chế độ | Dùng chung riêng từng model, kiểm tra lại lúc chuyển chế độ; cache bằng chứng vẫn riêng |
| Nạp model không cần thiết | Kiểm chứng lần 1 có thể nạp detector/VQA cho yêu cầu chỉ về pixel hoặc cảnh | Đen trắng dùng pixel; cảnh/mô tả tự do chỉ cần VQA; trang phục mới cần detector |
| Phép lựa chọn | Các từ khóa trong câu có “or” có thể thành các điều kiện AND hoặc mâu thuẫn màu | Chuyển nguyên câu sang VQA tự do; so sánh CLIP giữ LinCIR khi chưa có phép OR chuyên biệt |
| Cache chỉ mục | Một số bản ghi sai kiểu, sai digest hoặc vector không chuẩn hóa chưa bị loại | Kiểm tra kiểu, kích thước, giá trị hữu hạn và chuẩn vector; cache lỗi được xây dựng lại |
| Ghi cache/nhật ký | Lỗi dọn file tạm hoặc ghi nhật ký có thể làm mất kết quả tìm hợp lệ | Dọn file không che lỗi gốc; lỗi lưu cache/nhật ký được báo, không làm mất kết quả trong RAM |
| Thêm ảnh | Một file lỗi có thể làm gián đoạn cả lượt thêm; chép trực tiếp có thể để lại file chưa hoàn chỉnh | Kiểm tra đúng nội dung đã đọc; ghi file tạm rồi thay thế; báo thành công một phần; ảnh trùng không buộc lập lại chỉ mục |
| Giao diện | Đổi chế độ có thể còn hiển thị kết quả của chế độ trước; vài tùy chỉnh chưa nói rõ phạm vi | Xóa kết quả cũ khi đổi chế độ, yêu cầu tìm lại; làm rõ ngân sách, số ứng viên và checkbox lọc |
| Chạy GPU | Ma trận vector gallery nằm trên CPU nhưng truy vấn có thể nằm trên CUDA | Ma trận tìm kiếm theo thiết bị đã chọn; bản ghi trên đĩa vẫn CPU |
| VQA | Cấu hình padding của checkpoint có ID vượt vocabulary | Cấu hình dùng để nạp model được sửa theo EOS của tokenizer, bao gồm text_config |
| Tiền xử lý | Script chạy checkpoint chưa xử lý hướng EXIF giống demo; processor có thể cảnh báo thiếu torchvision | Thống nhất EXIF; chọn processor PIL khi phiên bản Transformers hỗ trợ |
| Đầu vào/script checkpoint | Script có thể cắt mô tả dài âm thầm hoặc bỏ ký hiệu $ của người dùng | Báo lỗi mô tả dài/rỗng/nhiều $, giữ đúng một pseudo-token; kiểm tra đường dẫn ảnh |
| LAION | Đọc ảnh lỗi và một số URL phản hồi chưa được xử lý đầy đủ | Báo lỗi ảnh rõ hơn, tái sử dụng vector tham chiếu, kiểm tra vector và URL; xử lý timeout/phản hồi sai |
| Công cụ đánh giá | Chỉ đánh giá bốn phương án, chưa bao gồm cascade; đường dẫn kết quả trùng có thể làm sai Recall | Thêm --cascade, ngân sách/ngưỡng, báo cáo từng tầng; loại đường dẫn trùng và yêu cầu có ảnh đích |
| Báo cáo truy vấn | Có thể giữ thống kê cascade của truy vấn trước khi lượt mới không chạy kiểm chứng | Xóa thống kê cũ ngay khi bắt đầu lượt cascade |

Không sửa trọng số Phi/CLIP, không train lại, không đổi LinCIR thành mô hình sinh ảnh. Các thay đổi tập trung sửa thực thi, giảm công việc thừa và làm bằng chứng/đánh giá rõ hơn.

## Kiểm tra đã hoàn thành

- Kiểm tra cú pháp toàn bộ 20 module Python ở thư mục project; kiểm tra lại sau các bản vá cuối.
- `pip check`: không có xung đột yêu cầu giữa các thư viện đang cài. Điều này không chứng minh các thư viện huấn luyện chưa cài đã có sẵn.
- 12 nhóm kiểm tra tự động đều qua: tách điều kiện/phủ định/phép OR; lọc vector tổng hợp 1.000 ứng viên; tính chỉ số và NaN; không trộn áo/mũ giữa các cá thể; vùng trang phục mơ hồ; mặt nạ trống và màu HSV; cache hỏng/ảnh thay đổi; thêm ảnh lỗi/trùng; chia sẻ model; VQA Yes/No/Unclear và ảnh đen trắng; cấu hình giao diện ở năm chế độ. File kiểm tra tạm đã được xóa; dữ liệu thử nghiệm tạm tự dọn sau khi chạy.
- Chạy model thật trên cùng một truy vấn cảnh `is by the sea` ở cả năm chế độ, đồng thời chạy công cụ đánh giá có `--instances --cascade`. Tất cả luồng chạy được và đưa ảnh bãi biển đã chọn lên đầu. Kết quả ở `outputs/system_audit_comparison.json`. Chỉ có **một truy vấn kiểm tra chức năng**, không dùng để kết luận chất lượng tổng thể, đặc biệt Precision@K không đáng dùng khi danh sách ảnh đúng chưa được gán nhãn đầy đủ.
- Kiểm chứng thực tế câu `wearing a blue shirt without a hat`: lọc nhiều tầng trả ảnh `a26fe9d3-e4ad-46d0-b99b-49bd3431d5fb.png`; lượt đo khoảng 56,45 giây, gồm kiểm chứng mới và nạp detector, dùng lại VQA đã nạp. Không so số này với thời gian sau cache để tuyên bố tăng tốc.
- Hệ số 0 bỏ qua kiểm chứng vùng và xóa thống kê cascade cũ.
- So sánh encoder tùy biến với encoder CLIP chuẩn trên câu không chứa pseudo-token: chênh lệch lớn nhất 0 trong môi trường hiện tại. Đây là kiểm tra tính tương thích attention/causal mask, không chứng minh chất lượng truy vấn ghép.
- Đầu vào thiếu ảnh, text rỗng, Top-K NaN, câu quá dài và nhiều ký hiệu $ đều được chặn.
- Kiểm tra LAION bằng phản hồi giả lập và timeout giả lập; không gửi truy vấn tới dịch vụ ngoài. Không xác nhận LAION online đang hoạt động.
- Nạp VQA với cấu hình padding đã sửa và hỏi ảnh bãi biển: trả bằng chứng “Ủng hộ”. Cảnh báo đọc cấu hình gốc có thể vẫn xuất hiện từ thành phần thư viện; cấu hình model thực thi đã được kiểm tra hợp lệ.
- Khởi động một server Gradio tạm trên cổng riêng, tải ảnh qua HTTP và gọi tìm kiếm “Bản cũ”: nhận đúng sáu đầu ra. Server thử đã đóng; không dừng server người dùng đang mở. Đây là kiểm tra truyền tải/gọi tìm thực tế, không phải kiểm tra trực quan toàn bộ trình duyệt.
- Kiểm tra ma trận chỉ mục theo thiết bị bằng CPU và thiết bị meta giả lập. Máy hiện không có CUDA nên chưa chạy GPU thật.
- Chạy `run_pretrained.py` bằng checkpoint thật: PASS; vector ảnh, pseudo-token và vector ghép đều có dạng dự kiến và giá trị hữu hạn. Ghi kết quả ở `outputs/pretrained_run.json`.

## Những giới hạn còn lại

1. **Độ chính xác model:** CLIP, detector và VQA có thể trả sai. Câu phủ định, phép lựa chọn, hành động, vị trí và mô tả dài vẫn khó. Việc chuyển nguyên câu sang VQA giúp không bỏ qua yêu cầu, không đảm bảo hiểu đúng từng thuộc tính.
2. **Recall của lọc nghiêm ngặt:** CLIP có thể loại ảnh đúng trước VQA; ảnh chưa rõ bị giữ ngoài kết quả; ngân sách có thể bỏ qua ảnh đúng. Ngưỡng hiện chưa hiệu chỉnh bằng tập nhãn độc lập. Khi thiếu ảnh, giảm ngưỡng/tăng ngân sách và đối chiếu bản cũ.
3. **Cùng cá thể:** trang phục có kiểm chứng theo cá thể; cảnh/mô tả tự do vẫn hỏi toàn ảnh. Chưa kiểm chứng hình học chính xác mọi quan hệ hoặc khớp danh tính với ảnh tham chiếu. Tối đa bốn cá thể; vùng đầu/thân là ước lượng, không phải phân đoạn giải phẫu.
4. **Tốc độ:** truy vấn mới trên CPU vẫn có thể mất hàng chục giây do VQA/detector. Cache vector không làm mất chi phí VQA mới; cache kiểm chứng trong RAM mất khi khởi động lại. Chưa đo kho 1.000/10.000 ảnh thật; phép lọc 1.000 vector tổng hợp chỉ kiểm tra logic.
5. **Xếp hạng sau lọc:** các ảnh đạt mọi điều kiện nhận cùng phần thưởng nhị phân, nên thứ tự sau lọc tương đương LinCIR trên tập được giữ. Chưa có bộ xếp hạng thuộc tính liên tục được huấn luyện/hiệu chỉnh.
6. **Nhánh huấn luyện gốc:** môi trường hiện thiếu accelerate, webdataset, torchvision và open_clip; chưa chạy huấn luyện gốc với bộ dữ liệu benchmark/GPU. Demo hiện tại không cần cài các thư viện huấn luyện này để dùng checkpoint có sẵn.
7. **GPU và LAION thật:** bản vá thiết bị được kiểm tra logic/CPU, chưa chạy CUDA; luồng LAION chỉ kiểm tra xử lý đầu vào/phản hồi giả lập, phụ thuộc dịch vụ bên ngoài.
8. **Cam kết ổn định:** chưa thể khẳng định không còn mọi lỗi tiềm ẩn. Những kiểm tra trên có phạm vi cụ thể; cần đánh giá nhiều truy vấn/ảnh gán nhãn độc lập trước khi báo cáo tăng độ chính xác.

Môi trường công cụ hiện không cung cấp công cụ/skill tên “supperpower” hoặc “superpower”; đã kiểm tra danh sách công cụ, không giả định đã gọi được. Chỉ xóa các file kiểm tra tạm do đợt rà soát tạo ra; các file kiểm tra có sẵn của project không bị xóa.

## Sử dụng bản đã vá

### Rà soát bổ sung theo yêu cầu tiếp theo

- Bản vá thiết bị ở lượt đầu chưa đủ: cache truy vấn và vector mô tả vẫn CPU. Đã sửa vector truy vấn trả về theo thiết bị tìm kiếm, chuyển vector mô tả về thiết bị của ma trận ảnh, và tạo chỉ số tầng lọc trên cùng thiết bị. Cache đĩa và cache văn bản vẫn lưu CPU. Trường hợp không có điều kiện cũng trả tensor rỗng đúng thiết bị. Chưa thử CUDA thật.
- Sắp xếp ngân sách kiểm chứng nay chuyển điểm ưu tiên về CPU theo một nhóm thay vì đồng bộ GPU cho từng ảnh. Giữ quy tắc ưu tiên LinCIR hoặc điểm điều kiện yếu nhất; chưa đo mức tăng tốc trên GPU.
- Quan sát chuẩn bị được kiểm tra đối tượng/điều kiện **trước khi đọc cache**. Trước đây cache có thể làm bỏ qua kiểm tra này. Khi ảnh đã đọc lại khác nội dung chuẩn bị, kiểm chứng từ chối dùng hộp/bằng chứng cũ. Quan sát đã giải phóng ảnh khỏi RAM được đọc lại an toàn.
- Dọn ảnh minh họa tạm không còn che mất lỗi ghi ảnh ban đầu nếu cả ghi và dọn cùng lỗi.
- Chín tình huống kiểm tra bổ sung đã qua: cú pháp, thiết bị truy vấn, thiết bị văn bản, lọc vector, quan sát hợp lệ, sai đối tượng khi cache đã có, đọc lại ảnh đã giải phóng, nội dung ảnh thay đổi và lỗi dọn sau lỗi ghi. Dữ liệu thử tạm tự dọn; không tạo file mã kiểm tra lâu dài.
- Chạy lại checkpoint thật ở bản cũ, so sánh CLIP và lọc nhiều tầng; câu cảnh biển giữ đúng ảnh kiểm tra. Tìm lại cùng truy vấn cho kết quả nhất quán; đo lượt lặp khoảng 0,68 giây với cache đã có, không phải thời gian cho truy vấn mới. Ghi kết quả chức năng tại `outputs/review2_smoke.json`.

Các giới hạn về model, ngân sách, benchmark và CUDA thật nêu trên vẫn áp dụng.

Đóng tiến trình demo cũ rồi chạy lại `python demo.py` trong thư mục project. Không cần train lại hay tải lại checkpoint. Thay đổi mã nguồn chỉ có hiệu lực sau khi khởi động lại server; chỉ tải lại trang web chưa đủ.

Để đánh giá so sánh trên nhãn tự chuẩn bị:

```text
python evaluate_semantic.py queries.json --instances --cascade --cascade_budget 20 --gate_threshold -0.02 --output outputs/comparison.json
```

Tách tập chọn ngưỡng/trọng số khỏi tập kiểm tra cuối. Đo truy vấn mới và sau cache riêng; ghi rõ số ảnh chưa kiểm chứng do ngân sách.


## Rà soát sâu bổ sung: thuật toán, huấn luyện và đánh giá

Đợt này đi sâu vào các luồng tìm kiếm đang dùng và mở rộng sang nhánh huấn luyện/đánh giá gốc. Không tuyên bố mọi dòng đã được chứng minh đúng hoặc hệ thống không còn mọi lỗi có thể xảy ra. Lượt kiểm tra cuối không phát hiện lỗi mới trong các tình huống đã thử.

### Bản vá và đối chiếu trước/sau

| Phần | Trước bản vá | Sau bản vá | Lợi ích / giới hạn |
|---|---|---|---|
| Tách thuộc tính | `has a hat`/`with a hat in its paw` có thể thành điều kiện đang đội mũ | Giữ nguyên yêu cầu chưa rõ quan hệ để kiểm tra tự do; không áp tầng lọc mặc/đội sai | Tránh loại ảnh đúng do suy diễn sở hữu = đang mặc; có thể tăng chi phí VQA và vẫn phụ thuộc model |
| Phủ định và phạm vi câu | `not currently wearing`, `no longer on a beach`, `instead of` có thể tạo điều kiện khẳng định sai | Phủ định chưa hiểu, thay thế và điều kiện phức tạp chuyển sang kiểm tra nguyên câu | Không chuyển câu phức tạp thành phép AND sai; không đảm bảo hiểu đúng câu tự do |
| Tính chọn lọc của tầng lọc | Đếm ảnh loại bỏ có thể đồng bộ GPU cho từng cột | Chuyển một nhóm số đếm về CPU mỗi tầng | Giữ nguyên tập ảnh qua phép AND; chưa đo GPU thật |
| Encoder pseudo-token | Cộng vị trí luôn dùng đủ context dù đầu vào ngắn | Cắt vị trí theo độ dài thật, kiểm tra batch/context và giữ gradient qua pseudo-token | CLIP nhỏ thật qua kiểm tra tương đương encoder chuẩn và causal mask ở 9/77 token |
| Tokenizer đánh giá | Phụ thuộc `clip` ở cấp module dù dùng HF | Dùng tokenizer đi cùng model HF; dự phòng `clip` khi caller không cung cấp tokenizer | Không đổi token 259 của LinCIR; cần đúng tokenizer khi caller tự tạo model |
| Loss tương phản | Tính exp trực tiếp có thể tràn và sử dụng thiết bị toàn cục | Tính trong miền log, theo thiết bị tensor; giữ float64 khi cần; đầu vào không hợp lệ bị từ chối | Tương đương công thức cũ trong miền số ổn định; loss này là tiện ích, vòng train Phi hiện dùng MSE |
| CPU và dtype đánh giá | `images.half()` không phù hợp mọi model CPU; Phi có thể nhận sai dtype | Theo dtype/device của encoder và Phi; nhân vector xếp hạng bằng float32 | Vá lỗi thực thi; chưa chạy GPU thật |
| EMA | Thiếu import `copy` khi nạp trạng thái, zip có thể bỏ sót tham số, trạng thái lỗi có thể cập nhật dở | Kiểm tra toàn bộ trạng thái trước khi nạp; kiểm tra số lượng/kích thước; bỏ dọn CUDA cache mỗi update | Nạp sai bị từ chối; EMA huấn luyện lưu float32 |
| Tích lũy gradient | Khai báo tham số nhưng thiếu context tích lũy; sai tên `arg.max_grad_norm` | Context `accelerator.accumulate`, cắt gradient dùng đúng biến | Mô phỏng bằng Torch/CLIP thật qua; chưa chạy Accelerate thật |
| Lịch learning rate | Kéo tổng bước theo tích lũy và số tiến trình | Đếm theo lần cập nhật trọng số, không tự bước ở micro-batch; bỏ qua bước LR khi optimizer bỏ cập nhật | Kiểm tra số lần cập nhật bằng mô phỏng; distributed/GPU chưa thực chạy |
| EMA trong train | Dùng `phi.module` dù chạy một tiến trình | `accelerator.unwrap_model(phi)` | Không yêu cầu model phải được bọc DDP |
| Checkpoint | EMA có thể được ghi đồng thời ở nhiều tiến trình; `phi_best` chưa chắc là trọng số vừa đánh giá | Chỉ tiến trình chính ghi; file tạm rồi thay thế; best lưu đúng model đã đánh giá | Kiểm tra lỗi thay thế file giữ checkpoint cũ và dọn file tạm |
| Vòng train rỗng | Có thể quay vòng không kết thúc | Dừng với thông báo dữ liệu không tạo được batch; kết thúc bình thường bằng `end_training` | Không âm thầm chạy mãi |
| Đồng bộ train | Tiến trình chính đánh giá riêng với model bọc; các tiến trình khác tiếp tục | Đồng bộ quanh đánh giá, dùng model đã unwrap; chờ tải caption trước bước đọc chung | Chỉ kiểm tra mã và mô phỏng; chưa chạy nhiều tiến trình |
| Dữ liệu và TargetPad | Loader luôn gọi giao diện HF trên torchvision transform; mở ảnh có thể giữ file handle; CIRR tạo lại danh sách khóa mỗi ảnh | Hàm tiền xử lý chung hai giao diện, đóng ảnh sau đọc và áp EXIF; danh sách CIRR chuẩn bị một lần | Kiểm tra CIRR classic thật với transform đơn giản; torchvision thật chưa có trong môi trường |
| Batch hỏng | Batch toàn `None` lỗi IndexError khó hiểu | Báo rõ batch không có dữ liệu đọc được; dataset rỗng báo lỗi rõ | Không coi dữ liệu benchmark hỏng là kết quả đánh giá hợp lệ |
| CLI đánh giá/xuất kết quả | Nhánh có biến encoder chưa tạo, sai đối số CIRCO, TargetPad dùng biến model cũ | Khởi tạo encoder HF nhất quán, truyền đúng model, hỗ trợ Phi/Pic2Word/OTI/SEARLE theo nhánh | 50 tổ hợp CLI qua với dịch vụ model/dataset giả lập; chưa chạy benchmark thật |
| Top-K benchmark | `topk(50)` lỗi khi kho dưới 50 ảnh | `topk(min(50, số ảnh))` | Kho thử nhỏ và query float16 qua kiểm tra |
| Tra ảnh tham chiếu | `.index()` quét danh sách cho từng truy vấn | Lập bảng ánh xạ một lần, giữ vị trí xuất hiện đầu tiên | Giảm công việc tra tên lặp lại, không đổi lựa chọn khi có tên trùng |
| LAION | Có thể nhận nhiều nguồn đầu vào và âm thầm bỏ một nguồn | Chỉ nhận một nguồn; kiểm tra vector hữu hạn và timeout/số ảnh | Chỉ thử phản hồi giả lập, không gửi truy vấn ngoài |
| Demo LAION cũ | Không dùng checkpoint người dùng chỉ định; đo FPS dùng sai marker; suy luận có thể tạo đồ thị gradient | Tôn trọng đường dẫn checkpoint, sửa marker FPS, dùng inference mode | Nhánh online cũ chưa chạy thực tế; demo local đang dùng được kiểm chứng riêng |
| Setup model | Ghi manifest trực tiếp; manifest hỏng báo lỗi khó hiểu | Ghi thay thế qua file tạm, từ chối manifest hỏng trước khi tải | Kiểm tra bằng tải giả lập trong thư mục tạm, không tải thêm model |
| Khởi động demo | Chấp nhận cổng không hợp lệ | Chặn cổng ngoài 1–65535 | Người dùng nhận lỗi tham số rõ ràng |

### Kết quả xác minh của đợt này

- **19 nhóm hồi quy qua**. Chi tiết: `outputs/review3_regression.json`. Bao gồm kiểm tra đạo hàm số float64 của loss, gradient thật qua encoder CLIP nhỏ, phủ định/phạm vi, lọc vector đến 1.000 ảnh tổng hợp, EMA, lỗi ghi checkpoint và manifest. Kiểm tra huấn luyện dùng Torch/CLIP thật với Accelerator mô phỏng, không phải một lượt train đầy đủ.
- **50 tổ hợp CLI đánh giá/xuất kết quả** qua: loại model, dataset và hai lựa chọn tiền xử lý. Model tải ngoài, dataset và hàm metric được giả lập để kiểm tra luồng/đối số; không dùng kết quả này để khẳng định chỉ số benchmark.
- **Model thật chạy cả năm chế độ** trên một truy vấn `is on a beach`, với gallery hiện có 14 ảnh. Tất cả đưa ảnh bãi biển `cce93c7d-3842-46b3-b83a-9603e2b38419.png` lên đầu và bản nâng cấp có kết quả. Ghi ở `outputs/review3_real_models.json`. Đây là kiểm tra chức năng một truy vấn, không là đánh giá độ chính xác tổng thể. Thời gian có dùng chung model/cache, không dùng để so tốc độ truy vấn mới.
- Kiểm tra cấu hình sự kiện Gradio và tokenizer bằng model thật; không chạy kiểm thử trực quan toàn bộ trình duyệt trong đợt này.
- Kiểm tra cú pháp **20 module Python** sau bản vá cuối; `pip check` không phát hiện xung đột các thư viện đã cài.
- Không tạo file mã test tồn tại lâu dài. Mã kiểm tra chạy trực tiếp; dữ liệu/ảnh/checkpoint thử dùng thư mục tạm đã dọn. Chỉ giữ nhật ký xác minh JSON; không xóa file test người dùng có sẵn.

### Giới hạn giữ nguyên

Không sửa trọng số LinCIR/CLIP đã train. Chưa chạy train đầy đủ, benchmark CIRR/FashionIQ/CIRCO thật, CUDA hoặc nhiều tiến trình. Môi trường còn thiếu thư viện/dữ liệu của nhánh huấn luyện. VQA/detector có thể sai; câu tự do được kiểm tra toàn ảnh và chưa chứng minh mọi quan hệ cùng cá thể. Lọc CLIP và ngân sách vẫn có thể bỏ ảnh đúng. Câu `has`/`with` ít được lọc cấu trúc hơn nên có thể chậm hơn; với yêu cầu mặc/đội rõ ràng, nên dùng `wearing ...`. Các giới hạn này cần dữ liệu gán nhãn và kiểm chứng thực nghiệm, không thể giải quyết bằng tuyên bố hết bug.

Sau cập nhật, đóng tiến trình demo cũ rồi chạy lại `python demo.py`. Không cần train lại để sử dụng bản demo đã vá.
