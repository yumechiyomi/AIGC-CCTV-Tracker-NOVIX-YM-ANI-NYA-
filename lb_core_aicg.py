# =================================================================
# PROJECT     : NOVIX YM ANI
# CORE TECH   : 3D ANATOMICAL INVARIANTS RECONSTRUCTION
# AUTHOR      : YUME CHIYOMI (ARCHITECT)
# STATUS      : NON-PROFIT CONTRIBUTION TO A05 - VIETNAM
# -----------------------------------------------------------------
# Mọi hành vi sao chép, thương mại hóa ngoài mục đích an ninh quốc gia
# đều vi phạm quyền sở hữu trí tuệ của tác giả.
# =================================================================
# =========================================================
# CG FACE IDENTIFICATION - FULL ONE FILE (DECA REAL)
# =========================================================
# REQUIRE:
# - DECA repo cloned (https://github.com/YadiraF/DECA)
# - pretrained models downloaded (fetch_data.sh)
# =========================================================

import cv2
import numpy as np
import torch
import mediapipe as mp
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Dict, List, Tuple

# =========================================================
# DECA IMPORT
# =========================================================
from decalib.deca import DECA
from decalib.utils.config import cfg as deca_cfg

# =========================================================
# DATA STRUCTURES
# =========================================================

@dataclass
class SkullCG:
    shape: torch.Tensor
    regions: Dict[str, torch.Tensor]
    age_group: str


@dataclass
class Embedding:
    vector: torch.Tensor
    region_scores: Dict[str, float]


# =========================================================
# FACE ANALYZER
# =========================================================

import cv2
import mediapipe as mp
import numpy as np

