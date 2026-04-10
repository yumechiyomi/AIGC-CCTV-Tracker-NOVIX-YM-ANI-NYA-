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
import json
import cv2
from datetime import datetime
from easy_cctv import CCTV

# ===============================
# SYSTEM INFO
# ===============================
SYSTEM_NAME = "AIGC CCTV TRACKER"
VERSION = "3.0.0"
AUTHOR = "Yume Chiyomi"

CAM_DIR = "cam"
WINDOW_SCALE = 0.6


# ===============================
# LOAD CAMERAS
# ===============================
def load_cameras(cam_dir):
    cameras = {}

    if not os.path.exists(cam_dir):
        return cameras

    for file in os.listdir(cam_dir):
        if not file.endswith(".json"):
            continue

        with open(os.path.join(cam_dir, file), "r", encoding="utf-8") as f:
            cam = json.load(f)

        cam_id = cam["camera_id"]

        cameras[cam_id] = {
            "name": cam.get("name", cam_id),
            "url": cam["url"],
            "latitude": cam.get("latitude"),
            "longitude": cam.get("longitude")
        }

    return cameras


# ===============================
# TERMINAL UI
# ===============================
def banner(cam_count):
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 65)
    print(f"{SYSTEM_NAME}")
    print(f"Version : {VERSION}")
    print(f"Author  : {AUTHOR}")
    print(f"Cameras : {cam_count}")
    print("=" * 65)
    print("Đang chạy (ESC để thoát | Ctrl+C để dừng)\n")


def show_result(r):
    print("\nPHÁT HIỆN!")
    print(f"Camera    : {r['camera_id']}")
    print(f"Độ khớp   : {r['match_percent']}%")
    print(f"Nhóm tuổi : {r['age_est']}")
    print(f"Thời gian : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Giải thích sinh học:")

    for k, v in r["explain"].items():
        print(f"   - {k}: {v}")

    print(f"Ảnh chụp: {len(r['images'])}")
    print("-" * 65)

    for i, img in enumerate(r["images"]):
        cv2.imshow(f"[MATCH] {r['camera_id']} #{i}", img)


# ===============================
# RUN SYSTEM (LIBRARY ENTRY)
# ===============================
def run(
    cam_dir="cam",
    query_image_path=None,   # truyền đường dẫn
    query_img_array=None,    # hoặc truyền numpy image
    config_path="setup/log.txt"
):
    cameras = load_cameras(cam_dir)

    if not cameras:
        print("Không tìm thấy camera trong cam/")
        return

    banner(len(cameras))

    # ===============================
    # XỬ LÝ ẢNH QUERY
    # ===============================
    if query_img_array is not None:
        query_input = query_img_array
    elif query_image_path is not None:
        query_input = query_image_path
    else:
        raise ValueError("Bạn phải truyền query_image_path hoặc query_img_array")

    cctv = CCTV(
        query_image=query_input,
        cameras=cameras,
        config_path=config_path
    )

    try:
        for r in cctv.listen():

            # ---------- LIVE CAMERA ----------
            for cid, frames in cctv.frame_buffer.items():
                if not frames:
                    continue

                frame = frames[-1]
                h, w = frame.shape[:2]
                resized = cv2.resize(
                    frame,
                    (int(w * WINDOW_SCALE), int(h * WINDOW_SCALE))
                )

                cv2.imshow(f"LIVE | {cid}", resized)

            # ---------- MATCH EVENT ----------
            show_result(r)

            key = cv2.waitKey(1)
            if key == 27:
                break

    except KeyboardInterrupt:
        pass
    finally:
        cctv.stop()
        print("\nHệ thống đã dừng")
        cv2.destroyAllWindows()


# ===============================
# ALLOW DIRECT RUN
# ===============================
if __name__ == "__main__":
    # chạy trực tiếp bằng file mặc định
    run(query_image_path="query.jpg")
