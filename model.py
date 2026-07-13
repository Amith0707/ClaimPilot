import os
import json
from typing import Literal
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from pydantic import BaseModel,ValidationError
from utils.logger import logger
from chunker import retrieve_rules
from utils.const import MODEL,SYSTEM_PROMPT,ROUTE_CLAIM_TOOL

load_dotenv()

class ClaimRouting(BaseModel):
    """Docs ?"""
    category: Literal[
        "Property Damage", "Personal Injury", "Fraud Review",
        "Litigation", "Claim Status Inquiry", "General Inquiry",
        "Insufficient Information"
    ]
    priority:Literal['High','Medium','Low']
    assigned_team: Literal[
        "Auto Claims Team", "Injury Specialists",
        "Fraud Investigation Unit", "Legal Team",
        "Customer Support Team", "Manual Review Team"
    ]
    reasoning: str 
    confidence:Literal["High", "Medium", "Low"]


def load_and_route(claim_text:str,k:int=8):
    """Need to place docs here [IMP]"""

    # client=Groq(api_key=os.getenv("GROQ_API_KEY"))
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    retrieved=retrieve_rules(claim_text=claim_text,k=k)
    logger.log("Retrived relevant user chunks and loaded the model successfully")

    rules_context = "\n\n".join([f"{r['header']}\n{r['text']}" for r in retrieved])
    user_message=f"""Retrieved policies for this claim: {rules_context}
                Claim to route:\"\"\"{claim_text}\"\"\"
                """
    response=client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {'role':'user','content':user_message}
        ],
        tools=[ROUTE_CLAIM_TOOL],
        tool_choice={"type": "function", "function": {"name": "route_claim"}}, # Need to understand this
        temperature=0.1
    )
    tool_call=response.choices[0].message.tool_calls[0]
    raw_result = json.loads(tool_call.function.arguments)

    # Validating model output
    try:
        validated = ClaimRouting(**raw_result)
        logger.log("Output validated successfully against schema")
        return validated.model_dump()
    
    # Need to add a fallback/retry logic here
    except ValidationError as e:
        logger.log(f"Schema validation failed: {e}", level="error")
        raise

# # Smoke test
# if __name__=="__main__":
#     test_res=load_and_route(" ")
#     print("-"*30)
#     print(test_res)
    