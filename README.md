# Tìm kiếm ảnh từ ảnh tham chiếu và mô tả — LinCIR, gated, FTI

Project của nhóm môn Xử lý ảnh: đưa vào **ảnh tham chiếu + mô tả thay đổi bằng tiếng Anh**, tìm ảnh phù hợp đã có trong kho. Hệ thống không sinh hoặc chỉnh sửa ảnh. Có ba phiên bản: LinCIR gốc, gated (truy vấn thích ứng và kết hợp điểm có giới hạn), FTI (token chủ thể và thuộc tính từ checkpoint FTI4CIR).

## 1. Cài đặt sau khi clone/pull

Các lệnh dưới đây chạy trong thư mục chứa README. Thay `<URL_REPO_NHOM>` bằng URL GitHub của nhóm.

```powershell
git clone <URL_REPO_NHOM>
cd <TEN_THU_MUC_REPO>
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe setup_models.py
.\.venv\Scripts\python.exe setup_models.py --check
```

Môi trường đã kiểm chứng trên máy phát triển: Windows, Python 3.14, CPU; phiên bản thư viện được cố định trong requirements.txt. Không cần GPU hoặc train lại. Các nền tảng khác chưa được kiểm chứng đầy đủ. Trên Linux/macOS, tạo môi trường bằng `python3 -m venv .venv` và dùng `.venv/bin/python` thay cho đường dẫn Windows; chọn gói PyTorch phù hợp hệ điều hành.

`setup_models.py` tải CLIP ViT-L/14, **chỉ tokenizer_2** của SDXL (không tải mô hình sinh ảnh SDXL), checkpoint LinCIR, checkpoint FTI và hai file nguồn FTI cần thiết. Các asset cố định theo revision/commit; checkpoint và nguồn FTI kiểm tra SHA256 trong model_manifest.json. Lần đầu cần Internet và vài GB dung lượng model/cache. Lần sau dùng model local.

Cache mặc định: `hf_models/` trong project mới. Để tương thích máy phát triển, nếu Windows đã có `C:/hf_cache` thì dùng cache đó. Có thể đổi bằng `--cache_dir` ở demo local hoặc `--cache-dir` ở setup/benchmark, hoặc đặt cùng biến môi trường cho mọi lệnh:

```powershell
$env:CIR_MODEL_CACHE = "D:\cir_model_cache"
.\.venv\Scripts\python.exe setup_models.py
```

## 2. Demo thường — không cần tải CIRCO

```powershell
.\.venv\Scripts\python.exe demo_fti.py
```

Mở **http://127.0.0.1:8013/**. Thêm ảnh ứng viên vào `gallery/` hoặc qua giao diện. Chọn ảnh tham chiếu, nhập text như `wearing a blue shirt`, chọn số kết quả, rồi nhấn **So sánh cả ba phiên bản**. Có thể chọn ảnh đối chiếu để xem thứ hạng của ảnh đó.

- Cần có ảnh phù hợp trong kho. Không có ảnh đáp ứng thì hệ thống vẫn trả ảnh gần nhất.
- Lần đầu mã hóa ảnh thành vector và lưu tại `outputs/index/`; thêm/sửa ảnh sẽ cập nhật phần cần thiết.
- `Ảnh mới` đo cả mã hóa ảnh tham chiếu; `Ảnh dùng lại` chuẩn bị cache trước bộ đếm. Thời gian chuẩn bị được báo riêng.
- Điểm tương đồng không phải xác suất chính xác. Mô hình có thể bỏ sót màu sắc, hoa văn nhỏ hoặc yêu cầu phức tạp.

Demo hai bản gốc/gated: `python demo.py` tại http://127.0.0.1:8000/. Nếu đã kích hoạt môi trường, có thể dùng `python` thay đường dẫn đầy đủ. Windows có `RUN_DEMO.cmd` chạy demo ba bản.

## 3. Demo các ví dụ CIRCO đã chọn

Cần đủ bộ dữ liệu CIRCO trước:

