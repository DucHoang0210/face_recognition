import mysql.connector
from mysql.connector import Error

# ================= CONFIG =================
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "123456",
    "database": "faceid",
    "port": 3306,
    "connection_timeout": 5,
    "autocommit": True,
    "use_pure": True
}

# ================= GLOBAL CONNECTION =================
conn_global = None


# ================= CONNECTION =================
def get_connection():
    global conn_global

    # 👉 Nếu đã có connection thì dùng lại
    try:
        if conn_global and conn_global.is_connected():
            return conn_global
    except:
        pass

    print("🔌 DB: connecting...")

    try:
        conn_global = mysql.connector.connect(**DB_CONFIG)
        print("✅ DB: connected")
        return conn_global

    except Error as e:
        print("❌ Lỗi kết nối MySQL:", e)
        return None


# ================= INIT DB =================
def init_db():
    print("🔥 DB: start init")

    conn = get_connection()
    if conn is None:
        print("❌ DB: connection failed")
        return

    try:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            file_path TEXT,
            hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        print("🔥 DB: done")

    except Exception as e:
        print("🔥 DB ERROR:", e)

    finally:
        cursor.close()
        # ❌ KHÔNG close conn_global


# ================= USER =================
def save_user(username):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT IGNORE INTO users(username) VALUES (%s)",
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
            print("❌ User không tồn tại")
            return False

        user_id = row[0]

        cursor.execute("""
            INSERT INTO images(user_id, file_path, hash)
            VALUES (%s, %s, %s)
        """, (user_id, path, img_hash))

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