class FaceAnalyzer:
    def __init__(self):
        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )

    # detect trả thêm bbox info
    # Tìm đến Class FaceAnalyzer trong file lb_core_aicg.py
    def detect(self, img: np.ndarray):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.detector.process(rgb)
        h, w, _ = img.shape

        if result.detections:
            #
            bbox = result.detections[0].location_data.relative_bounding_box
            
            
            x_min = int(bbox.xmin * w)
            y_min = int(bbox.ymin * h)
            bw = int(bbox.width * w)
            bh = int(bbox.height * h)

            
            cx, cy = x_min + bw // 2, y_min + bh // 2
            
            side = int(max(bw, bh) * 1.5) 

            
            x1 = max(0, cx - side // 2)
            y1 = max(0, cy - side // 2)
            x2 = min(w, x1 + side)
            y2 = min(h, y1 + side)

            face_crop = img[y1:y2, x1:x2]
            
            return face_crop, (x2-x1, y2-y1, w, h)

        return img, (w, h, w, h)
    def age_group(self, bbox_info):
        bw, bh, w, h = bbox_info

        face_ratio = (bw * bh) / (w * h)

        if face_ratio < 0.02:
            return "ADULT"
        elif face_ratio < 0.05:
            return "TEEN"
        elif face_ratio < 0.1:
            return "CHILD"
        else:
            return "INFANT"


# =========================================================
# LOAD DECA (NO RENDER)
# =========================================================

def load_deca(device="cuda"):
    deca_cfg.model.use_tex = False
    deca_cfg.model.use_light = False
    deca_cfg.model.extract_tex = False
    deca_cfg.model.use_detail = False
    deca_cfg.rasterizer_type = "standard"

    deca = DECA(config=deca_cfg, device=device)
    deca.eval()
    return deca


# =========================================================
# SKULL INFERENCE (REAL CG)
# =========================================================

class SkullInferencerDECA:
    def __init__(self, device="cuda"):
        self.device = device
        self.deca = load_deca(device)

    @torch.no_grad()
    def infer(self, face_tensor: torch.Tensor, age_group: str) -> SkullCG:
        face_tensor = face_tensor.to(self.device)
        codedict = self.deca.encode(face_tensor)

        shape = codedict["shape"].squeeze(0)
        codedict["exp"].zero_()

        regions = {
            "orbit": shape[0:40],
            "nasal": shape[40:70],
            "forehead": shape[70:110],
            "global": shape[110:]
        }

        return SkullCG(shape=shape, regions=regions, age_group=age_group)


# =========================================================
# GROWTH NORMALIZATION
# =========================================================

class GrowthNormalizer:
    def normalize(self, skull: SkullCG) -> SkullCG:
        s = skull.shape

        if skull.age_group in ("INFANT", "CHILD"):
            s = s * 1.15
        elif skull.age_group == "TEEN":
            s = s * 1.05

        s = F.normalize(s, dim=0)
        skull.shape = s

        skull.regions = {
            "orbit": s[0:40],
            "nasal": s[40:70],
            "forehead": s[70:110],
            "global": s[110:]
        }
        return skull


# =========================================================
# EMBEDDING NETWORK
# =========================================================

class SkullEmbeddingNet(nn.Module):
    def __init__(self, in_dim=200, out_dim=1024):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.ReLU(),
            nn.Linear(512, out_dim)
        )

    def forward(self, x):
        return F.normalize(self.net(x), dim=1)


# =========================================================
# BIOLOGICAL MATCHER
# =========================================================

class Matcher:
    def compare(self, q: Embedding, c: Embedding, age: str, child_mode=False) -> Dict:

        if child_mode:
            w = {"orbit": 0.60, "nasal": 0.15, "forehead": 0.10, "global": 0.15}
        elif age in ("INFANT", "CHILD"):
            w = {"orbit": 0.45, "nasal": 0.20, "forehead": 0.15, "global": 0.20}
        elif age == "TEEN":
            w = {"orbit": 0.30, "nasal": 0.20, "forehead": 0.15, "global": 0.35}
        else:
            w = {"orbit": 0.25, "nasal": 0.20, "forehead": 0.15, "global": 0.40}

        cos = float(torch.sum(q.vector * c.vector))

        bio = 0.0
        explain = {}
        for k in w:
            s = min(q.region_scores[k], c.region_scores[k])
            bio += w[k] * s
            explain[k] = round(float(s), 3)

        score = (0.7 * cos + 0.3 * bio) * 100.0
        return {"score": score, "explain": explain}


# =========================================================
# FULL SYSTEM
# =========================================================

class CGFaceID:
    def __init__(self, device="cuda", child_mode=False):
        self.child_mode = child_mode
        self.face = FaceAnalyzer() # Khởi tạo bộ dò
        self.skull_inf = SkullInferencerDECA(device)
        self.growth = GrowthNormalizer()
        self.embed_net = SkullEmbeddingNet().to(device)
        self.matcher = Matcher()
        self.device = device
         # Khởi tạo bộ dò
    def preprocess_face(self, face: np.ndarray) -> torch.Tensor:
        face = cv2.resize(face, (224, 224))
        face = face[:, :, ::-1]
        face = torch.from_numpy(face).permute(2, 0, 1).float() / 255.0
        return face.unsqueeze(0)

    def process_image(self, img: np.ndarray) -> Tuple[Embedding, str]:
        # Gọi hàm detect để lấy đúng vùng mặt
        face_crop, bbox_info = self.face.detect(img)
        age = self.face.age_group(bbox_info)
        face_t = self.preprocess_face(face_crop)

        skull = self.skull_inf.infer(face_t, age)
        skull = self.growth.normalize(skull)

        emb_vec = self.embed_net(skull.shape.unsqueeze(0).to(self.device)).squeeze(0)

        region_scores = {
            k: float(torch.norm(v))
            for k, v in skull.regions.items()
        }

        return Embedding(emb_vec, region_scores), age

    def find(self, query: np.ndarray, candidates: List[np.ndarray]) -> Dict:
        q_emb, age = self.process_image(query)

        results = []
        explains = []

        for i, img in enumerate(candidates):
            c_emb, _ = self.process_image(img)
            out = self.matcher.compare(
                q_emb,
                c_emb,
                age,
                child_mode=self.child_mode
            )

            results.append((i, out["score"]))
            explains.append(out["explain"])

        results.sort(key=lambda x: x[1], reverse=True)
        best_id, best_score = results[0]

        return {
            "best_match": {
                "id": best_id,
                "percent": round(best_score, 2),
                "age_mode": age,
                "confidence": (
                    "VERY HIGH" if best_score > 85 else
                    "HIGH" if best_score > 70 else
                    "MEDIUM"
                ),
                "explain": explains[best_id]
            },
            "top_k": [
                {"id": i, "percent": round(s, 2)}
                for i, s in results[:5]
            ]
        }


# =========================================================
# DEMO
# =========================================================

if __name__ == "__main__":
    system = CGFaceID(device="cuda")

    query = np.zeros((256, 256, 3), dtype=np.uint8)
    candidates = [
        np.ones((256, 256, 3), dtype=np.uint8) * (i * 25)
        for i in range(6)
    ]

    result = system.find(query, candidates)
    print(result)
