import psycopg2
from psycopg2 import Error

# ================= CONFIG (PostgreSQL matching Java Spring Boot) =================
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "postgres",
    "password": "123456",
    "database": "faceid_db",
    "port": 5432
}

# ================= GLOBAL CONNECTION =================
conn_global = None


# ================= CONNECTION =================
def get_connection():
    global conn_global

    # 👉 Nếu đã có connection thì dùng lại
    try:
        if conn_global and not conn_global.closed:
            return conn_global
    except:
        pass

    print("🔌 DB: connecting to PostgreSQL...")

    try:
        conn_global = psycopg2.connect(**DB_CONFIG)
        conn_global.autocommit = True
        print("✅ DB: connected to PostgreSQL")
        return conn_global

    except Error as e:
        print("❌ Lỗi kết nối PostgreSQL:", e)
        return None


# ================= INIT DB =================
def init_db():
    print("🔥 DB: start init (PostgreSQL)")

    conn = get_connection()
    if conn is None:
        print("❌ DB: connection failed")
        return

    try:
        cursor = conn.cursor()

        # Tạo bảng users nếu chưa có (Mặc dù Java Spring Boot (Hibernate) đã tự động sinh)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) DEFAULT '',
            has_face_data BOOLEAN DEFAULT FALSE,
            wallet_address VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tạo bảng images để lưu thông tin ảnh và hash bản quyền
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            user_id INT,
            file_path TEXT,
            hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        print("🔥 DB: done initializing PostgreSQL tables")

    except Exception as e:
        print("🔥 DB ERROR:", e)

    finally:
        cursor.close()
        # ❌ KHÔNG close conn_global để tối ưu hoá kết nối


# ================= USER =================
def save_user(username):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        # Dùng ON CONFLICT của PostgreSQL
        cursor.execute(
            "INSERT INTO users(username, password_hash, has_face_data) VALUES (%s, '', false) ON CONFLICT (username) DO NOTHING",
            (username,)
        )

        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )

        row = cursor.fetchone()
        return row[0] if row else None

    except Error as e:
        print("❌ save_user error:", e)
        return None

    finally:
        cursor.close()


def get_users():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        return [row[0] for row in cursor.fetchall()]

    except Error as e:
        print("❌ get_users error:", e)
        return []

    finally:
        cursor.close()


# ================= IMAGE =================
def save_image(username, path, img_hash):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            # Tạo người dùng mới nếu chưa có
            user_id = save_user(username)
            if not user_id:
                print("❌ User không tồn tại và không thể tạo mới")
                return False
        else:
            user_id = row[0]

        # Lưu ảnh mới
        cursor.execute("""
            INSERT INTO images(user_id, file_path, hash)
            VALUES (%s, %s, %s)
        """, (user_id, path, img_hash))

        # Đồng thời cập nhật trạng thái đã có FaceID của user
        cursor.execute("""
            UPDATE users SET has_face_data = true WHERE id = %s
        """, (user_id,))

        return True

    except Error as e:
        print("❌ save_image error:", e)
        return False

    finally:
        cursor.close()


def get_images_by_user(username):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, hash, created_at 
            FROM images 
            JOIN users ON users.id = images.user_id
            WHERE users.username = %s
            ORDER BY created_at DESC
        """, (username,))

        return cursor.fetchall()

    except Error as e:
        print("❌ get_images_by_user error:", e)
        return []

    finally:
        cursor.close()