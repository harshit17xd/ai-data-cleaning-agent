import os
import json
import pandas as pd
from dotenv import load_dotenv

# LangChain - Try Groq first (free), then OpenAI
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from langchain_openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# ==============================
# Load API Keys
# ==============================
load_dotenv()
groq_api_key = os.getenv("Groq_API_KEY", "").strip().strip('"\'')
openai_api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"\'')

# ==============================
# Define State
# ==============================
class CleaningState(BaseModel):
    """
    State schema defining input and output for the LangGraph agent.
    """
    input_text: str
    structured_response: str = ""


# ==============================
# AI Agent Class
# ==============================
class AIAgent:

    def __init__(self):
        self.enabled = False
        self.llm = None
        self.graph = None
        self.model_name = "None"
        self.last_prompt = ""
        self.last_response = ""
        self.last_error = ""
        
        # Try Groq first (free!) - supports gsk_ and sk-proj-gsk_ formats
        if GROQ_AVAILABLE and groq_api_key and "gsk_" in groq_api_key:
            # Allow override via env if user knows a working Groq model
            override_model = os.getenv("GROQ_MODEL", "").strip()
            groq_models = [m for m in [override_model] if m]
            # Common Groq model names (adjust if Groq deprecates any)
            groq_models += [
                "llama-3.3-70b-versatile",
                "llama3-8b-8192",
                "llama3-70b-8192",
                "llama-3.1-8b-instant",
            ]
            for model in groq_models:
                try:
                    self.llm = ChatGroq(api_key=groq_api_key, model=model, temperature=0)
                    self.model_name = f"Groq ({model})"
                    self.enabled = True
                    self.graph = self.create_graph()
                    print(f"✅ AI Agent: Using {self.model_name}")
                    break
                except Exception as e:
                    print(f"⚠️ Groq model init failed ({model}): {e}")
                    self.enabled = False

        # Fallback to OpenAI if Groq not available
        if not self.enabled and OPENAI_AVAILABLE and openai_api_key and openai_api_key.startswith("sk-"):
            try:
                self.llm = OpenAI(api_key=openai_api_key, temperature=0)
                self.model_name = "OpenAI (GPT)"
                self.enabled = True
                self.graph = self.create_graph()
                print(f"✅ AI Agent: Using {self.model_name}")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
                self.enabled = False
        
        # Show what's available
        if not self.enabled:
            print("\n❌ NO AI MODEL AVAILABLE!")
            print(f"   Groq available: {GROQ_AVAILABLE}, Key valid: {'gsk_' in groq_api_key if groq_api_key else False}")
            print(f"   OpenAI available: {OPENAI_AVAILABLE}, Key valid: {openai_api_key.startswith('sk-') if openai_api_key else False}")
            print("\n   To use Groq (FREE):")
            print("   1. Get key from: https://console.groq.com")
            print("   2. Set in .env: Groq_API_KEY=gsk_... or sk-proj-gsk_...")
            print("\n   To use OpenAI:")
            print("   1. Check your API quota at https://platform.openai.com/account/usage/overview")
            print("   2. Add credits if needed")

    # ------------------------------
    # Create Graph
    # ------------------------------
    def create_graph(self):
        """
        Creates and returns a LangGraph agent graph with state management.
        """
        graph = StateGraph(CleaningState)

        # ✅ Agent Logic
        def agent_logic(state: CleaningState) -> CleaningState:
            """
            Processes input and returns a structured response.
            """
            try:
                response = self.llm.invoke(state.input_text)
                
                # Handle different response types
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                return CleaningState(
                    input_text=state.input_text,
                    structured_response=response_text
                )
            except Exception as e:
                print(f"❌ LLM Error: {e}")
                raise

        # Graph flow
        graph.add_node("cleaning_agent", agent_logic)
        graph.add_edge("cleaning_agent", END)
        graph.set_entry_point("cleaning_agent")

        return graph.compile()

    def _extract_json_payload(self, text: str):
        """
        Attempts to parse JSON from direct content or fenced markdown blocks.
        """
        candidate = text.strip()

        # Try markdown code blocks
        if "```" in candidate:
            parts = candidate.split("```")
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("[") or stripped.startswith("{"):
                    try:
                        return json.loads(stripped)
                    except json.JSONDecodeError:
                        pass

        # Try direct JSON
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Text was: {candidate[:200]}...")
            raise

    # ------------------------------
    # Process Data
    # ------------------------------
    def process_data(self, df: pd.DataFrame, batch_size=20, user_instructions: str = ""):
        """
        Processes data in batches using AI to detect and fix data quality issues.
        Handles: invalid emails, phone numbers, dates, salaries, ages, missing values, duplicates.
        Works for ANY dynamic database schema.
        """
        if df is None or df.empty:
            return df

        if not self.enabled or self.graph is None:
            print("⚠️ AI not enabled, returning original data")
            return df

        cleaned_batches = []
        cleaned_instruction_text = (user_instructions or "").strip()

        for batch_num, i in enumerate(range(0, len(df), batch_size)):
            df_batch = df.iloc[i:i + batch_size].copy()
            
            print(f"\n🔄 Processing batch {batch_num + 1}...")

            # Build comprehensive cleaning instructions
            instruction_block = ""
            if cleaned_instruction_text:
                instruction_block = f"\nUser Requirements:\n{cleaned_instruction_text}"

            prompt = f"""You are a Data Quality Expert. Clean this data strictly:

DATA TABLE:
{df_batch.to_string()}

COLUMN INFO: {list(df_batch.columns)}

STRICT VALIDATION RULES:
1. EMAIL: Must be valid (name@domain.ext) - REMOVE rows with @@, no @, invalid format
2. PHONE: Must be EXACTLY 10 digits - REMOVE rows with letters, symbols, or wrong length
3. AGE: Must be number 18-80 - REMOVE "twenty five", text values, out of range
4. SALARY: Must be numeric - REMOVE "not_available", text values, use null if missing
5. DATE: Must be YYYY-MM-DD, valid date - REMOVE 13+ months, 31st in 30-day months, invalid dates
6. DUPLICATES: Remove exact duplicate rows
7. INVALID ROWS: REMOVE any row that fails validation above{instruction_block}

CRITICAL: Only keep rows that pass ALL validations above!

Return ONLY a valid JSON array. Example format:
[
  {{"name": "value", "age": 25, "email": "test@example.com", ...}},
  {{"name": "value", "age": 30, ...}}
]

NO explanations, NO markdown, ONLY JSON array."""

            # Store the exact prompt sent to LLM (latest batch)
            self.last_prompt = prompt
            self.last_response = ""
            self.last_error = ""

            state = CleaningState(
                input_text=prompt,
                structured_response=""
            )

            try:
                print("   📤 Sending to LLM...")
                response = self.graph.invoke(state)

                if isinstance(response, dict):
                    response = CleaningState(**response)

                llm_text = response.structured_response
                self.last_response = str(llm_text)
                print(f"   📥 LLM Response (first 300 chars): {str(llm_text)[:300]}...")

                # Try to extract JSON
                try:
                    parsed = self._extract_json_payload(llm_text)
                    cleaned_batch = pd.DataFrame(parsed)
                    
                    print(f"   ✅ Parsed {len(cleaned_batch)} rows from LLM")
                    
                    if cleaned_batch.empty:
                        print(f"   ⚠️ LLM returned empty data, using original batch")
                        cleaned_batches.append(df_batch)
                    else:
                        cleaned_batches.append(cleaned_batch)
                        
                except json.JSONDecodeError as json_err:
                    print(f"   ❌ JSON parse failed: {json_err}")
                    print(f"   📝 Raw response: {llm_text[:500]}")
                    print(f"   ⚠️ Using original batch")
                    cleaned_batches.append(df_batch)
                    
            except Exception as e:
                self.last_error = str(e)
                print(f"   ❌ Error in batch: {str(e)[:200]}")
                print(f"   ⚠️ Using original batch")
                cleaned_batches.append(df_batch)

        if not cleaned_batches:
            print("❌ No batches processed, returning original data")
            return df

        print(f"\n✅ Concatenating {len(cleaned_batches)} batches...")
        result = pd.concat(cleaned_batches, ignore_index=True)
        
        # Remove exact duplicates in final output
        before_dedup = len(result)
        result = result.drop_duplicates().reset_index(drop=True)
        after_dedup = len(result)
        print(f"🔄 Removed {before_dedup - after_dedup} duplicate rows")
        
        print(f"📊 Final result: {len(result)} cleaned rows")
        return result


# ==============================
# Example Usage
# ==============================
if __name__ == "__main__":
    # Sample Data
    data = {
        "Name": ["A", "B", None, "D", "D"],
        "Age": [25, None, 30, 22, 22],
        "City": ["Pune", "Mumbai", "Delhi", None, None]
    }

    df = pd.DataFrame(data)

    agent = AIAgent()
    result = agent.process_data(df)

    print("\n===== CLEANED OUTPUT =====\n")
    print(result)