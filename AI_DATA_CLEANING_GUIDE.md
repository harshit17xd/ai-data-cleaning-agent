# 🤖 AI Data Cleaning with Dynamic Database Support

## ✅ What Just Got Fixed

Your sample data with these issues has been added to `data/sample_data.csv`:
- ❌ Invalid ages (text: "twenty five")
- ❌ Invalid emails (missing @, double @@)
- ❌ Invalid phone numbers (contains letters)
- ❌ Missing values
- ❌ Invalid salaries (text: "not_available")
- ❌ Invalid dates (13-01, 06-31)
- ❌ Duplicate records
- ❌ Unknown departments

## 🚀 How to Use

### Option 1: Test with Sample Data (Recommended First)
```bash
# Go to scripts folder
cd scripts

# Run the AI cleaning test
python test_ai_cleaning.py
```

**Output:**
- Loads: `data/sample_data.csv`
- Shows original issues
- Applies basic cleaning
- **Sends to LLM for intelligent fixing**
- Saves result: `data/sample_data_cleaned.csv`

### Option 2: Use in main.py (Any Database)
```python
from ai_agent import AIAgent
from data_cleaning import DataCleaning
import pandas as pd

# Load ANY data (CSV, Excel, Database, API)
df = pd.read_csv("your_file.csv")

# Clean it
cleaner = DataCleaning()
df_basic = cleaner.clean_data(df)

# Smart AI fixing (any schema)
ai_agent = AIAgent()
df_cleaned = ai_agent.process_data(df_basic)

print(df_cleaned)
```

### Option 3: Use via FastAPI Backend
```bash
# Start backend
cd scripts
uvicorn backend:app --reload

# Upload any CSV/Excel via http://127.0.0.1:8000/docs
# Click /clean-data endpoint
# Upload file + enable "Use Agentic AI cleaning"
```

### Option 4: Use via Streamlit Frontend
```bash
streamlit run app/app.py

# Upload CSV/Excel
# Select "Use Agentic AI cleaning"
# Click "Clean Data"
```

## 🎯 Features

✅ **Dynamic Schema Support** - Works with ANY columns, ANY data type
✅ **Email Validation** - Fixes @, double @@, missing domains
✅ **Phone Validation** - Removes letters, keeps 10 digits
✅ **Date Parsing** - Converts any format to YYYY-MM-DD, fixes invalid dates
✅ **Salary Cleaning** - Converts text to numbers
✅ **Age Validation** - Converts text to numbers, removes invalid ranges
✅ **Duplicate Removal** - Automatic duplicate detection
✅ **Missing Value Handling** - Smart imputation or nulls
✅ **Text Normalization** - Fixes capitalization, whitespace
✅ **Range Validation** - Removes impossible values

## 📋 What the AI Agent Does

The LLM receives detailed instructions to:
1. Detect ALL data quality issues
2. Fix them intelligently based on column names
3. Return proper JSON with cleaned data
4. Keep valid rows, fix invalid ones
5. Handle any schema automatically

## ⚠️ Important: Set Your OpenAI API Key

### 1. Copy template
```bash
copy .env.example .env
```

### 2. Edit `.env` file
```
DB_PASSWORD=your_db_password
OPENAI_API_KEY=sk-your-actual-openai-key
```

### 3. Get OpenAI Key
- Go to https://platform.openai.com/account/api-keys
- Create new API key
- Copy it to `.env`

## 🧪 Testing

```bash
# Test with your problematic data
python scripts/test_ai_cleaning.py

# Before: 10 rows with issues
# After: Cleaned data WITHOUT issues
```

## 📊 For ANY Dynamic Database

Just load your data and pass to AIAgent:

```python
# From PostgreSQL
engine = create_engine("postgresql://...")
df = pd.read_sql("SELECT * FROM your_table", engine)

# From MySQL
engine = create_engine("mysql+pymysql://...")
df = pd.read_sql("SELECT * FROM your_table", engine)

# From API
response = requests.get("your_api_endpoint")
df = pd.DataFrame(response.json())

# From Excel/CSV
df = pd.read_csv("file.csv")
df = pd.read_excel("file.xlsx")

# Clean ALL of them the same way
ai_agent = AIAgent()
df_cleaned = ai_agent.process_data(df)
```

## ✨ That's It!

Your data cleaning is now **fully automated with AI** for ANY database! 🎉
