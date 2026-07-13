import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from typing import Literal
from utils.logger import logger
from chunker import retrieve_rules
from utils.const import MODEL, SYSTEM_PROMPT, ROUTE_CLAIM_TOOL

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ClaimRouting(BaseModel):
    category: Literal[
        "Property Damage", "Personal Injury", "Fraud Review",
        "Litigation", "Claim Status Inquiry", "General Inquiry",
        "Insufficient Information", "Out of Scope", "System Error"
    ]
    priority: Literal["High", "Medium", "Low"]
    assigned_team: Literal[
        "Auto Claims Team", "Injury Specialists",
        "Fraud Investigation Unit", "Legal Team",
        "Customer Support Team", "Manual Review Team",
        "Automated Response", "Engineering / Retry Queue"
    ]
    reasoning: str
    confidence: Literal["High", "Medium", "Low"]


FALLBACK_RESULT = {
    "category": "System Error",
    "priority": "Medium",
    "assigned_team": "Engineering / Retry Queue",
    "reasoning": "Automated routing failed due to a system error (API failure or invalid response after retries). This claim has NOT been reviewed for content and should be re-processed or escalated, not treated as a low-priority ambiguous claim.",
    "confidence": "Low"
}


def load_and_route(claim_text: str, k: int = 8, max_retries: int = 2):
    """Routes an insurance claim to the correct category/team using RAG + LLM tool-calling.
    Retries on failure; falls back to a safe System Error result if all retries fail."""

    retrieved = retrieve_rules(claim_text=claim_text, k=k)
    logger.log("Retrieved relevant policy chunks successfully")

    rules_context = "\n\n".join([f"{r['header']}\n{r['text']}" for r in retrieved])
    user_message = f"""Retrieved policy rules for this claim:

{rules_context}

Claim to route:
\"\"\"{claim_text}\"\"\""""

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                tools=[ROUTE_CLAIM_TOOL],
                tool_choice={"type": "function", "function": {"name": "route_claim"}},
                temperature=0.1
            )

            tool_call = response.choices[0].message.tool_calls[0]
            raw_result = json.loads(tool_call.function.arguments)
            validated = ClaimRouting(**raw_result)

            logger.log("Model response validated successfully")
            return validated.model_dump()

        except ValidationError as e:
            logger.log(f"Validation failed on attempt {attempt + 1}: {e}", level="warning")
            if attempt < max_retries:
                continue
            logger.log("Max retries reached after validation failures, using fallback", level="error")
            return FALLBACK_RESULT

        except Exception as e:
            logger.log(f"API call failed on attempt {attempt + 1}: {e}", level="error")
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s...
                continue
            logger.log("Max retries reached after API failures, using fallback", level="error")
            return FALLBACK_RESULT


if __name__ == "__main__":
    test_res = load_and_route("my Car was rear-ended and my neck hurts lil bit")
    print("-" * 30)
    print(test_res)