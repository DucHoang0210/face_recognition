import os
import json
import glob
import numpy as np
from deepface import DeepFace
from config.settings import (
    FACES_DIR, EMBEDDINGS_PATH,
    DEEPFACE_MODEL, DEEPFACE_DETECTOR
)


# ──────────────────────────────────────────────
# Helpers đọc / ghi file JSON
# ──────────────────────────────────────────────

def _load_db() -> dict:
    """Đọc embeddings.json, trả về dict rỗng nếu chưa tồn tại."""
    if not os.path.exists(EMBEDDINGS_PATH):
        return {}
    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(db: dict) -> None:
    """Ghi dict vào embeddings.json."""
    with open(EMBEDDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# Tính embedding cho 1 ảnh
# ──────────────────────────────────────────────

def _get_embedding(img_path: str) -> list | None:
    """
    Tính embedding vector cho ảnh tại img_path.
    Trả về list float, hoặc None nếu không phát hiện được khuôn mặt.
    """
    try:
        result = DeepFace.represent(
            img_path=img_path,
            model_name=DEEPFACE_MODEL,
            detector_backend=DEEPFACE_DETECTOR,
            enforce_detection=True,
        )
        return result[0]["embedding"]
    except Exception as e:
        print(f"[embedding] Lỗi xử lý {img_path}: {e}")
        return None


# ──────────────────────────────────────────────
# API công khai
# ──────────────────────────────────────────────

def build_embeddings() -> int:
    """
    Quét toàn bộ ảnh trong FACES_DIR, tính embedding và lưu vào JSON.
    Tên file = tên người dùng (vd: duchoang.jpg → 'duchoang').
    
    Returns:
        Số người đã xử lý thành công.
    """
    db = {}
    patterns = ["*.jpg", "*.jpeg", "*.png"]
    image_paths = []
    for p in patterns:
        image_paths.extend(glob.glob(os.path.join(FACES_DIR, p)))

    for img_path in image_paths:
        username = os.path.splitext(os.path.basename(img_path))[0]
        emb = _get_embedding(img_path)
        if emb is not None:
            db[username] = {
                "embedding": emb,
                "img_path": img_path,
            }
            print(f"[embedding] ✅ {username}")
        else:
            print(f"[embedding] ❌ {username} — bỏ qua")

    _save_db(db)
    print(f"[embedding] Đã lưu {len(db)} người vào {EMBEDDINGS_PATH}")
    return len(db)


def add_user(username: str, img_path: str) -> bool:
    """
    Thêm hoặc cập nhật 1 người dùng vào database.

    Args:
        username: Tên hiển thị / ID người dùng
        img_path: Đường dẫn ảnh khuôn mặt

    Returns:
        True nếu thành công, False nếu không phát hiện được khuôn mặt
    """
    emb = _get_embedding(img_path)
    if emb is None:
        return False

    # Sao chép ảnh vào FACES_DIR
    import shutil
    ext = os.path.splitext(img_path)[1]
    dest = os.path.join(FACES_DIR, f"{username}{ext}")
    if img_path != dest:
        shutil.copy2(img_path, dest)

    db = _load_db()
    db[username] = {
        "embedding": emb,
        "img_path": dest,
    }
    _save_db(db)
    print(f"[embedding] Đã thêm '{username}'")
    return True


def add_user_from_multiple(username: str, img_paths: list[str]) -> bool:
    """
    Thêm người dùng từ nhiều ảnh, lấy embedding trung bình để tăng độ chính xác.
    """
    embeddings = []
    for p in img_paths:
        emb = _get_embedding(p)
        if emb is not None:
            embeddings.append(emb)

    if not embeddings:
        print(f"[embedding] Không lấy được embedding nào cho '{username}'")
        return False

    avg_emb = np.mean(embeddings, axis=0).tolist()

    # Lưu ảnh đầu tiên hợp lệ làm ảnh đại diện
    import shutil
    first_valid = img_paths[0]
    ext = os.path.splitext(first_valid)[1]
    dest = os.path.join(FACES_DIR, f"{username}{ext}")
    shutil.copy2(first_valid, dest)

    db = _load_db()
    db[username] = {
        "embedding": avg_emb,
        "img_path": dest,
    }
    _save_db(db)
    print(f"[embedding] Đã thêm '{username}' từ {len(embeddings)} ảnh")
    return True


def delete_user(username: str) -> bool:
    """Xóa người dùng khỏi database và ảnh lưu trữ."""
    db = _load_db()
    if username not in db:
        print(f"[embedding] Không tìm thấy '{username}'")
        return False

    img_path = db[username].get("img_path", "")
    if os.path.exists(img_path):
        os.remove(img_path)

    del db[username]
    _save_db(db)
    print(f"[embedding] Đã xóa '{username}'")
    return True


def list_users() -> list[str]:
    """Trả về danh sách tên người dùng đã đăng ký."""
    db = _load_db()
    return list(db.keys())


def get_embeddings_db() -> dict:
    """Trả về toàn bộ database embeddings."""
    return _load_db()