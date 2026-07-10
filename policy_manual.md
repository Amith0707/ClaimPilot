RULE 1 — Property Damage (default)
Claims describing vehicle damage only, with no mention of injury, legal action, or fraud indicators, are categorized as Property Damage, routed to Auto Claims Team, priority Medium.

RULE 2 — Property Damage (high value)
If a Property Damage claim mentions repair estimates, total loss, or damage description exceeding a significant financial threshold, or involves multiple vehicles, priority is escalated to High even without injury.

RULE 3 — Personal Injury (precedence rule)
Any claim mentioning injury, pain, hospital, medical treatment, or bodily harm — regardless of how minor — is categorized as Personal Injury and routed to Injury Specialists, taking precedence over any property damage mentioned in the same claim.

RULE 4 — Personal Injury (priority)
Personal Injury claims are priority High by default. Only downgrade to Medium if the injury is explicitly described as resolved, minor, and not requiring ongoing treatment. If the claim describes severe, critical, life-threatening, unconscious, not breathing, fatal, death, or passed away language, priority remains High and the reasoning field must explicitly flag it as top-severity requiring immediate emergency-level human follow-up, ambulance dispatch, or escalation beyond standard claims processing.

RULE 5 — Litigation trigger (legal language)
Any claim containing legal language such as "attorney," "lawyer," "sue," "lawsuit," or "legal action" is categorized as Litigation and routed to Legal Team with priority High, regardless of the underlying incident type.

RULE 6 — Fraud Review (mismatch signal)
Claims where the described severity contradicts other stated details (e.g., "minor damage" paired with a very high repair estimate, or inconsistent incident timelines) are flagged as Fraud Review, routed to Fraud Investigation Unit, priority High, pending manual verification.

RULE 7 — Fraud Review (explicit suspicion language)
Claims containing language suggesting staged incidents, multiple recent claims from the same party in a short timeframe, repeated or similar claims filed close together, or explicit mention of prior fraud investigations are categorized as Fraud Review, routed to Fraud Investigation Unit, priority High.

RULE 8 — Claim Status Inquiry
Claims that reference an existing/prior claim and ask about its status, delay, or progress — rather than reporting a new incident — are categorized as Claim Status Inquiry, routed to Customer Support Team.

RULE 9 — Claim Status Inquiry (priority from tone)
Status inquiries expressing frustration, repeated follow-up, or long delay (e.g., "weeks," "still waiting," exclamations, all-caps) are priority High, routed to Customer Support Team. Neutral or first-time status checks are priority Medium, routed to Customer Support Team.

RULE 10 — General Inquiry
Claims that are questions about coverage, policy terms, or general information — with no specific incident being reported — are categorized as General Inquiry, routed to Customer Support Team, priority Low.

RULE 11 — Insufficient Information (fallback)
If a claim is too short, vague, or otherwise lacks enough distinguishing signal to determine incident type, severity, or parties involved — whether because it is a short message like "broken" or "help," or a longer message that never mentions injury, damage, legal action, fraud, or status — categorize as Insufficient Information, route to Manual Review Team, priority Low, confidence Low. Do not guess a specific category with high confidence.

RULE 12 — Ambiguous claims (tie-break rule)
When a claim reasonably fits more than one category — most commonly Personal Injury vs. Property Damage — the reasoning field must explicitly state which signal was prioritized and why (default: injury takes precedence per Rule 3).

RULE 13 — Multiple signals present
If a claim contains signals for more than one category (e.g., injury + legal language), prioritize in this order: Litigation > Personal Injury > Fraud Review > Property Damage > Claim Status Inquiry > General Inquiry. State the overriding signal in the reasoning field.

RULE 14 — Angry/emotional tone
Anger, frustration, or emotional language alone — without any accompanying mention of legal action, attorney, lawsuit, fraud, staged incidents, injury, or specific damage details — does NOT indicate Litigation, Fraud Review, or Personal Injury. General complaints or expressions of frustration with no other substantive content should be treated as Claim Status Inquiry or General Inquiry, with tone affecting priority only, not category.


RULE 15 — Missing required documentation
If a claim references injury or significant damage but does not mention any supporting documentation (police report, medical record, photos), note this in the reasoning field as a flag for manual follow-up, without downgrading confidence unless the description itself is too vague to categorize.

RULE 16 — Off-topic / non-claim input
Messages unrelated to an insurance claim, accident, policy question, or claim status — such as general conversation, unrelated questions, greetings, or test input with no insurance-relevant content — should be categorized as Insufficient Information, routed to Manual Review Team, priority Low, confidence Low, with reasoning noting the message appears unrelated to an insurance claim.