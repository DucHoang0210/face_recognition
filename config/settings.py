import os

# Đường dẫn gốc project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Đường dẫn dữ liệu
FACES_DIR = os.path.join(BASE_DIR, "data", "faces")
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "data", "embeddings", "embeddings.json")
LOGS_PATH = os.path.join(BASE_DIR, "data", "logs", "login_log.json")

# Tạo thư mục nếu chưa tồn tại
for path in [FACES_DIR, TEMP_DIR,
             os.path.dirname(EMBEDDINGS_PATH),
             os.path.dirname(LOGS_PATH)]:
    os.makedirs(path, exist_ok=True)

# Cấu hình DeepFace
DEEPFACE_MODEL = "Facenet"          # Facenet / VGG-Face / ArcFace
DEEPFACE_DETECTOR = "opencv"        # opencv / retinaface / mtcnn
DEEPFACE_DISTANCE = "cosine"        # cosine / euclidean
SIMILARITY_THRESHOLD = 0.50         # Ngưỡng nhận diện (cosine: càng nhỏ càng giống, tăng lên để nhạy hơn)

# Cấu hình webcam
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Cấu hình UI
APP_TITLE = "Hệ Thống Nhận Diện Khuôn Mặt"
APP_WIDTH = 1000
APP_HEIGHT = 650

# Cấu hình watermark
WATERMARK_TEXT = "Bản quyền số"
WATERMARK_POSITION = "bottom_right"
WATERMARK_OPACITY = 128  # 0-255

# Cấu hình hash
IMAGE_DIR = "data/images/"
HASH_DIR = "data/hashes/"