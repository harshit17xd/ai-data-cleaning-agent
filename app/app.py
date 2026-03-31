import streamlit as st
import requests
import pandas as pd
import json
from io import StringIO

# ==============================
# 🔹 FASTAPI BACKEND URL
# ==============================
FASTAPI_URL = "http://127.0.0.1:8000"

# ==============================
# 🔹 STREAMLIT CONFIG
# ==============================
st.set_page_config(page_title="AI-Powered Data Cleaning", layout="wide")

# ==============================
# 🔹 SIDEBAR
# ==============================
st.sidebar.header("📊 Data Source Selection")

data_source = st.sidebar.radio(
    "Select Data Source:",
    ["CSV/Excel", "Database Query", "API Data"],
    index=0
)

# ==============================
# 🔹 MAIN TITLE
# ==============================
st.markdown("""
# 🚀 AI-Powered Data Cleaning  
Clean your data effortlessly using AI-powered processing!
""")

# ==============================
# 🔹 CSV / EXCEL HANDLING
# ==============================
if data_source == "CSV/Excel":

    st.subheader("📂 Upload File for Cleaning")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1]

        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("### 🔍 Raw Data Preview:")
        st.dataframe(df)

        if st.button("🚀 Clean Data"):
            try:
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue())
                }

                response = requests.post(
                    f"{FASTAPI_URL}/clean-data",
                    files=files
                )

                if response.status_code == 200:

                    st.subheader("🔍 Raw API Response (Debugging)")
                    st.json(response.json())

                    # Parse response
                    cleaned_data_raw = response.json()["cleaned_data"]

                    if isinstance(cleaned_data_raw, str):
                        cleaned_data = pd.DataFrame(json.loads(cleaned_data_raw))
                    else:
                        cleaned_data = pd.DataFrame(cleaned_data_raw)

                    st.subheader("✅ Cleaned Data:")
                    st.dataframe(cleaned_data)

                else:
                    st.error("❌ Failed to clean data.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ==============================
# 🔹 DATABASE HANDLING
# ==============================
elif data_source == "Database Query":

    st.subheader("🛢️ Database Query Cleaning")

    db_url = st.text_input("Enter Database URL")
    query = st.text_area("Enter SQL Query", "SELECT * FROM my_table")

    if st.button("🚀 Fetch & Clean Data"):
        try:
            response = requests.post(
                f"{FASTAPI_URL}/clean-db",
                json={"db_url": db_url, "query": query}
            )

            if response.status_code == 200:
                cleaned_data = pd.DataFrame(response.json()["cleaned_data"])

                st.subheader("✅ Cleaned Data:")
                st.dataframe(cleaned_data)

            else:
                st.error("❌ Failed to fetch/clean data.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ==============================
# 🔹 API HANDLING
# ==============================
elif data_source == "API Data":

    st.subheader("🌐 Fetch Data from API")

    api_url = st.text_input(
        "Enter API Endpoint:",
        "https://jsonplaceholder.typicode.com/posts"
    )

    if st.button("🚀 Fetch & Clean Data"):
        try:
            response = requests.post(
                f"{FASTAPI_URL}/clean-api",
                json={"api_url": api_url}
            )

            if response.status_code == 200:
                cleaned_data = pd.DataFrame(response.json()["cleaned_data"])

                st.subheader("✅ Cleaned Data:")
                st.dataframe(cleaned_data)

            else:
                st.error("❌ Failed to fetch data from API.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")