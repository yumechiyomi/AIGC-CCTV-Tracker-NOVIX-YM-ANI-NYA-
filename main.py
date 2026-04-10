# =================================================================
# PROJECT     : NOVIX YM ANI
# CORE TECH   : 3D ANATOMICAL INVARIANTS RECONSTRUCTION
# AUTHOR      : YUME CHIYOMI (ARCHITECT)
# STATUS      : NON-PROFIT CONTRIBUTION TO A05 - VIETNAM
# -----------------------------------------------------------------
# Mọi hành vi sao chép, thương mại hóa ngoài mục đích an ninh quốc gia
# đều vi phạm quyền sở hữu trí tuệ của tác giả.
# =================================================================
import os
import sys
import argparse
import torch
from _search import run

def check_hardware():
    print("="*50)
    print("KIỂM TRA HỆ THỐNG")
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"GPU: {gpu_name} ({vram:.2f} GB VRAM) - SẴN SÀNG")
    else:
        print("CẢNH BÁO: Không tìm thấy GPU. Hệ thống sẽ chạy rất chậm trên CPU!")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description="AIGC CCTV High-Performance Runner")
    
    # Cho phép nhập đường dẫn ảnh ngay khi gõ lệnh
    parser.add_argument("image", nargs="?", help="Đường dẫn ảnh mục tiêu (ví dụ: target.jpg)")
    
    # Tham số cấu hình bổ sung
    parser.add_argument("--threshold", type=int, default=75, help="Độ chính xác yêu cầu (0-100)")
    parser.add_argument("--child", action="store_true", help="Kích hoạt chế độ tìm trẻ em")

    args = parser.parse_args()

    # Nếu không nhập đường dẫn ảnh khi gõ lệnh, chương trình sẽ hỏi
    query_path = args.image
    if not query_path:
        query_path = input("Nhập đường dẫn hoặc kéo thả ảnh vào đây: ").strip()
        # Xử lý trường hợp kéo thả ảnh có dấu ngoặc kép trên Windows
        query_path = query_path.replace('"', '').replace("'", "")

    if not os.path.exists(query_path):
        print(f"Lỗi: Không tìm thấy file tại {query_path}")
        return

    check_hardware()

    print(f"Đang truy vết đối tượng: {query_path}")
    
    try:
        # Kích hoạt bộ xử lý từ _search.py
        # Bạn có thể ép cấu hình mạnh nhất tại đây
        run(
            query_image_path=query_path,
            # Có thể truyền thêm cấu hình trực tiếp nếu cần
        )
    except KeyboardInterrupt:
        print("\nHệ thống đã dừng theo yêu cầu.")
    except Exception as e:
        print(f"Lỗi vận hành: {e}")

if __name__ == "__main__":
    main()
