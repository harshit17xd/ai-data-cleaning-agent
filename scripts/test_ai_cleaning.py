"""
🚀 DIRECT AI DATA CLEANING TEST
Test your problematic data directly with LLM without any framework
Works for ANY dynamic database/CSV
"""

import pandas as pd
import sys
import os

# Add scripts to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ai_agent import AIAgent
from data_cleaning import DataCleaning

def clean_data_with_ai(file_path, use_ai=True):
    """
    Load any CSV/data and clean it with AI directly
    Works for: sample_data.csv, any dynamic database export, any schema
    """
    print(f"\n{'='*60}")
    print(f"📂 Loading: {file_path}")
    print(f"{'='*60}\n")
    
    # Load data
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    print(f"📊 Original Data ({len(df)} rows, {len(df.columns)} columns):")
    print(df.to_string())
    print(f"\n🔴 ISSUES DETECTED:")
    print(f"  - Rows: {len(df)}")
    print(f"  - Columns: {list(df.columns)}")
    print(f"  - Missing values: {df.isnull().sum().sum()}")
    print(f"  - Duplicates: {df.duplicated().sum()}")
    
    # Step 1: Basic cleaning
    print(f"\n\n{'='*60}")
    print(f"🔧 STEP 1: Basic Rule-Based Cleaning")
    print(f"{'='*60}\n")
    
    cleaner = DataCleaning()
    df_basic = cleaner.clean_data(df, impute_missing=False)
    
    print(f"✅ After basic cleaning ({len(df_basic)} rows):")
    print(df_basic.to_string())
    
    # Step 2: AI Cleaning
    if use_ai:
        print(f"\n\n{'='*60}")
        print(f"🤖 STEP 2: AI-Powered Smart Cleaning (LLM)")
        print(f"{'='*60}\n")
        
        ai_agent = AIAgent()
        
        if not ai_agent.enabled:
            print("⚠️ OPENAI_API_KEY not found in .env file")
            print("   Set it to enable AI cleaning features")
            print("   OPENAI_API_KEY=sk-...")
            return df_basic
        
        print("🤔 Sending to LLM for intelligent data fixing...\n")
        
        df_ai = ai_agent.process_data(df_basic)
        
        print(f"\n✅ After AI Cleaning ({len(df_ai)} rows):\n")
        print(df_ai.to_string())
        
        print(f"\n\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"Original rows: {len(df)}")
        print(f"After basic cleaning: {len(df_basic)}")
        print(f"After AI cleaning: {len(df_ai)}")
        print(f"Rows fixed/removed: {len(df) - len(df_ai)}")
        
        return df_ai
    
    return df_basic


if __name__ == "__main__":
    # ✅ Test with your sample data
    print("\n" + "="*60)
    print("🎯 AI DATA CLEANING - DIRECT TEST")
    print("="*60)
    
    # Load and clean sample data
    file_path = os.path.join(
        os.path.dirname(__file__),
        "../data/sample_data.csv"
    )
    
    cleaned_df = clean_data_with_ai(file_path, use_ai=True)
    
    # Save cleaned data
    if cleaned_df is not None:
        output_path = os.path.join(
            os.path.dirname(__file__),
            "../data/sample_data_cleaned.csv"
        )
        cleaned_df.to_csv(output_path, index=False)
        print(f"\n💾 Cleaned data saved to: {output_path}")
