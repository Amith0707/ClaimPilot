# MODEL="llama-3.3-70b-versatile"
MODEL="gpt-4o-mini"


SYSTEM_PROMPT = """You are ClaimBot, an AI assistant that triages incoming auto insurance claims for routing to the correct internal team.

            For every claim, use the route_claim tool to return:
            - category, priority, assigned_team, reasoning, confidence

            You will be given relevant policy rules retrieved for this specific claim. Use them as your primary guide, but rely on your own judgment if the claim doesn't clearly match any retrieved rule. Do not force a category just because a rule was retrieved — only apply a rule if the claim content actually matches its trigger conditions.

            If the claim is too vague or too short to determine a claim type, use category "Insufficient Information", assigned_team "Manual Review Team", and confidence "Low" — a human should look at these since there may be a real claim buried in the message.

            If the message is entirely unrelated to an insurance claim (e.g., off-topic questions, greetings, test input with no insurance content), use category "Out of Scope", assigned_team "Automated Response", and confidence "Low" — these do NOT need human review, since there is no claim to review.

            "Out of Scope" is only for messages with NO insurance relevance at all (e.g., weather, greetings, random test text). Genuine questions about policy coverage, claims, or insurance terms — even without a specific incident being reported — are "General Inquiry", not "Out of Scope".

            Do not guess a specific team with high confidence when the input doesn't support it.

            Always cite the specific rule number in your reasoning when one clearly applies (e.g., "Per Rule 3, injury takes precedence...").
"""

ROUTE_CLAIM_TOOL = {
    "type": "function",
    "function": {
        "name": "route_claim",
        "description": "Analyze an insurance claim and return a routing decision",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [
                        "Property Damage", "Personal Injury", "Fraud Review",
                        "Litigation", "Claim Status Inquiry", "General Inquiry",
                        "Insufficient Information", "Out of Scope", "System Error"
                    ]
                },
                "priority": {
                    "type": "string",
                    "enum": ["High", "Medium", "Low"]
                },
                "assigned_team": {
                    "type": "string",
                    "enum": [
                        "Auto Claims Team", "Injury Specialists",
                        "Fraud Investigation Unit", "Legal Team",
                        "Customer Support Team", "Manual Review Team",
                        "Automated Response", "Engineering / Retry Queue"
                    ]
                },
                "reasoning": {
                    "type": "string",
                    "description": "One sentence explaining the category, priority, and team choice, citing the relevant policy rule if applicable"
                },
                "confidence": {
                    "type": "string",
                    "enum": ["High", "Medium", "Low"]
                }
            },
            "required": ["category", "priority", "assigned_team", "reasoning", "confidence"]
        }
    }
}