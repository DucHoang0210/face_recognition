# pyrefly: ignore [missing-import]
import sys
import io
# Configure UTF-8 encoding for standard output and error to support emojis on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, File, UploadFile, Form
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import time

# Import từ các thư mục của bạn
from modules.face.embedding import add_user
from modules.face.recognition import recognize_face, recognize_from_frame
from modules.database.db import save_image, init_db
from modules.image.hash import hash_image
from config.settings import TEMP_DIR, FACES_DIR

app = FastAPI(title="Face Recognition API")

# Cấu hình CORS để cho phép React (Frontend) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo thư mục temp nếu chưa có
os.makedirs(TEMP_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    # Khởi tạo kết nối và các bảng cơ sở dữ liệu PostgreSQL
    init_db()

@app.post("/api/face/register")
async def register_face(
    username: str = Form(...), 
    file: UploadFile = File(...)
):
    """API lưu khuôn mặt người dùng mới & kiểm tra KYC chống trùng mặt"""
    # Đọc file ảnh gửi lên
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"success": False, "message": "File ảnh không hợp lệ."}

    # Lưu ảnh tạm thời để thực hiện nhận dạng kiểm tra KYC
    temp_path = os.path.join(TEMP_DIR, f"temp_register_{int(time.time()*1000)}.jpg")
    cv2.imwrite(temp_path, img)

    try:
        # 1️⃣ Kiểm tra KYC: Khuôn mặt này đã được người khác đăng ký chưa?
        recognize_result = recognize_face(temp_path)
        if recognize_result["success"]:
            matched_user = recognize_result["username"]
            if matched_user != username:
                return {
                    "success": False, 
                    "message": f"KYC thất bại: Khuôn mặt này đã được đăng ký bởi tài khoản '{matched_user}' trước đó!"
                }

        # 2️⃣ Nếu mặt hợp lệ (chưa ai đăng ký hoặc trùng với chính mình), tiến hành đăng ký
        is_success = add_user(username, temp_path)
        
        if is_success:
            # 3️⃣ Lưu thông tin ảnh khuôn mặt vào PostgreSQL db
            # Đường dẫn ảnh chính thức sau khi add_user thành công: FACES_DIR/username.jpg
            dest_path = os.path.join(FACES_DIR, f"{username}.jpg")
            img_hash = hash_image(dest_path) if os.path.exists(dest_path) else hash_image(temp_path)
            
            db_success = save_image(username, dest_path if os.path.exists(dest_path) else temp_path, img_hash)
            
            if db_success:
                return {
                    "success": True, 
                    "message": f"Khuôn mặt của {username} đã được lưu và đồng bộ cơ sở dữ liệu PostgreSQL."
                }
            else:
                return {
                    "success": True, 
                    "message": f"Đăng ký khuôn mặt của {username} thành công nhưng lỗi khi ghi nhận vào DB PostgreSQL."
                }
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=5678, reload=False)
