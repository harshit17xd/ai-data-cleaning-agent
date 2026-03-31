"""
🔍 DEBUG SCRIPT - Check What's Wrong
Run this to see exactly where the issue is
"""

import os
import sys
from dotenv import load_dotenv

print("\n" + "="*60)
print("🔍 AI DATA CLEANING - DEBUG CHECK")
print("="*60 + "\n")

# 1. Check .env file
print("1️⃣ Checking .env file...")
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"\'')

if not openai_key:
    print("   ❌ OPENAI_API_KEY not found!")
    print("   📋 Fix: Create .env file with OPENAI_API_KEY=sk-your-key")
    sys.exit(1)

if not openai_key.startswith("sk-"):
    print(f"   ❌ OPENAI_API_KEY looks invalid: {openai_key[:20]}...")
    print("   📋 Fix: Key should start with 'sk-', check .env file")
    sys.exit(1)

key_preview = openai_key[:20] + "..." + openai_key[-10:]
print(f"   ✅ OPENAI_API_KEY found: {key_preview}")

# 2. Check imports
print("\n2️⃣ Checking Python packages...")
try:
    import pandas as pd
    print("   ✅ pandas")
except ImportError:
    print("   ❌ pandas - install: pip install pandas")
    sys.exit(1)

try:
    from langchain_openai import OpenAI
    print("   ✅ langchain_openai")
except ImportError:
    print("   ❌ langchain_openai - install: pip install langchain-openai")
    sys.exit(1)

try:
    from langgraph.graph import StateGraph, END
    print("   ✅ langgraph")
except ImportError:
    print("   ❌ langgraph - install: pip install langgraph")
    sys.exit(1)

# 3. Initialize AI Agent
print("\n3️⃣ Initializing AI Agent...")
sys.path.append(os.path.dirname(__file__))

try:
    from ai_agent import AIAgent
    print("   ✅ Imported AIAgent")
except ImportError as e:
    print(f"   ❌ Failed to import AIAgent: {e}")
    sys.exit(1)

try:
    ai_agent = AIAgent()
    print(f"   ✅ AI Agent created")
    
    if ai_agent.enabled:
        print(f"   ✅ AI Agent ENABLED (LLM ready)")
    else:
        print(f"   ❌ AI Agent DISABLED")
        print(f"      Check OPENAI_API_KEY in .env file")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error creating AI Agent: {e}")
    sys.exit(1)

# 4. Test with sample data
print("\n4️⃣ Testing with sample data...")
try:
    data = {
        "name": ["Harsh", "Rahul"],
        "age": [21, "twenty five"],
        "email": ["harsh@gmail.com", "rahul@@gmail"],
        "salary": [50000, "not_available"]
    }
    df = pd.DataFrame(data)
    print(f"   📊 Sample data created: {len(df)} rows")
    print(df.to_string())
    
    print("\n   🤖 Sending to LLM...")
    df_cleaned = ai_agent.process_data(df)
    
    print(f"\n   ✅ Result: {len(df_cleaned)} rows cleaned")
    print(df_cleaned.to_string())
    
except Exception as e:
    print(f"   ❌ Error during cleaning: {e}")
    print(f"\n   💡 Troubleshooting:")
    print(f"      - Check OpenAI API key is correct")
    print(f"      - Check you have API credits")
    print(f"      - Try running: python -c \"from langchain_openai import OpenAI; OpenAI(api_key='sk-...').invoke('test')\"")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL CHECKS PASSED!")
print("="*60)
print("\nYou can now:")
print("  1. Run: uvicorn backend:app --reload")
print("  2. Run: streamlit run ../app/app.py")
print("  3. Upload CSV files and enable 'Use Agentic AI cleaning'")
print("\n")
