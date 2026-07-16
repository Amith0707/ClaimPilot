# ClaimBot AI — Engineering & Debugging Log

This document records the iterative testing, debugging, and hardening process
behind the routing logic — organized by phase and finding, not as a day-by-day
diary. It captures every significant failure discovered, how it was
root-caused, and how it was fixed, across three escalating rounds of testing:
baseline correctness testing, targeted rule-boundary tightening, and
adversarial/real-use-case stress-testing.

## Table of contents

- [Phase 1 — Baseline correctness testing](#phase-1--baseline-correctness-testing)

- [Phase 2 — Design-level finding: Manual Review Team receiving non-claim messages](#phase-2--design-level-finding-manual-review-team-receiving-non-claim-messages)

- [Phase 3 — Boundary tightening after further live testing](#phase-3--boundary-tightening-after-further-live-testing)

- [Phase 4 — Adversarial stress-testing](#phase-4--adversarial-stress-testing)

- [Phase 5 — Real-use-case validation](#phase-5--real-use-case-validation)

- [Phase 6 — Retrieval depth (k) validation](#phase-6--retrieval-depth-k-validation)

- [Cross-cutting: provider swap during testing](#cross-cutting-provider-swap-during-testing)

- [Summary of all fixes](#summary-of-all-fixes)

- [Known limitations (documented, not fixed in v1)](#known-limitations-documented-not-fixed-in-v1)

---

## Phase 1 — Baseline correctness testing

**Suite:** `tests/test_routing.py`, initial run
**Result:** 38 passed / 4 failed (42 total)

Structural reliability (valid JSON, all fields present, no crashes): **19/19
passed**, including adversarial inputs (empty string, non-English text,
off-topic questions, pure numbers). This confirmed the schema enforcement
layer (LLM tool-use + Pydantic validation) was solid from the start.

Correctness (actual routing decision matches expected): **15/19 passed**,
4 failed. Each failure was investigated against three hypotheses:

- **(A) Policy manual ambiguity** — the rule itself under-specified, or
  missing precedence against another rule
- **(B) Model-specific reasoning failure** — the LLM mis-weighs retrieved
  rules inconsistently
- **(C) RAG-specific failure** — retrieval surfaces the wrong/insufficient
  rules, so the LLM never had the right context

**Outcome across all 4 failures: every one traced back to (A) — rule
ambiguity or missing precedence in the policy manual**, not model reasoning
or retrieval quality on their own — though one failure did surface a real
structural retrieval weakness for a specific *type* of rule (detailed below).

### Failure 1 — Incidental legal mention over-triggered Litigation

**Input:** "My lawyer said I should report that I hurt my shoulder in the crash"
**Expected:** Personal Injury — **Got:** Litigation

**Root cause:** Rule 5 originally read:

Any claim containing legal language such as "attorney," "lawyer," "sue,"
"lawsuit," or "legal action" is categorized as Litigation and routed to
Legal Team with priority High, regardless of the underlying incident type.


This didn't distinguish adversarial legal language ("I'm suing them") from
incidental mentions ("my lawyer told me to report this"). Any mention of a
lawyer, in any context, triggered full Litigation routing.

**Fix — rewrote Rule 5 to require adversarial intent:**

A claim is categorized as Litigation and routed to Legal Team with priority
High only when the legal language indicates active or adversarial legal
action against the insurer — such as "I'm suing," "my lawyer is filing a
suit," "we are pursuing legal action," or "I've retained an attorney to
take action against you." Incidental mentions of legal counsel — such as a
lawyer merely advising the claimant on how to report or document a claim
("my lawyer said I should report this") — do NOT trigger Litigation on
their own. In such incidental cases, categorize based on the substantive
content of the claim (injury, damage, etc.) per the normal precedence
rules, and note the incidental legal mention in the reasoning field
without it driving the category.

**Re-test:** PASSED — correctly returns Personal Injury.

### Failure 2 — Cost/severity mismatch not flagged as fraud

**Input:** "Minor scratch on my bumper, repair estimate is 8 lakh rupees"
**Expected:** Fraud Review — **Got:** Property Damage (High priority)

**Root cause:** Rule 2 (cost escalation) and Rule 6 (severity/cost mismatch)
both applied with no stated precedence between them. The model's choice of
Rule 2 was logically defensible given the ambiguity — it simply had no
instruction that Rule 6 should win.

**Fix:** Strengthened Rule 6 with imperative, unambiguous precedence
language ("MUST be categorized as Fraud Review... NOT Property Damage"),
explicitly stating it outranks Rule 2 when severity language contradicts
the stated cost. Confirmed via direct retrieval testing that Rule 6 *was*
already being retrieved alongside Rule 2 in every relevant case — the gap
was in the model's weighting of the two rules, not retrieval.

**Re-test:** PASSED — correctly returns Fraud Review.

### Failure 3 — Frustration/delay priority threshold under-specified

**Input:** "I've called three times about claim 4521 and still no update,
it's been THREE WEEKS"
**Expected:** High priority — **Got:** Medium priority

**Root cause, first hypothesis:** qualitative thresholds ("frustration,"
"long delay") without concrete numbers — categorized as (A).

**First fix attempt failed:** adding numeric thresholds directly to a
standalone Rule 9 did not resolve the issue. Direct retrieval diagnostics
(`retrieve_rules()` run manually against this exact input) showed **Rule 9
was not being retrieved at all, even at k=8 out of 16 total rules**,
despite the strengthened wording. This ruled out simple wording ambiguity
and pointed to a structural retrieval problem specific to this rule.

**Why retrieval kept missing Rule 9:** it functioned as a cross-cutting
*priority modifier* layered on top of a category rule, using vocabulary
("weeks," "frustration," "repeated") that overlapped semantically with
several unrelated rules (anger/tone, severity, fraud timelines). This
diluted its embedding-similarity signal in a way rewording alone couldn't
fix — unlike an earlier, successful fix to Rule 4 (severity language),
where the missing terms were rare/specific enough that adding them created
an unambiguous match.

**Actual fix:** merged Rule 9's priority logic directly into Rule 8 (the
category rule it modifies), removing it as a standalone retrieval target
entirely. Since Rule 8 is reliably retrieved for all status-inquiry claims,
its priority logic can no longer be lost separately.

**Re-test:** PASSED — priority now correctly returns High.

**Generalizable finding:** modifier rules (priority/tone qualifiers layered
on a category, rather than defining one) are structurally more prone to
retrieval under-ranking than category-defining rules in a small-corpus RAG
setup. Merging modifiers into their parent rule is a more robust fix than
reformulating them as standalone entries.

### Failure 4 — Same precedence rule applied inconsistently across similar inputs

**Input:** "This is RIDICULOUS, my lawyer is involved because I got badly
hurt and the other driver's damage claim looks fake to me"
**Original expected:** Litigation — **Got:** Personal Injury

**Initial concern:** this looked like genuine (B) model inconsistency — the
same claimed precedence order that (seemingly) applied in Failure 1 wasn't
being applied here, on a structurally similar input.

**Resolution:** once Rule 5 was fixed (Failure 1), this input's legal
mention ("my lawyer is involved") was correctly recognized as incidental,
not adversarial — for the identical reason as Failure 1. The original
*expected value* for this test case had itself been based on the old,
overly-broad Rule 5, and was corrected to Personal Injury.

**Conclusion: this was never genuine model inconsistency.** It was the same
rule ambiguity as Failure 1, surfacing on a second input. Fixing the shared
root cause resolved both cases identically — no model-comparison experiment
was needed to confirm this, contrary to the original suspicion.

**Result of Phase 1: 42/42 passed** after all four fixes above.

---

## Phase 2 — Design-level finding: Manual Review Team receiving non-claim messages

**Discovered during manual UI testing, not from the automated suite.**

Off-topic, non-insurance messages (e.g., "What's the weather like today?")
were routing to `Insufficient Information` / `Manual Review Team` — the
same human queue as genuinely ambiguous claim attempts. This meant human
reviewers would waste time opening messages that were never claims at all.

**Fix:** introduced a new category/team pair specifically for non-claim
input:
- `"Out of Scope"` → `"Automated Response"` (no human review needed)
- Kept `"Insufficient Information"` → `"Manual Review Team"` reserved for
  messages that plausibly ARE claim attempts, just too vague to categorize

**Follow-up regression found:** the model then over-applied "Out of Scope"
to genuine insurance questions (e.g., "Does my policy cover rental car
reimbursement?"), misreading them as non-claims. Fixed with an explicit
system-prompt boundary: "Out of Scope" requires zero insurance relevance;
genuine coverage/policy questions remain "General Inquiry" regardless of
whether an incident is reported.

**Why this mattered beyond the test suite passing:** the entire point of
automated routing is to reduce human review load. Silently routing
non-claims into the human queue would have partially defeated the system's
own purpose — a business-logic gap, not a technical one, and one that no
automated test would have caught on its own. Found through deliberate
manual review of model output.

---

## Phase 3 — Boundary tightening after further live testing

Continued manual and live-UI testing surfaced three more specific gaps,
each addressed and re-verified:

### Injury keywords without accident context
**Input:** "i'm hurt" (no vehicle/accident mention at all)
Was routing to Personal Injury on injury-keyword match alone. **Fixed** by
adding an explicit requirement to Rule 3: injury language must co-occur
with some vehicle/accident/collision context to trigger Personal Injury;
otherwise, route to Insufficient Information.

### Pure emotional venting misclassified as General Inquiry
**Input:** "I am angry" (no claim reference, no question)
Was being force-fit into General Inquiry despite containing no answerable
question. **Fixed** by rewriting Rule 9 (General Inquiry) to require an
identifiable, answerable topic, and Rule 10 (Insufficient Information) to
explicitly claim zero-reference emotional venting.

### Tone-driven priority inflation
**Input:** "I am very angry my issue is not resolved yet"
Was receiving High priority off tone alone, without meeting any of Rule 8's
concrete escalation thresholds (2+ weeks pending, 2+ contact attempts,
explicit no-update phrases). **Fixed** by making Rule 8 explicit that
emotional tone alone never satisfies an escalation threshold — only
concrete, statable conditions do.

### Redesigning the Insufficient Information / Manual Review boundary

A deeper design question emerged from the above: **should every vague
message go to Manual Review Team, even when a human could do nothing with
it beyond asking for clarification?** The answer was no — this was
identified as an unnecessary drain on the same limited human-review
resource the "Out of Scope" fix (Phase 2) was meant to protect.

**Redesign:** `Insufficient Information` now splits by actionability:
- **Zero-reference messages** ("broken," "help," "i'm hurt," "I am angry")
  → `Automated Response` (a human has no more to work with than the model
  does; the correct action is an automated request for more detail)
- **Content-rich but genuinely unclassifiable messages** (specific,
  detailed, but self-contradictory or spanning categories the precedence
  rules can't resolve) → `Manual Review Team` (reserved ONLY for cases
  where a human genuinely has more context to work with than the model)

This redesign required re-running and correcting a substantial portion of
the test suite, since several previously-passing test expectations were
themselves based on the older, less precise routing logic.

**Regression found during this redesign:** tightening the "vague message"
boundary initially overcorrected — messages that DID contain a real
reference (e.g., "MY CAR HAS BEEN SITTING FOR WEEKS") were briefly
misrouted to Insufficient Information, because the new language wasn't
specific enough about what counts as a "reference." Fixed by making Rule 8
explicitly list example reference patterns (a car, a claim number, a
stated time period) and stating that heavy emotional tone does not
disqualify a message from this category if any such reference is present.

**Result after this phase: 53/53 passed** (test suite expanded to cover
each new boundary case).

---

## Phase 4 — Adversarial stress-testing

Once the rule set stabilized, deliberately adversarial inputs were
constructed to probe for failure modes the existing test suite wouldn't
catch — inputs designed to exploit the *specific wording* of recently
strengthened rules, not just generic edge cases.

### Real bug found: negation blindness in Rule 6

**Input:** "The scratch on my bumper is definitely NOT minor, the repair
estimate is 8 lakh rupees which honestly seems right for the damage"

**Result before fix:** Fraud Review, High priority — **incorrectly
flagging an honest customer for suspected fraud.**

**Root cause:** Rule 6's explicit trigger-word list (added in Phase 1 to
fix Failure 2) included "minor" as a minimizing-language signal. The model
pattern-matched on the literal word "minor" appearing near a high cost
figure, without processing that the word was negated ("NOT minor") — i.e.,
the claimant was asserting the damage genuinely matched the cost, not
minimizing it.

**Severity of this finding:** this is arguably the most consequential bug
found in the whole project — a false fraud accusation against a genuine
claim is a serious real-world harm, not just a misrouting. Caught
specifically because adversarial testing targeted the exact wording just
added to fix an earlier failure, rather than only testing generic phrasing.

**Fix:** added explicit negation-handling instructions to Rule 6: minimizing
words that are negated or contradicted do not count as minimizing language;
the rule must be applied based on the sentence's actual asserted meaning,
not merely the presence of trigger words.

**Re-test:** PASSED — correctly returns Property Damage, not Fraud Review.
Added as a permanent regression test.

### Other adversarial cases tested (no bugs found)

- **Self-contradictory injury report** ("no injuries... but my neck has
  been stiff since") — handled well: fell back to Insufficient Information
  with Low confidence rather than confidently guessing either way.
- **Threshold precision** ("13 days" + "two emails," one threshold missed,
  one met) — correctly resolved to High priority via the contact-attempts
  threshold, with both facts cited in reasoning.
- **Negated legal language** ("retained an attorney, but... no intention
  of taking action") — correctly did NOT trigger Litigation, confirming
  Rule 5's own negation-handling (fixed earlier, in Phase 1) held up under
  a fresh adversarial phrasing.
- **Multi-signal "kitchen sink" input** (legal + fraud + severe injury +
  status escalation, all at once) — resolved via Rule 12's precedence
  order with reasoning that visibly walked the competing signals, though
  with one minor miss (didn't flag top-severity language per Rule 4
  alongside the Litigation categorization).

### Documented, unfixed limitation: disputed third-party injury claims

**Input:** "The person I hit is claiming a neck injury but he walked away
completely fine and was laughing with his friends after"

The system correctly applies Rule 3 (injury + accident context → Personal
Injury) but does not recognize that the *claimant* is expressing skepticism
about someone *else's* injury claim — a meaningfully different situation
than a first-party injury report, and arguably a fraud-adjacent signal in
its own right. Not fixed in v1: this requires reasoning about whose claim
is being made and the speaker's stated belief about its legitimacy, a
harder NLU task than the rest of the rule set handles. Documented rather
than patched, to avoid rushing a fix for a genuinely hard problem this
close to completion.

---

## Phase 5 — Real-use-case validation

To answer "does the output actually solve the stated business problem"
directly, the system was tested against deliberately unfiltered, realistic
customer language — messages written to sound like real, unedited claim
submissions rather than constructed to hit a specific rule.

**Result: 4 of 6 test messages handled cleanly with no notes.** Two
surfaced genuine, minor scope gaps rather than bugs:

1. **No billing/coverage-dispute category.** A message combining a towing
   fee dispute with an unresponsive-company complaint routed to Claim
   Status Inquiry — the closest existing category, correctly applied given
   the taxonomy, but revealing that the 7-category design was built around
   accident triage, not billing disputes.
2. **Hit-and-run circumstances aren't specifically surfaced.** A claim
   mentioning a hit-and-run (no plate number, other driver fled) routed
   correctly on injury/damage content, but the hit-and-run circumstance
   itself wasn't flagged in reasoning, despite materially affecting how a
   real claims team would need to handle documentation.

Both are logged as scoped v2 considerations rather than v1 defects — the
core routing logic generalized well to authentic, unfiltered input.

---

## Phase 6 — Retrieval depth (k) validation

Once the rule set stabilized at 55/55 passing tests, the retrieval depth
(`k=8`) itself was tested directly rather than left as an assumed default,
to confirm it wasn't simply carried over from earlier debugging without
being re-justified against the final, consolidated rule set.

**Method:** the full test suite was re-run with `k` temporarily lowered to
3 and to 5, with no other code or rule changes, then restored to 8.

**Result:**

| k | Result | Failure(s) |
|---|---|---|
| 3 | 53/55 passed | "MY CAR HAS BEEN SITTING FOR WEEKS" downgraded to Medium priority (Rule 8 retrieved, but without enough of its threshold detail); a multi-signal legal/injury/fraud claim fell through to Insufficient Information entirely |
| 5 | 53/55 passed | The same "SITTING FOR WEEKS" claim fell through to Insufficient Information completely — a *worse* failure than at k=3, not a better one |
| 8 | 55/55 passed | None |

**Why k=5 failed worse than k=3 on the same claim:** counterintuitively,
failures did not scale monotonically with k. At k=5, whatever rules were
retrieved for the "SITTING FOR WEEKS" claim apparently crowded out Rule 8
entirely — likely Rule 13 (angry tone) or Rule 15 (off-topic) ranking
competitively enough to displace it at that window size. At k=3, Rule 8
was retrieved but without its full threshold-detail context, which was
enough to be applied at all, just applied conservatively. This indicates
that the specific rules included in the retrieved set matter as much as
how many are included — a small increase in k doesn't guarantee smooth
improvement.

**Token cost check:** at k=8, each call includes roughly 1,400 tokens of
rule context, out of a 128,000-token context window — under 1.5% of
capacity. Combined with GPT-4o-mini's per-token pricing, this represents a
negligible cost difference from k=3 or k=5 at the project's current scale
(~15 rules). The token savings from a lower k were not judged worth the
demonstrated correctness risk.

**Conclusion:** `k=8` is not an arbitrary or historically-inherited value —
it is the minimum tested depth with zero known failures against the full
test suite, and the token cost difference versus smaller values is
negligible at this policy manual size. If the manual grows substantially
larger, this tradeoff would need to be re-evaluated, since token cost
scales with corpus size in a way it does not at the current scale.

---

## Cross-cutting: provider swap during testing

Partway through Phase 1 testing, Groq's free-tier daily token cap (100K
TPD) was reached mid-session. Since the pipeline's retrieval, prompt
construction, and validation logic are all independent of which LLM
provider is called, switching from Groq (Llama 3.3 70B) to OpenAI
(GPT-4o-mini) required changing only the client initialization in
`model.py`. All previously-passing tests continued to pass after the
swap with no other code changes — a real, tested demonstration of the
architecture's provider independence, not a design claim made without
evidence.

---

## Summary of all fixes

| Rule/Component | Issue | Fix | Result |
|---|---|---|---|
| Rule 5 (Litigation) | Any lawyer mention triggered Litigation | Required adversarial legal intent | Fixed Failures 1 & 4 |
| Rule 6 (Fraud Review) | No precedence over Rule 2 on cost mismatch | Added imperative precedence language | Fixed Failure 2 |
| Rule 6 (Fraud Review) | Negation blindness — false fraud accusation | Added explicit negation-handling instructions | Fixed via stress-testing |
| Rule 8/9 (Status Inquiry) | Priority modifier rule under-retrieved | Merged Rule 9 into Rule 8 | Fixed Failure 3 |
| Rule 3 (Personal Injury) | Injury keywords without accident context over-triggered | Required accompanying vehicle/accident context | Fixed via live testing |
| Rule 9/10 boundary | Pure venting force-fit into General Inquiry | Required identifiable question for General Inquiry | Fixed via live testing |
| Rule 8 (Status Inquiry) | Tone alone inflated priority | Required concrete, statable thresholds | Fixed via live testing |
| Category/team design | Manual Review Team receiving non-claim messages | Added Out of Scope / Automated Response pair | Fixed via manual review |
| Category/team design | Manual Review Team receiving unactionable vague messages | Split Insufficient Information by actionability | Redesigned |
| Retrieval config | Rules occasionally missed at low k | Bumped k from 5 to 8 | Safety margin |
| Infrastructure | Groq free-tier rate limit hit mid-testing | Swapped to OpenAI provider | Confirmed provider-agnostic design |

**Final test suite: 55/55 passed**, covering structural reliability, all
mission-required edge cases, threshold precision, negation handling, and
multi-signal precedence.

---

## Known limitations (documented, not fixed in v1)

1. **Disputed third-party injury claims** are not specially flagged —
   see Phase 4.
2. **No billing/coverage-dispute category** — see Phase 5.
3. **Hit-and-run circumstances** aren't surfaced in reasoning even when
   present — see Phase 5.
4. **Consistency on genuinely borderline priority calls** (e.g., ambiguous
   injury severity language) can vary slightly between runs, since the LLM
   is not fully deterministic even at low temperature — observed during
   early development, not fully re-verified after the final rule set
   stabilized.

Each of the above was identified through deliberate testing adversarial
stress-testing or unfiltered real-use-case validation rather than left
undiscovered.