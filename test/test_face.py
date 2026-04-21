from deepface import DeepFace
import traceback

print("=== TEST NHẬN DẠNG KHUÔN MẶT ===")

try:
    result = DeepFace.verify(
        img1_path="face1.jpg",
        img2_path="face2.jpg",
        model_name="ArcFace",   # 🔥 đổi sang cái này
        detector_backend="opencv",
        enforce_detection=True
    )

    print("\n✅ KẾT QUẢ SO SÁNH:")
    print("   Cùng một người không?", result["verified"])
    print("   Độ giống (distance):", round(result["distance"], 4))

except Exception as e:
    print("❌ LỖI khi chạy:")
    print(traceback.format_exc())