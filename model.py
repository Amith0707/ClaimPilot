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
    """Schema for a validated claim routing decision.

    Enforces that every routed claim conforms to a fixed set of categories,
    priorities, and teams before it is trusted or persisted. Used to validate
    the raw JSON returned by the LLM's tool call in :func:`load_and_route`.

    Attributes
    ----------
    category : str
        The claim category. One of: "Property Damage", "Personal Injury",
        "Fraud Review", "Litigation", "Claim Status Inquiry", "General Inquiry",
        "Insufficient Information", "Out of Scope", "System Error".
    priority : str
        Urgency level. One of: "High", "Medium", "Low".
    assigned_team : str
        The internal team the claim is routed to. One of: "Auto Claims Team",
        "Injury Specialists", "Fraud Investigation Unit", "Legal Team",
        "Customer Support Team", "Manual Review Team", "Automated Response",
        "Engineering / Retry Queue".
    reasoning : str
        A one-sentence explanation of the routing decision, citing the
        relevant policy rule where applicable.
    confidence : str
        Model's confidence in the decision. One of: "High", "Medium", "Low".
    """

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
    """Route an insurance claim to the correct category, priority, and team.

        Retrieves the most relevant policy rules for the given claim via RAG
        (:func:`chunker.retrieve_rules`), constructs a prompt combining those
        rules with the claim text, and calls the LLM with a schema-enforced
        tool call to produce a structured routing decision. The result is
        validated against :class:`ClaimRouting` before being returned.

        On failure whether an LLM API error (rate limit, timeout, connection
        error) or a schema validation failure the call is retried up to
        ``max_retries`` times with exponential backoff. If all retries fail,
        a safe default (:data:`FALLBACK_RESULT`) is returned instead of raising,
        so the caller never receives an unhandled exception.

        Parameters
        ----------
        claim_text : str
            The raw claim description to route, as submitted by a customer or
            loaded from a demo ticket.
        k : int, optional
            Number of policy rule chunks to retrieve from the vector store for
            context (default is 8). At the current policy manual size (~15
            rules), a high k reduces the risk of relevant rules being missed
            by similarity ranking.
        max_retries : int, optional
            Maximum number of retry attempts after the first failed call
            (default is 2, giving 3 total attempts).

        Returns
        -------
        dict
            A dictionary with keys ``category``, ``priority``, ``assigned_team``,
            ``reasoning``, and ``confidence``, matching :class:`ClaimRouting`.
            Returns :data:`FALLBACK_RESULT` if all attempts fail.

        Notes
        -----
        If the environment variable ``SIMULATE_DISCONNECT`` is set to ``"true"``,
        this function raises a :class:`ConnectionError` on every attempt,
        regardless of the real API's availability. This is a debug hook used to
        demonstrate graceful failure handling without requiring an actual network
        disconnect.

        Examples
        --------
        >>> result = load_and_route("My car was rear-ended and my neck hurts")
        >>> result["category"]
        'Personal Injury'
        """

    retrieved = retrieve_rules(claim_text=claim_text, k=k)
    logger.log("Retrieved relevant policy chunks successfully")

    rules_context = "\n\n".join([f"{r['header']}\n{r['text']}" for r in retrieved])
    user_message = f"""Retrieved policy rules for this claim:

{rules_context}

Claim to route:
\"\"\"{claim_text}\"\"\""""

    for attempt in range(max_retries + 1):
        try:
            if os.getenv("SIMULATE_DISCONNECT") == "true":
                raise ConnectionError("Simulated network disconnect for demo purposes")
            
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

# if __name__ == "__main__":
#     test_res = load_and_route("my Car was rear-ended and my neck hurts lil bit")
#     print("-" * 30)
#     print(test_res)