```powershell
.\.venv\Scripts\python.exe prepare_circo.py
.\.venv\Scripts\python.exe prepare_circo.py --check
.\.venv\Scripts\python.exe demo_circo_showcase.py
```

Chỉ chạy benchmark đầy đủ khi `ready: true`, `missing_images: 0`. Dữ liệu có **123.403 ảnh**, khoảng hơn 20 GB; nên dành tối thiểu 30 GB trống cho dữ liệu và dự phòng, chưa tính model. Công cụ tải có thể tiếp tục khi chạy lại. Không xóa ảnh sau khi tạo vector: demo và một số bước đánh giá vẫn cần ảnh.

Mở **http://127.0.0.1:8015/**, cuộn xuống **Ví dụ CIRCO đã kiểm chứng**, chọn một hàng rồi nhấn nút so sánh phía trên. Có bốn ví dụ cải thiện và một ví dụ FTI thua. `docs/demo_cases.json` chứa ID ảnh và text, không chứa đường dẫn máy cá nhân. Demo CIRCO tái sử dụng `outputs/circo_index/`; máy mới phải tạo vector lần đầu. Không thêm ảnh vào kho CIRCO khi so sánh.

| Ví dụ | Hạng ảnh đích: gốc | gated | FTI |
|---|---:|---:|---:|
| Người ngồi ghế, ảnh đen trắng (query 8) | 7 | 2 | 1 |
| Đồ ăn có thuyền và bầu trời phía sau (103) | 21 | 3 | 1 |
| Ghế nhìn từ phía sau, có đồng hồ (199) | 43 | 26 | 1 |
| Hai người đeo cà vạt xanh trong nhà (100) | Ngoài Top50 | Ngoài Top50 | 1 |
| Ví dụ giới hạn (114) | 1 | 1 | 49 |

Các ví dụ được chọn để minh họa, không thay thế benchmark tổng hợp. Hạng là vị trí ảnh đích chuẩn; các ảnh ground truth khác cũng có thể đúng. Đổi sang kho nhỏ sẽ làm thứ hạng thay đổi.

## 4. Benchmark cả ba phiên bản

