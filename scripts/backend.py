import sys
import os
import pandas as pd
import io
import aiohttp
import json
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from sqlalchemy import create_engine
from pydantic import BaseModel

# Ensure scripts folder is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import custom modules
from scripts.ai_agent import AIAgent
from scripts.data_cleaning import DataCleaning

app = FastAPI()

# ==============================
# Initialize Agents
# ==============================
ai_agent = AIAgent()
cleaner = DataCleaning()


def run_ai_cleaning(df: pd.DataFrame, user_prompt: str = "") -> tuple:
    """
    Runs AI cleaning with robust fallback to rule-cleaned data.
    Returns: (cleaned_df, ai_status_dict)
    """
    ai_status = {
        "ai_enabled": ai_agent.enabled,
        "ai_applied": False,
        "ai_message": "",
        "llm_model": getattr(ai_agent, "model_name", "None"),
        "llm_prompt": "",
        "llm_response": "",
        "llm_error": ""
    }
    
    if not ai_agent.enabled:
        ai_status["ai_message"] = "❌ AI disabled: No valid LLM key found (Groq/OpenAI)."
        print(ai_status["ai_message"])
        return df, ai_status
    
    try:
        print("\n" + "="*60)
        print("🤖 STARTING AI CLEANING...")
        print("="*60)
        print(f"Input rows: {len(df)}")
        print(f"Columns: {list(df.columns)}\n")
        
        ai_result = ai_agent.process_data(df, user_instructions=user_prompt)
        # Attach latest LLM debug info (best-effort)
        ai_status["llm_prompt"] = getattr(ai_agent, "last_prompt", "")
        ai_status["llm_response"] = getattr(ai_agent, "last_response", "")
        ai_status["llm_error"] = getattr(ai_agent, "last_error", "")

        if isinstance(ai_result, pd.DataFrame):
            if not ai_result.empty:
                ai_status["ai_applied"] = True
                model_name = getattr(ai_agent, "model_name", "LLM")
                ai_status["ai_message"] = f"✅ AI cleaning completed ({model_name}): {len(df)} → {len(ai_result)} rows"
                print(f"\n{ai_status['ai_message']}")
                return ai_result, ai_status
            else:
                ai_status["ai_message"] = "⚠️ AI returned empty result, using basic cleaning"
                print(ai_status["ai_message"])
                return df, ai_status

        ai_status["ai_message"] = "⚠️ AI output format invalid, using original data"
        return df, ai_status
        
    except Exception as e:
        ai_status["ai_message"] = f"❌ AI cleaning error: {str(e)[:100]}"
        print(f"\n{ai_status['ai_message']}")
        print(f"Full error: {e}")
        return df, ai_status


def dataframe_to_json_records(df: pd.DataFrame):
    """
    Converts DataFrame into JSON-safe records (no NaN/Inf values).
    """
    safe_df = df.copy()
    safe_df = safe_df.replace([np.inf, -np.inf], np.nan)
    # Normalize pandas missing values to None for JSON serialization
    safe_df = safe_df.astype(object).where(pd.notnull(safe_df), None)
    safe_df = safe_df.replace({pd.NA: None, np.nan: None})
    return safe_df.to_dict(orient="records")


@app.get("/")
async def root():
    return {
        "message": "AI Data Cleaning backend is running",
        "docs": "/docs",
        "endpoints": ["/clean-data", "/clean-db", "/clean-api", "/health"]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

# ==============================
# CSV / Excel Cleaning Endpoint
# ==============================
@app.post("/clean-data")
async def clean_data(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    cleaning_prompt: str = Form("")
):
    """
    Receives file from UI, cleans it using rule-based & AI methods, returns cleaned JSON.
    """
    try:
        contents = await file.read()
        file_extension = file.filename.split(".")[-1].lower()

        # Load file into DataFrame
        if file_extension == "csv":
            try:
                df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(contents.decode("latin-1")))
        elif file_extension == "xlsx":
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")

        input_rows = len(df)

        # Step 1: Rule-Based Cleaning
        df_cleaned = cleaner.clean_data(df)

        # Step 2: Optional AI Cleaning
        final_df = df_cleaned
        ai_meta = {
            "ai_enabled": False,
            "ai_applied": False,
            "ai_message": "Basic rule-based cleaning applied (AI not requested)"
        }
        
        if use_ai:
            df_ai_cleaned, ai_meta = run_ai_cleaning(df_cleaned, user_prompt=cleaning_prompt)
            if isinstance(df_ai_cleaned, pd.DataFrame) and not df_ai_cleaned.empty:
                final_df = df_ai_cleaned

        # Enforce strict validations so UI always shows cleaned output
        final_df = cleaner.enforce_strict_rules(final_df)

        return {
            "status": "success",
            "input_rows": input_rows,
            "rows": int(len(final_df)),
            "columns": [str(col) for col in final_df.columns],
            "cleaned_data": dataframe_to_json_records(final_df),
            "preview": dataframe_to_json_records(final_df.head(10)),
            "ai_enabled": ai_meta["ai_enabled"],
            "ai_applied": ai_meta["ai_applied"],
            "ai_message": ai_meta["ai_message"],
            "llm_model": ai_meta.get("llm_model", "None"),
            "llm_prompt": ai_meta.get("llm_prompt", ""),
            "llm_response": ai_meta.get("llm_response", ""),
            "llm_error": ai_meta.get("llm_error", ""),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ==============================
# Database Cleaning Endpoint
# ==============================
class DBQuery(BaseModel):
    db_url: str
    query: str


@app.post("/clean-db")
async def clean_db(query: DBQuery):
    """
    Fetches data from database, cleans it using AI, and returns cleaned JSON.
    """
    try:
        engine = create_engine(query.db_url)
        df = pd.read_sql(query.query, engine)

        # Rule-based cleaning
        df_cleaned = cleaner.clean_data(df)

        # AI cleaning (with fallback)
        df_ai_cleaned, ai_meta = run_ai_cleaning(df_cleaned)
        final_df = cleaner.enforce_strict_rules(df_ai_cleaned)

        return {
            "cleaned_data": dataframe_to_json_records(final_df),
            "ai_enabled": ai_meta["ai_enabled"],
            "ai_applied": ai_meta["ai_applied"],
            "ai_message": ai_meta["ai_message"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from database: {str(e)}")


# ==============================
# API Data Cleaning Endpoint
# ==============================
class APIRequest(BaseModel):
    api_url: str


@app.post("/clean-api")
async def clean_api(api_request: APIRequest):
    """
    Fetches data from an API, cleans it using AI, and returns cleaned JSON.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_request.api_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to fetch data from API.")

                data = await response.json()

        # Convert API response to DataFrame
        df = pd.DataFrame(data)

        # Rule-based cleaning
        df_cleaned = cleaner.clean_data(df)

        # AI cleaning (with fallback)
        df_ai_cleaned, ai_meta = run_ai_cleaning(df_cleaned)
        final_df = cleaner.enforce_strict_rules(df_ai_cleaned)

        return {
            "cleaned_data": dataframe_to_json_records(final_df),
            "ai_enabled": ai_meta["ai_enabled"],
            "ai_applied": ai_meta["ai_applied"],
            "ai_message": ai_meta["ai_message"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing API data: {str(e)}")


# ==============================
# Run Server
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)