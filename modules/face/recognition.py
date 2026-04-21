import numpy as np
from deepface import DeepFace
from config.settings import (
    DEEPFACE_MODEL, DEEPFACE_DETECTOR,
    DEEPFACE_DISTANCE, SIMILARITY_THRESHOLD
)
from .embedding import get_embeddings_db


def _cosine_distance(a: list, b: list) -> float:
    """Tính cosine distance giữa 2 vector."""
    a, b = np.array(a), np.array(b)
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)


def _euclidean_distance(a: list, b: list) -> float:
    """Tính euclidean distance giữa 2 vector."""
    return float(np.linalg.norm(np.array(a) - np.array(b)))


def recognize_face(img_path: str) -> dict:
    """
    Nhận diện khuôn mặt từ ảnh.

    Args:
        img_path: Đường dẫn ảnh cần nhận diện

    Returns:
        {
            "success": bool,
            "username": str | None,
            "distance": float | None,
            "confidence": float,       # 0.0 → 1.0
            "message": str
        }
    """
    # 1. Tính embedding ảnh đầu vào
    try:
        result = DeepFace.represent(
            img_path=img_path,
            model_name=DEEPFACE_MODEL,
            detector_backend=DEEPFACE_DETECTOR,
            enforce_detection=True,
        )
        input_emb = result[0]["embedding"]
    except Exception as e:
        return {
            "success": False,
            "username": None,
            "distance": None,
            "confidence": 0.0,
            "message": f"Không phát hiện được khuôn mặt: {e}",
        }

    # 2. Load database
    db = get_embeddings_db()
    if not db:
        return {
            "success": False,
            "username": None,
            "distance": None,
            "confidence": 0.0,
            "message": "Database trống. Hãy đăng ký người dùng trước.",
        }

    # 3. So sánh với tất cả người dùng
    best_name = None
    best_dist = float("inf")

    for username, data in db.items():
        stored_emb = data["embedding"]
        if DEEPFACE_DISTANCE == "cosine":
            dist = _cosine_distance(input_emb, stored_emb)
        else:
            dist = _euclidean_distance(input_emb, stored_emb)

        if dist < best_dist:
            best_dist = dist
            best_name = username

    # 4. Đánh giá kết quả
    if best_dist <= SIMILARITY_THRESHOLD:
        # Chuyển distance → confidence (0→1)
        confidence = max(0.0, 1.0 - best_dist / SIMILARITY_THRESHOLD)
        return {
            "success": True,
            "username": best_name,
            "distance": round(best_dist, 4),
            "confidence": round(confidence, 2),
            "message": f"Xin chào, {best_name}!",
        }
    else:
        return {
            "success": False,
            "username": None,
            "distance": round(best_dist, 4),
            "confidence": 0.0,
            "message": "Không nhận diện được. Bạn chưa được đăng ký.",
        }


def recognize_from_frame(frame) -> dict:
    """
    Nhận diện từ numpy array (frame từ OpenCV).
    Lưu tạm thành file rồi gọi recognize_face.
    """
    import cv2, os, time
    from config.settings import TEMP_DIR

    tmp_path = os.path.join(TEMP_DIR, f"tmp_{int(time.time()*1000)}.jpg")
    cv2.imwrite(tmp_path, frame)
    result = recognize_face(tmp_path)

    # Xóa file tạm
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return result