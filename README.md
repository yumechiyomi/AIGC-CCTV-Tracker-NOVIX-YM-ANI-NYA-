# NOVIX YM ANI: AIGC CCTV Tracker v10.0

**NOVIX YM ANI** là hệ thống truy vết đối tượng thông minh thông qua mạng lưới CCTV, dựa trên công nghệ **Tái cấu trúc đặc điểm giải phẫu 3D (3D Anatomical Invariants Reconstruction)**. Dự án được thiết kế chuyên biệt để hỗ trợ công tác an ninh, giúp duy trì nhận diện đối tượng ngay cả khi bị che khuất hoặc thay đổi diện mạo theo thời gian.

> [!IMPORTANT]
> **Tình trạng:** Beta.  
> **Bản quyền:** Sản phẩm được phát triển độc lập 100% bởi Yume Chiyomi. Mọi hành vi sao chép hoặc thương mại hóa ngoài mục đích an ninh đều vi phạm quyền sở hữu trí tuệ của tác giả.

## Công nghệ cốt lõi

Hệ thống tập trung vào phân tích các chỉ số sinh học và cấu trúc xương thay vì chỉ nhận diện khuôn mặt 2D thông thường:

* **3D Skull Inference (DECA):** Tích hợp thư viện DECA để suy luận cấu trúc hộp sọ từ hình ảnh 2D, giúp nhận diện chính xác ở nhiều góc quay khác nhau.
* **Anatomical Invariants Reconstruction:** Phân tích các vùng đặc điểm giải phẫu bất biến:
    * **Orbit:** Vùng hốc mắt (Chiếm trọng số cao nhất khi truy tìm trẻ em).
    * **Nasal:** Cấu trúc vùng mũi.
    * **Forehead:** Đặc điểm vùng trán.
* **Growth Normalization:** Thuật toán tự động bù đắp sự tăng trưởng sinh học theo độ tuổi (Infant, Child, Teen, Adult) để duy trì độ khớp khi đối tượng trưởng thành.
* **Biological Matcher:** Cơ chế so khớp kết hợp giữa Vector Embedding và giải thích sinh học (Explainable AI).

## Cấu trúc hệ thống

Dự án được module hóa để đạt hiệu năng xử lý song song và hoạt động ổn định:

* **`main.py`**: Điểm khởi đầu của hệ thống, hỗ trợ kiểm tra phần cứng (GPU/CUDA) và nhận diện mục tiêu.
* **`lb_core_aicg.py`**: "Bộ não" AI xử lý Face Detection (MediaPipe), Skull Inference (DECA) và nhúng vector đặc trưng.
* **`lb_easy_cctv.py`**: Thư viện quản lý logic camera, bộ đệm khung hình và kết nối luồng xử lý AI.
* **`lb_cam_worker.py` & `lb_camlib.py`**: Quản lý đa luồng (Multi-threading) cho các luồng camera, đảm bảo FPS ổn định và tự động kết nối lại khi mất tín hiệu.
* **`_search.py`**: Giao diện điều khiển (Terminal UI) hiển thị kết quả truy vết và Live Camera.

## 📂 Cấu trúc thư mục

```text
.
├── cam/                # Chứa cấu hình các camera (.json)
├── setup/              # Chứa tệp cấu hình log.txt
├── _search.py          # Logic chạy chính và giao diện hiển thị
├── lb_core_aicg.py     # Nhân xử lý AI và đặc điểm sinh học
├── lb_easy_cctv.py     # Thư viện tích hợp hệ thống CCTV
├── lb_cam_worker.py    # Quản lý luồng xử lý camera
├── lb_camlib.py        # Thư viện điều khiển phần cứng camera
└── main.py             # Script khởi chạy hệ thống (Runner)
## 📦 Yêu cầu cài đặt

Hệ thống yêu cầu **Python 3.9+** và các thư viện sau:

* **OpenCV, NumPy**: Xử lý hình ảnh và tính toán ma trận.
* **PyTorch, TensorFlow**: Framework học sâu cho các mô hình AI.
* **MediaPipe**: Hỗ trợ nhận diện các điểm đặc trưng trên cơ thể.
* **DECA (Pre-trained models)**: Mô hình tái cấu trúc cấu trúc mặt 3D.
```
---

## 💻 Hướng dẫn sử dụng

1.  **Cấu hình Camera**: Thêm các tệp cấu hình `.json` vào thư mục `cam/`.
2.  **Khởi chạy**:

Sử dụng lệnh sau trong terminal:

```bash
python main.py
```
## 👤 Tác giả

* **KTS Hệ thống:** Yume Chiyomi (yumec807).
* **Mục tiêu:** Phát triển giải pháp AI bảo vệ an ninh cộng đồng.

> **Lưu ý:** Dự án được tối ưu hóa cho xử lý thời gian thực trên các dòng **MacBook** và **Workstation** có hỗ trợ GPU.
