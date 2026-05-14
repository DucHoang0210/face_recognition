# pyrefly: ignore [missing-import]
from fastapi import FastAPI, File, UploadFile, Form
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import time

# Import từ các thư mục cũ của bạn
from modules.face.embedding import add_user
from modules.face.recognition import recognize_from_frame
from config.settings import TEMP_DIR

app = FastAPI(title="Face Recognition API")

# Cấu hình CORS để cho phép React (Frontend) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong thực tế nên đổi thành ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo thư mục temp nếu chưa có
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/api/face/register")
async def register_face(
    username: str = Form(...), 
    file: UploadFile = File(...)
):
    """API lưu khuôn mặt người dùng mới"""
    # Đọc file ảnh gửi lên
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"success": False, "message": "File ảnh không hợp lệ."}

    # Lưu ảnh tạm thời
    temp_path = os.path.join(TEMP_DIR, f"temp_register_{int(time.time()*1000)}.jpg")
    cv2.imwrite(temp_path, img)

    try:
        # Tái sử dụng hàm add_user của bạn
        is_success = add_user(username, temp_path)
        
        if is_success:
            return {"success": True, "message": f"Khuôn mặt của {username} đã được lưu."}
        else:
            return {"success": False, "message": "Không phát hiện thấy khuôn mặt trong ảnh!"}
    finally:
        # Xóa file tạm
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/face/recognize")
async def recognize_face_endpoint(file: UploadFile = File(...)):
    """API nhận diện khuôn mặt"""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"success": False, "message": "File ảnh không hợp lệ."}

    # Gọi hàm nhận diện từ code cũ của bạn
    result = recognize_from_frame(img)
    return result
