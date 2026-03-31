import streamlit as st
import requests
import pandas as pd
import json

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


def render_basic_visualization(df, key_prefix):
    """Renders a simple, safe chart for available numeric columns."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    st.subheader("📈 Visualization")
    if not numeric_cols:
        st.info("Unable to display visualization: no numeric columns found after cleaning.")
        return

    if len(numeric_cols) == 1:
        y_col = numeric_cols[0]
        st.bar_chart(df[[y_col]])
        return

    x_col = st.selectbox("X-axis", options=numeric_cols, key=f"{key_prefix}_x")
    y_options = [col for col in numeric_cols if col != x_col]
    y_col = st.selectbox("Y-axis", options=y_options, key=f"{key_prefix}_y")

    chart_df = df[[x_col, y_col]].dropna()
    if chart_df.empty:
        st.info("Unable to display visualization: selected columns do not contain chartable values.")
        return

    st.line_chart(chart_df.set_index(x_col))

# ==============================
# 🔹 CSV / EXCEL HANDLING
# ==============================
if data_source == "CSV/Excel":

    st.subheader("📂 Upload File for Cleaning")

    use_ai_cleaning = st.checkbox(
        "Use Agentic AI cleaning (slower, needs Groq/OpenAI key)",
        value=False,
        help="Turn this on to enable AI agent processing after basic cleaning."
    )

    user_cleaning_prompt = ""
    if use_ai_cleaning:
        user_cleaning_prompt = st.text_area(
            "Cleaning Prompt (sent to LLM)",
            value="",
            height=120,
            placeholder=(
                "Example: fix emails/phones/dates, convert text ages to numbers."
            ),
            help="This prompt is sent to the LLM only when Agentic AI cleaning is enabled."
        )

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
                data = {
                    "use_ai": str(use_ai_cleaning).lower(),
                    "cleaning_prompt": user_cleaning_prompt.strip() if use_ai_cleaning else ""
                }

                response = requests.post(
                    f"{FASTAPI_URL}/clean-data",
                    files=files,
                    data=data
                )

                if response.status_code == 200:

                    payload = response.json()
                    cleaned_data_raw = payload.get("cleaned_data", payload.get("preview", []))

                    if isinstance(cleaned_data_raw, str):
                        cleaned_data = pd.DataFrame(json.loads(cleaned_data_raw))
                    else:
                        cleaned_data = pd.DataFrame(cleaned_data_raw)

                    st.subheader("✅ Cleaned Data:")
                    st.dataframe(cleaned_data)
                    st.caption(
                        f"Input Rows: {payload.get('input_rows', 'NA')} | "
                        f"Rows: {payload.get('rows', len(cleaned_data))} | "
                        f"Columns: {len(payload.get('columns', cleaned_data.columns))}"
                    )
                    if use_ai_cleaning:
                        if payload.get("ai_applied"):
                            st.success(payload.get("ai_message", "Agentic AI cleaning was applied."))
                        else:
                            st.warning(payload.get("ai_message", "Agentic AI was requested but not applied."))
                        with st.expander("🧠 LLM Debug (prompt + raw response)", expanded=False):
                            st.markdown(f"**Model:** {payload.get('llm_model', 'None')}")
                            llm_error = payload.get("llm_error", "")
                            if llm_error:
                                st.error(f"LLM Error: {llm_error}")
                            st.markdown("**Prompt sent to LLM:**")
                            st.code(payload.get("llm_prompt", ""), language="text")
                            st.markdown("**Raw LLM response:**")
                            st.code(payload.get("llm_response", ""), language="text")
                        prompt_rules = payload.get("prompt_rules_applied", [])
                        if prompt_rules:
                            st.info("Prompt rules applied: " + " | ".join(prompt_rules))
                        prompt_rules_message = payload.get("prompt_rules_message", "")
                        if prompt_rules_message:
                            st.warning(prompt_rules_message)
                    else:
                        st.info("Basic rule-based cleaning mode was used.")
                        prompt_rules = payload.get("prompt_rules_applied", [])
                        if prompt_rules:
                            st.info("Prompt rules applied: " + " | ".join(prompt_rules))
                        prompt_rules_message = payload.get("prompt_rules_message", "")
                        if prompt_rules_message:
                            st.warning(prompt_rules_message)
                    render_basic_visualization(cleaned_data, "file_clean")

                else:
                    st.error(f"❌ Failed to clean data. {response.text}")

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
                payload = response.json()
                cleaned_data = pd.DataFrame(payload.get("cleaned_data", []))

                st.subheader("✅ Cleaned Data:")
                st.dataframe(cleaned_data)
                render_basic_visualization(cleaned_data, "db_clean")

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
                payload = response.json()
                cleaned_data = pd.DataFrame(payload.get("cleaned_data", []))

                st.subheader("✅ Cleaned Data:")
                st.dataframe(cleaned_data)
                render_basic_visualization(cleaned_data, "api_clean")

            else:
                st.error("❌ Failed to fetch data from API.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")