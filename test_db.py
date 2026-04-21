import mysql.connector

print("Connecting...")

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="123456",
    port=3306,
    connection_timeout=5
)

print("OK CONNECTED")