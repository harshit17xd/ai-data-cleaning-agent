import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =========================
# 🔹 DATABASE CONFIG
# =========================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "euron_ai_agent")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "fresh@12345")     
# =========================
# 🔹 CONNECT + TEST
# =========================
try:
    # Connect to PostgreSQL
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    cursor = connection.cursor()

    print("✅ PostgreSQL Connection Successful!")

    # =========================
    # 🔹 FETCH TABLES
    # =========================
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)

    tables = cursor.fetchall()

    print("\n📊 Tables in the database:")
    for table in tables:
        print("👉", table[0])

    # =========================
    # 🔹 FETCH DATA FROM my_table
    # =========================
    cursor.execute("SELECT * FROM my_table;")
    rows = cursor.fetchall()

    print("\n📄 Data from my_table:")
    for row in rows:
        print(row)

    # =========================
    # 🔹 CLOSE CONNECTION
    # =========================
    cursor.close()
    connection.close()

    print("\n🔒 Connection Closed.")

except Exception as e:
    print(f"\n❌ Error connecting to PostgreSQL: {e}")