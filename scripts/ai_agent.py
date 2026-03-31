import os
import json
import pandas as pd
from dotenv import load_dotenv

# LangChain + LangGraph
from langchain_openai import OpenAI
from langgraph.graph import StateGraph, END

from pydantic import BaseModel

# ==============================
# Load API Key
# ==============================
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

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
        self.enabled = bool(openai_api_key)
        self.llm = OpenAI(openai_api_key=openai_api_key, temperature=0) if self.enabled else None
        self.graph = self.create_graph() if self.enabled else None

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
            response = self.llm.invoke(state.input_text)

            return CleaningState(
                input_text=state.input_text,
                structured_response=str(response)
            )

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

        if "```" in candidate:
            parts = candidate.split("```")
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("[") or stripped.startswith("{"):
                    return json.loads(stripped)

        return json.loads(candidate)

    # ------------------------------
    # Process Data
    # ------------------------------
    def process_data(self, df: pd.DataFrame, batch_size=20):
        """
        Processes data in batches to avoid token limits.
        Returns a DataFrame. Falls back to rule-cleaned input if AI is unavailable or fails.
        """
        if df is None or df.empty:
            return df

        if not self.enabled or self.graph is None:
            return df

        cleaned_batches = []

        for i in range(0, len(df), batch_size):
            df_batch = df.iloc[i:i + batch_size].copy()

            prompt = f"""
You are an AI Data Cleaning Agent. Analyze the dataset:

{df_batch.to_string()}

Tasks:
- Identify missing values
- Choose best imputation strategy (mean, median, mode)
- Remove duplicates
- Format text correctly

Return only valid JSON as an array of objects.
Do not add explanations or markdown.
"""

            state = CleaningState(
                input_text=prompt,
                structured_response=""
            )

            try:
                response = self.graph.invoke(state)

                if isinstance(response, dict):
                    response = CleaningState(**response)

                parsed = self._extract_json_payload(response.structured_response)
                cleaned_batch = pd.DataFrame(parsed)

                if cleaned_batch.empty:
                    cleaned_batches.append(df_batch)
                else:
                    cleaned_batches.append(cleaned_batch)
            except Exception:
                # Fail open: keep service usable when model/quota/parsing fails.
                cleaned_batches.append(df_batch)

        if not cleaned_batches:
            return df

        return pd.concat(cleaned_batches, ignore_index=True)


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