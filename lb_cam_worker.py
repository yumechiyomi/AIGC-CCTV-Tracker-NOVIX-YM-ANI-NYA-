# =================================================================
# PROJECT     : NOVIX YM ANI
# CORE TECH   : 3D ANATOMICAL INVARIANTS RECONSTRUCTION
# AUTHOR      : YUME CHIYOMI (ARCHITECT)
# STATUS      : NON-PROFIT CONTRIBUTION TO A05 - VIETNAM
# -----------------------------------------------------------------
# Mọi hành vi sao chép, thương mại hóa ngoài mục đích an ninh quốc gia
# đều vi phạm quyền sở hữu trí tuệ của tác giả.
# =================================================================
import time
import queue
import threading
from lb_camlib import CameraManager

# ==================================================
# CAM WORKER
# ==================================================
class CamWorker:
    def __init__(self, worker_id, cameras, fps=2):
        """
        worker_id : tên worker
        cameras   : dict camera được phân cho worker
        fps       : fps mỗi camera
        """
        self.worker_id = worker_id
        self.cam_mgr = CameraManager(cameras, fps=fps)

        self.running = False
        self.frame_queue = queue.Queue(maxsize=50)

    # ----------------------------------------------
    # START WORKER
    # ----------------------------------------------
    def start(self):
        print(f"[WORKER {self.worker_id}] Starting...")
        self.cam_mgr.open_all()
        self.running = True

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    # ----------------------------------------------
    # MAIN LOOP
    # ----------------------------------------------
    def _loop(self):
        while self.running:
            frames = self.cam_mgr.read_all()
            for cid, frame in frames.items():
                try:
                    self.frame_queue.put_nowait({
                        "worker": self.worker_id,
                        "camera_id": cid,
                        "frame": frame,
                        "time": time.time()
                    })
                except queue.Full:
                    pass

            time.sleep(0.01)

    # ----------------------------------------------
    # GET FRAME (FOR AI ENGINE)
    # ----------------------------------------------
    def get_frame(self, timeout=1):
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ----------------------------------------------
    # STOP
    # ----------------------------------------------
    def stop(self):
        self.running = False
        self.cam_mgr.close_all()
        print(f"[WORKER {self.worker_id}] Stopped")
