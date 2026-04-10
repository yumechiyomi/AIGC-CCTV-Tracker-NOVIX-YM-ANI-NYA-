
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
import os
from collections import deque
from lb_core_aicg import CGFaceID
from lb_cam_worker import CamWorker
import torch
# ===============================
# CONFIG LOADER
# ===============================
def load_config(path="setup/log.txt"):
    cfg = {}
    if not os.path.exists(path):
        return cfg

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().lower()

    return cfg


# ===============================
# CCTV LIBRARY
# ===============================
class CCTV:
    def __init__(self, query_image, cameras, config_path="setup/log.txt"):
        self.cfg = load_config(config_path)

        # ---------- CONFIG ----------
        self.threshold = int(self.cfg.get("threshold", 70))
        self.child_mode = self.cfg.get("child_mode", "false") == "true"
        self.upload_enabled = self.cfg.get("upload_enabled", "false") == "true"
        self.upload_endpoint = self.cfg.get("upload_endpoint")

        # ⭐ capture config
        self.capture_count = int(self.cfg.get("capture_count", 3))

        # ---------- AI ----------
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.ai = CGFaceID(device=device, child_mode=self.child_mode)
                self.query_img = cv2.imread(query_image)

        if self.query_img is None:
            raise ValueError("❌ Không đọc được query image")
        self.query_emb, self.age = self.ai.process_image(self.query_img)

        # ---------- CAMERA ----------
        self.worker = CamWorker("W1", cameras)
        self.worker.start()

        # ⭐ frame buffer per camera
        self.frame_buffer = {}
        for cam_id in cameras.keys():
            self.frame_buffer[cam_id] = deque(maxlen=self.capture_count)

    # ===============================
    # MAIN STREAM (RETURN)
    # ===============================
    def listen(self):
            while True:
                data = self.worker.get_frame()
                if not data:
                    continue

                cam_id = data["camera_id"]
                frame = data["frame"]

                emb, _ = self.ai.process_image(frame)

                
                if cam_id in self.frame_buffer:
                    self.frame_buffer[cam_id].append(frame.copy())

                
                out = self.ai.matcher.compare(
                    self.query_emb,
                    emb,
                    self.age,
                    child_mode=self.child_mode
                )

                
                if out["score"] >= self.threshold:
                    result = {
                        "camera_id": cam_id,
                        "match_percent": round(out["score"], 2),
                        "age_est": self.age,
                        "explain": out["explain"],
                        
                        "images": list(self.frame_buffer.get(cam_id, []))
                    }

                    
                    if self.upload_enabled:
                        self._upload(result)

                    yield result

    # ===============================
    # OPTIONAL UPLOAD
    # ===============================
    def _upload(self, data):
        if not self.upload_endpoint:
            return
        try:
            import requests
            requests.post(
                self.upload_endpoint,
                json=data,
                timeout=5
            )
        except Exception:
            pass
    # ===============================
    # STOP SYSTEM
    # ===============================
    def stop(self):
        if hasattr(self, "worker") and self.worker:
            self.worker.stop()
