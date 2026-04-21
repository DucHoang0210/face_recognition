import cv2
import os
import time
from config.settings import TEMP_DIR, CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


def capture_face(save_path: str = None, show_preview: bool = False) -> str | None:
    """
    Chụp ảnh khuôn mặt từ webcam.
    
    Args:
        save_path: Đường dẫn lưu ảnh. Mặc định lưu vào TEMP_DIR/capture_<timestamp>.jpg
        show_preview: Hiển thị cửa sổ preview (dùng cho debug)
    
    Returns:
        Đường dẫn ảnh đã lưu, hoặc None nếu thất bại
    """
    if save_path is None:
        timestamp = int(time.time())
        save_path = os.path.join(TEMP_DIR, f"capture_{timestamp}.jpg")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    print("Camera opened:", cap.isOpened())
    if not cap.isOpened():
        raise RuntimeError("Không mở được camera")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # Làm ấm camera (bỏ qua vài frame đầu cho ổn định ánh sáng)
    for _ in range(5):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("[capture] Không thể đọc frame từ webcam!")
        return None

    # Kiểm tra sơ bộ có khuôn mặt không (dùng Haar cascade nhanh)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade_path = os.path.join(os.path.dirname(__file__), "../../haarcascade/haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    if len(faces) == 0:
        print("[capture] Không phát hiện khuôn mặt trong frame!")
        return None

    cv2.imwrite(save_path, frame)
    print(f"[capture] Đã lưu ảnh: {save_path}")
    return save_path


def capture_multiple(username: str, count: int = 5, delay: float = 0.5) -> list[str]:
    """
    Chụp nhiều ảnh để đăng ký người dùng mới (tăng độ chính xác embedding).

    Args:
        username: Tên người dùng
        count: Số ảnh cần chụp
        delay: Khoảng cách giữa các lần chụp (giây)

    Returns:
        Danh sách đường dẫn ảnh đã lưu
    """
    user_dir = os.path.join(os.path.dirname(TEMP_DIR), "faces")
    os.makedirs(user_dir, exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    print("Camera opened:", cap.isOpened())
    if not cap.isOpened():
        print("[capture] Không thể mở webcam!")
        return []

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # Làm ấm camera
    for _ in range(5):
        cap.read()

    cascade_path = os.path.join(os.path.dirname(__file__), "../../haarcascade/haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)

    saved_paths = []
    attempt = 0
    max_attempts = count * 10

    while len(saved_paths) < count and attempt < max_attempts:
        ret, frame = cap.read()
        attempt += 1
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) > 0:
            path = os.path.join(user_dir, f"{username}_{len(saved_paths)+1}.jpg")
            cv2.imwrite(path, frame)
            saved_paths.append(path)
            print(f"[capture] Ảnh {len(saved_paths)}/{count}: {path}")
            time.sleep(delay)

    cap.release()
    print(f"[capture] Đã chụp {len(saved_paths)} ảnh cho '{username}'")
    return saved_paths


def get_frame_generator():
    """
    Generator trả về từng frame từ webcam (dùng cho live preview trong Tkinter).
    Gọi next() để lấy frame kế tiếp, gọi .close() để đóng camera.
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    print("Camera opened:", cap.isOpened())
    if not cap.isOpened():
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    cascade_path = os.path.join(os.path.dirname(__file__), "../../haarcascade/haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Vẽ bounding box quanh khuôn mặt
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 100), 2)

            yield frame
    finally:
        cap.release()