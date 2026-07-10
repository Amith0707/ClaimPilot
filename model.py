import os
import json
from dotenv import load_dotenv
from groq import Groq
from utils.logger import logger
from chunker import retrieve_rules

# Importing constants
from utils.const import MODEL,SYSTEM_PROMPT,ROUTE_CLAIM_TOOL

load_dotenv()

def load_and_route(claim_text:str,k:int=5):
    """Need to place docs here [IMP]"""

    client=Groq(api_key=os.getenv("GROQ_API_KEY"))
    retrieved=retrieve_rules(claim_text=claim_text,k=k)
    logger.log("Retrived relevant user chunks and loaded the model successfully")

    rules_context = "\n\n".join([f"{r['header']}\n{r['text']}" for r in retrieved])
    user_message=f"""Retrieved policies for this claim: {claim_text}
                Claim to route:\"\"\"{claim_text}\"\"\"
                """
    response=client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {'role':'user','content':user_message}
        ],
        tools=[ROUTE_CLAIM_TOOL],
        tool_choice={"type": "function", "function": {"name": "route_claim"}} # Need to understand this
    )
    tool_call=response.choices[0].message.tool_calls[0]
    result=json.loads(tool_call.function.arguments)
    logger.log("Model response submitted successfully")

    return result

# Smoke test
# if __name__=="__main__":
#     test_res=load_and_route("my Car was rear-ended and my neck hurts lil bit")
#     print("-"*30)
#     print(test_res)
    