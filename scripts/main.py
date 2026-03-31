from data_ingestions import DataIngestion
from data_cleaning import DataCleaning
from ai_agent import AIAgent

# =========================
# 🔹 DATABASE CONFIG
# =========================
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "euron_ai_agent"
DB_USER = "postgres"
DB_PASSWORD = "fresh@12345"

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# =========================
# 🔹 INITIALIZE COMPONENTS
# =========================
ingestion = DataIngestion(DB_URL)
cleaner = DataCleaning()
ai_agent = AIAgent()

# =========================
# 🔹 1. LOAD + CLEAN CSV
# =========================
df_csv = ingestion.load_csv("sample_data.csv")

if df_csv is not None:
    print("\n🔹 Cleaning CSV Data...")
    df_csv = cleaner.clean_data(df_csv)
    df_csv = ai_agent.process_data(df_csv)
    print("\n✅ AI-Cleaned CSV Data:\n", df_csv)


# =========================
# 🔹 2. LOAD + CLEAN EXCEL
# =========================
df_excel = ingestion.load_excel("sample_data.xlsx")

if df_excel is not None:
    print("\n🔹 Cleaning Excel Data...")
    df_excel = cleaner.clean_data(df_excel)
    df_excel = ai_agent.process_data(df_excel)
    print("\n✅ AI-Cleaned Excel Data:\n", df_excel)


# =========================
# 🔹 3. LOAD + CLEAN DATABASE
# =========================
df_db = ingestion.load_from_database("SELECT * FROM my_table")  # change table name

if df_db is not None:
    print("\n🔹 Cleaning Database Data...")
    df_db = cleaner.clean_data(df_db)
    df_db = ai_agent.process_data(df_db)
    print("\n✅ AI-Cleaned Database Data:\n", df_db)


# =========================
# 🔹 4. FETCH + CLEAN API DATA
# =========================
API_URL = "https://jsonplaceholder.typicode.com/posts"

df_api = ingestion.fetch_from_api(API_URL)

if df_api is not None:
    print("\n🔹 Cleaning API Data...")

    # Limit rows (important for LLM)
    df_api = df_api.head(30)

    # Reduce long text fields
    if "body" in df_api.columns:
        df_api["body"] = df_api["body"].apply(
            lambda x: x[:100] + "..." if isinstance(x, str) else x
        )

    df_api = cleaner.clean_data(df_api)
    df_api = ai_agent.process_data(df_api)

    print("\n✅ AI-Cleaned API Data:\n", df_api)