Thử nhanh 5 truy vấn trên toàn bộ kho:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 benchmark_circo.py --modes baseline gated fti_clip --limit 5 --batch-size 1 --cpu-threads 1 --independent-latency --prepared-reference-latency --output outputs/circo_smoke.json
```

Chạy đủ 220 truy vấn: bỏ `--limit 5`, đổi output sang `outputs/circo_three_versions.json`. Một lần chạy có giới hạn cứng **20 phút**, tính cả nạp model/tạo index. Máy mới chưa có vector có thể vượt giới hạn; chạy lại cùng lệnh để tiếp tục index. Không coi output chạy dở là benchmark đầy đủ. Chạy lại tiếp tục nếu cấu hình và mã giữ nguyên; thay mã/cấu hình thì dùng tên output mới.

- `baseline`, `gated`, `fti_clip` là ba lựa chọn được duy trì.
- `--prepared-reference-latency` đưa mã hóa tham chiếu ra ngoài bộ đếm; bỏ cờ để đo cả bước này. Không so thời gian giữa hai giao thức khác nhau.
- `--independent-latency` xóa cache RAM giữa các bản; thứ tự chạy luân phiên.
- `mAP@K` đo thứ hạng của nhiều ảnh đúng; `Recall@K` dùng ảnh đích chuẩn; `GTRecall@K` dùng toàn bộ ground truth.
- Kết quả đầy đủ cần `partial: false`, `completed_queries: 220`, `snapshot_verified: true`.

Số liệu lịch sử đã kiểm chứng, **không phải số liệu tự động đảm bảo trên mọi máy/kho**:

| Phiên bản | mAP@10 | mAP@50 |
|---|---:|---:|
| LinCIR gốc | 14,04 | 16,26 |
| gated | 16,66 | 19,02 |
| FTI | 18,99 | 21,71 |

Bằng chứng tại `docs/results/`. Đây là CIRCO **validation**, đã dùng trong phát triển; chưa phải test độc lập. FTI dùng tiền xử lý CLIP center-crop224 tương thích gallery, **không tái lập nguyên trạng cấu hình targetpad trong bài FTI**. Không khẳng định FTI thắng mọi truy vấn hoặc luôn đạt ngưỡng tốc độ +10%.

## 5. Các thư mục và phần không đưa lên GitHub

| Vị trí | Nội dung |
|---|---|
| `demo.py`, `demo_fti.py`, `demo_circo_showcase.py` | Giao diện local và so sánh CIRCO |
| `upgraded_retrieval.py`, `fti_retrieval.py` | Hai nâng cấp được giữ |
| `setup_models.py`, `model_manifest.json` | Tải/kiểm tra asset đúng phiên bản |
| `prepare_circo.py`, `benchmark_circo.py` | Dữ liệu và đánh giá |
| `docs/results/`, `docs/demo_cases.json` | Bằng chứng và ví dụ |
| `docs/history/`, `docs/README_UPSTREAM.md` | Báo cáo trước và hướng dẫn nghiên cứu gốc |
| `gallery/`, `benchmarks/` | Ảnh trên máy, bị Git bỏ qua |
| `pretrained_models/`, `experiments/`, `hf_models/` | Model/nguồn tải về, bị Git bỏ qua |
| `outputs/`, `.venv/`, `dist/` | Cache, kết quả mới, môi trường, gói ZIP; bị Git bỏ qua |

Pull mã nguồn **không mang theo** model, ảnh hoặc vector. Mỗi thành viên chạy setup một lần; chỉ cần CIRCO nếu dùng demo/benchmark CIRCO. Khi đổi máy/đường dẫn, index có thể phải tạo lại vì cache kiểm tra đường dẫn, kích thước và thời gian sửa file.

Mã train/evaluate gốc vẫn giữ để tham khảo. Chỉ cài `requirements-training.txt` và xem tài liệu upstream nếu cần nghiên cứu phần đó; nhánh training không nằm trong kiểm tra demo của nhóm.

## 6. Cập nhật và đóng gói

Sau khi pull: cài lại requirements nếu thay đổi, chạy `python setup_models.py --check`, rồi mở demo. Đóng gói mã nguồn đã chọn bằng:

```powershell
.\.venv\Scripts\python.exe package_project.py
```

Gói ZIP và danh sách SHA256 nằm trong `dist/`; không chứa `.git`, model, ảnh gallery/CIRCO, cache, log hoặc môi trường. Để đưa lên GitHub, dùng repository hiện tại, kiểm tra `git status`, commit mã/docs cần thiết rồi push lên repository nhóm. Không dùng `git add -f` với dữ liệu/model.

## 7. Lỗi thường gặp

- Thiếu checkpoint/cache: chạy `python setup_models.py`; nếu dùng cache riêng, đặt cùng đường dẫn cho setup và demo.
- Thiếu thư viện: xác nhận dùng Python của `.venv`, cài `requirements.txt`.
- Cổng bận: thêm `--port 8016` vào lệnh demo.
- CIRCO chưa sẵn sàng: chạy lại prepare và check; demo thường vẫn dùng được với kho riêng.
- Lần đầu lâu: phải nạp model và tạo vector. `Get-Content ... -Wait` chỉ xem log, không phải tiến trình tải.
- Số thứ hạng khác: kiểm tra cùng kho đầy đủ, cùng text, cùng checkpoint và tiền xử lý.

## 8. Nguồn và giấy phép

Project này là bản chỉnh sửa phục vụ bài tập, dựa trên [LinCIR của NAVER](https://github.com/navervision/LinCIR) và [bài LinCIR](https://arxiv.org/abs/2312.01998). Giữ `LICENSE`, `NOTICE` và tài liệu upstream; mã gốc LinCIR theo CC BY-NC-4.0. FTI dùng asset từ [nguồn FTI4CIR](https://github.com/iLearn-Lab/SIGIR24-FTI4CIR), được tải riêng, không gán lại giấy phép của LinCIR cho asset FTI. CIRCO/COCO và ảnh có điều kiện sử dụng riêng, không đóng gói lại trong repo này. Chi tiết nguồn/commit tại model_manifest.json.
