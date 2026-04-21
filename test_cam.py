import cv2

def test_camera(index=0):
    print(f"Testing camera index {index}...")

    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Không mở được camera!")
        return

    print("✅ Camera mở thành công!")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Không đọc được frame!")
            break

        cv2.imshow("Camera Test", frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC để thoát
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # thử lần lượt
    for i in range(3):
        test_camera(i)