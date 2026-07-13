RULE 1 — Property Damage (default)
Claims describing vehicle damage only, with no mention of injury, legal action, or fraud indicators, are categorized as Property Damage, routed to Auto Claims Team, priority Medium.

RULE 2 — Property Damage (high value)
If a Property Damage claim mentions repair estimates, total loss, or damage description exceeding a significant financial threshold, or involves multiple vehicles, priority is escalated to High even without injury.

RULE 3 — Personal Injury (precedence rule)
Any claim mentioning injury, pain, hospital, medical treatment, or bodily harm — regardless of how minor — is categorized as Personal Injury and routed to Injury Specialists, taking precedence over any property damage mentioned in the same claim.

RULE 4 — Personal Injury (priority)
Personal Injury claims are priority High by default. Only downgrade to Medium if the injury is explicitly described as resolved, minor, and not requiring ongoing treatment. If the claim describes severe, critical, life-threatening, unconscious, not breathing, fatal, death, or passed away language, priority remains High and the reasoning field must explicitly flag it as top-severity requiring immediate emergency-level human follow-up, ambulance dispatch, or escalation beyond standard claims processing.

RULE 5 — Litigation trigger (legal language)
A claim is categorized as Litigation and routed to Legal Team with priority High only when the legal language indicates active or adversarial legal action against the insurer — such as "I'm suing," "my lawyer is filing a suit," "we are pursuing legal action," or "I've retained an attorney to take action against you." Incidental mentions of legal counsel — such as a lawyer merely advising the claimant on how to report or document a claim ("my lawyer said I should report this") — do NOT trigger Litigation on their own. In such incidental cases, categorize based on the
substantive content of the claim (injury, damage, etc.) per the normal precedence rules, and note the incidental legal mention in the reasoning field without it driving the category.

RULE 6 — Fraud Review (mismatch signal)
Claims where the described severity contradicts other stated details (e.g., "minor damage" paired with a very high repair estimate, or inconsistent incident timelines) MUST be categorized as Fraud Review, routed to Fraud Investigation Unit, priority High — NOT Property Damage, even when the repair estimate alone would otherwise trigger Rule 2's cost escalation. A mismatch between described severity and financial/documentary evidence is a stronger signal than cost alone.

RULE 7 — Fraud Review (explicit suspicion language)
Claims containing language suggesting staged incidents, multiple recent claims from the same party in a short timeframe, repeated or similar claims filed close together, or explicit mention of prior fraud investigations are categorized as Fraud Review, routed to Fraud Investigation Unit, priority High.

RULE 8 — Claim Status Inquiry
Claims that reference an existing/prior claim and ask about its status, delay, or
progress — rather than reporting a new incident — are categorized as Claim Status
Inquiry, routed to Customer Support Team. Priority is High when any of the following
are present: the claim has been pending 2 or more weeks, the claimant mentions 2 or
more prior contact attempts, phrases like "still no update," "no response," or
"haven't heard back," or strong emotional language (all-caps, exclamation marks,
words like "ridiculous," "unacceptable"). Otherwise, priority is Medium.

RULE 9— General Inquiry
Claims that are questions about coverage, policy terms, or general information — with no specific incident being reported — are categorized as General Inquiry, routed to Customer Support Team, priority Low.

RULE 10 — Insufficient Information (fallback)
If a claim is too short, vague, or otherwise lacks enough distinguishing signal to determine incident type, severity, or parties involved — whether because it is a short message like "broken" or "help," or a longer message that never mentions injury, damage, legal action, fraud, or status — categorize as Insufficient Information, route to Manual Review Team, priority Low, confidence Low. Do not guess a specific category with high confidence.

RULE 11 — Ambiguous claims (tie-break rule)
When a claim reasonably fits more than one category — most commonly Personal Injury vs. Property Damage — the reasoning field must explicitly state which signal was prioritized and why (default: injury takes precedence per Rule 3).

RULE 12 — Multiple signals present
If a claim contains signals for more than one category (e.g., injury + legal language), prioritize in this order: Litigation > Personal Injury > Fraud Review > Property Damage > Claim Status Inquiry > General Inquiry. State the overriding signal in the reasoning field.

RULE 13 — Angry/emotional tone
Anger, frustration, or emotional language alone — without any accompanying mention of legal action, attorney, lawsuit, fraud, staged incidents, injury, or specific damage details — does NOT indicate Litigation, Fraud Review, or Personal Injury. General complaints or expressions of frustration with no other substantive content should be treated as Claim Status Inquiry or General Inquiry, with tone affecting priority only, not category.

RULE 14 — Missing required documentation
If a claim references injury or significant damage but does not mention any supporting documentation (police report, medical record, photos), note this in the reasoning field as a flag for manual follow-up, without downgrading confidence unless the description itself is too vague to categorize.

RULE 15 — Off-topic / non-claim input
Messages unrelated to an insurance claim, accident, policy question, or claim status — such as general conversation, unrelated questions, greetings, or test input with no insurance-relevant content — should be categorized as "Out of Scope", NOT "Insufficient Information". Route to "Automated Response", NOT "Manual Review Team", since these messages do not require human claims-handling attention and should not consume reviewer time. Priority Low, confidence Low, with reasoning noting the message appears unrelated to an insurance claim.