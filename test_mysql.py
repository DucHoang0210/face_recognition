import mysql.connector
import time

print("🚀 Start test...")

try:
    print("👉 Connecting...")
    start = time.time()

    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="123456",
        connection_timeout=3
    )

    print("⏱ Time:", time.time() - start)
    print("✅ CONNECT OK")

    conn.close()

except Exception as e:
    print("❌ ERROR:", e)