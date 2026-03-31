import sys
import os
import pandas as pd
import io
import aiohttp
import json
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException
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


def run_ai_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs AI cleaning with robust fallback to rule-cleaned data.
    """
    try:
        ai_result = ai_agent.process_data(df)

        if isinstance(ai_result, pd.DataFrame):
            return ai_result

        if isinstance(ai_result, str):
            text = ai_result.strip()
            try:
                if text.startswith("[") or text.startswith("{"):
                    parsed = json.loads(text)
                    parsed_df = pd.DataFrame(parsed)
                    if not parsed_df.empty:
                        return parsed_df
            except Exception:
                pass

            try:
                parsed_df = pd.read_csv(io.StringIO(text))
                if not parsed_df.empty:
                    return parsed_df
            except Exception:
                pass

        return df
    except Exception:
        return df


def dataframe_to_json_records(df: pd.DataFrame):
    """
    Converts DataFrame into JSON-safe records (no NaN/Inf values).
    """
    safe_df = df.replace([np.inf, -np.inf], np.nan).where(pd.notnull(df), None)
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
async def clean_data(file: UploadFile = File(...)):
    """
    Receives file from UI, cleans it using rule-based & AI methods, returns cleaned JSON.
    """
    try:
        contents = await file.read()
        file_extension = file.filename.split(".")[-1]

        # Load file into DataFrame
        if file_extension == "csv":
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif file_extension == "xlsx":
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")

        # Step 1: Rule-Based Cleaning
        df_cleaned = cleaner.clean_data(df)

        # Step 2: AI Cleaning (with fallback)
        df_ai_cleaned = run_ai_cleaning(df_cleaned)

        return {"cleaned_data": dataframe_to_json_records(df_ai_cleaned)}

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
        df_ai_cleaned = run_ai_cleaning(df_cleaned)

        return {"cleaned_data": dataframe_to_json_records(df_ai_cleaned)}

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
        df_ai_cleaned = run_ai_cleaning(df_cleaned)

        return {"cleaned_data": dataframe_to_json_records(df_ai_cleaned)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing API data: {str(e)}")


# ==============================
# Run Server
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)