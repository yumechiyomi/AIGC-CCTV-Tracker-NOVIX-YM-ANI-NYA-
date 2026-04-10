# =================================================================
# PROJECT     : NOVIX YM ANI
# CORE TECH   : 3D ANATOMICAL INVARIANTS RECONSTRUCTION
# AUTHOR      : YUME CHIYOMI (ARCHITECT)
# STATUS      : NON-PROFIT CONTRIBUTION TO A05 - VIETNAM
# -----------------------------------------------------------------
# Mọi hành vi sao chép, thương mại hóa ngoài mục đích an ninh quốc gia
# đều vi phạm quyền sở hữu trí tuệ của tác giả.
# =================================================================
import cv2
import time
import threading


# ==================================================
# CAMERA STATUS
# ==================================================
class CameraStatus:
    OK = "OK"
    CONNECT_FAIL = "CONNECT_FAIL"
    NO_FRAME = "NO_FRAME"


# ==================================================
# TEST CAMERA
# ==================================================
def test_camera(url, timeout=5):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        return CameraStatus.CONNECT_FAIL

    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None:
            cap.release()
            return CameraStatus.OK

    cap.release()
    return CameraStatus.NO_FRAME


# ==================================================
# CAMERA CLASS
# ==================================================
class Camera:
    def __init__(self, cam_id, url, name=None, fps=2):
        self.cam_id = cam_id
        self.url = url
        self.name = name or cam_id
        self.fps = fps

        self.cap = None
        self.last_read = 0
        self.lock = threading.Lock()

        self.fail_count = 0
        self.last_frame = None

    # ----------------------------------------------
    # OPEN CAMERA
    # ----------------------------------------------
    def open(self):
        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            raise RuntimeError(f"Không mở được camera {self.name}")

    # ----------------------------------------------
    # READ FRAME (FPS CONTROL)
    # ----------------------------------------------
    def read(self):
        with self.lock:
            now = time.time()
            if now - self.last_read < 1.0 / self.fps:
                return None

            self.last_read = now

            if self.cap is None or not self.cap.isOpened():
                self._reconnect()

            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.fail_count += 1
                if self.fail_count >= 3:
                    self._reconnect()
                return None

            self.fail_count = 0
            self.last_frame = frame
            return frame

    # ----------------------------------------------
    # RECONNECT WITH BACKOFF
    # ----------------------------------------------
    def _reconnect(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass

        for wait in [1, 2, 5, 10]:
            try:
                time.sleep(wait)
                self.cap = cv2.VideoCapture(self.url)
                if self.cap.isOpened():
                    self.fail_count = 0
                    return
            except Exception:
                continue

    # ----------------------------------------------
    # CLOSE
    # ----------------------------------------------
    def close(self):
        if self.cap:
            self.cap.release()


# ==================================================
# CAMERA MANAGER (MULTI CAM)
# ==================================================
class CameraManager:
    def __init__(self, cameras: dict, fps=2):
        """
        cameras = {
            "CAM_01": {"name": "...", "url": 0},
            "CAM_02": {"name": "...", "url": "rtsp://user:pass@ip/..."}
        }
        """
        self.cameras = {}
        for cid, cfg in cameras.items():
            self.cameras[cid] = Camera(
                cam_id=cid,
                url=cfg["url"],
                name=cfg.get("name", cid),
                fps=fps
            )

    # ----------------------------------------------
    # TEST ALL CAMERAS
    # ----------------------------------------------
    def test_all(self):
        result = {}
        for cid, cam in self.cameras.items():
            result[cid] = test_camera(cam.url)
        return result

    # ----------------------------------------------
    # OPEN ALL
    # ----------------------------------------------
    def open_all(self):
        for cam in self.cameras.values():
            try:
                cam.open()
            except Exception as e:
                print(f"[WARN] {cam.name}: {e}")

    # ----------------------------------------------
    # READ ALL FRAMES
    # ----------------------------------------------
    def read_all(self):
        frames = {}
        for cid, cam in self.cameras.items():
            frame = cam.read()
            if frame is not None:
                frames[cid] = frame
        return frames

    # ----------------------------------------------
    # CLOSE ALL
    # ----------------------------------------------
    def close_all(self):
        for cam in self.cameras.values():
            cam.close()
