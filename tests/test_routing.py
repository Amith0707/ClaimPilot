import pytest
from model import load_and_route

REQUIRED_FIELDS = {"category", "priority", "assigned_team", "reasoning", "confidence"}

test_batch = [
    "broken",
    "help",
    "...",
    "THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!",
    "This is RIDICULOUS, nothing works and I've been waiting 3 days!!!",
    "I am SO ANGRY right now, this whole company is a joke",
    "I am angry",
    "i'm hurt",
    "Another car hit mine and I think I hurt my back a little",
    "My lawyer said I should report that I hurt my shoulder in the crash",
    "Minor scratch on my bumper, repair estimate is 8 lakh rupees",
    "This is my third claim this month, similar to the last one",
    "My passenger is not breathing and we need an ambulance, this just happened",
    "There has been a fatality in this accident",
    "Just checking on the status of claim number 4521",
    "I've called three times about claim 4521 and still no update, it's been THREE WEEKS",
    "Does my policy cover rental car reimbursement?",
    "I hit another car and the other driver says their neck hurts",
    "This is RIDICULOUS, my lawyer is involved because I got badly hurt and the other driver's damage claim looks fake to me",
    "Mera car accident ho gaya aur mujhe chot lagi hai",
    "The other driver and I settled privately in cash but now my policy renewal shows an open claim against me and the garage is billing my insurer for repairs I already paid for myself",
    "12345",
    "What's the weather like today?",
    "",  # true blank input
]


@pytest.mark.parametrize("claim", test_batch)
def test_claim_routing_returns_valid_json(claim):
    """M4S1/M4S2 — valid structured output with all required fields, no crashes."""
    result = load_and_route(claim)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    missing = REQUIRED_FIELDS - result.keys()
    assert not missing, f"Missing fields: {missing}"

expected_results = {
    # Zero-reference messages -> Insufficient Information / Automated Response
    "broken": {
        "assigned_team": "Automated Response",
    },
    "help": {
        # Ambiguous between Out of Scope and Insufficient Information — only
        # team assignment matters here, not the exact category label
        "assigned_team": "Automated Response",
    },
    "...": {
        "assigned_team": "Automated Response",
    },
    "i'm hurt": {
        "category": "Insufficient Information",
        "assigned_team": "Automated Response",
    },
    "I am angry": {
        "category": "Insufficient Information",
        "assigned_team": "Automated Response",
    },
    "I am SO ANGRY right now, this whole company is a joke": {
        "assigned_team": "Automated Response",
    },
    "The scratch on my bumper is definitely NOT minor, the repair estimate is 8 lakh rupees which honestly seems right for the damage": {
        "category": "Property Damage",
        "assigned_team": "Auto Claims Team",
    },
    "THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "High",  # "WEEKS" meets the 2+ week threshold
    },
    "This is RIDICULOUS, nothing works and I've been waiting 3 days!!!": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "Medium",  # 3 days < 2-week threshold, no repeat contacts
    },
    "Just checking on the status of claim number 4521": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "Medium",  # neutral first-time check, no threshold met
    },
    "I've called three times about claim 4521 and still no update, it's been THREE WEEKS": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "High",  # multiple thresholds met
    },

    "Another car hit mine and I think I hurt my back a little": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "My lawyer said I should report that I hurt my shoulder in the crash": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "I hit another car and the other driver says their neck hurts": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "This is RIDICULOUS, my lawyer is involved because I got badly hurt and the other driver's damage claim looks fake to me": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },

    "My passenger is not breathing and we need an ambulance, this just happened": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
        "priority": "High",
    },
    "There has been a fatality in this accident": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
        "priority": "High",
    },

    "Minor scratch on my bumper, repair estimate is 8 lakh rupees": {
        "category": "Fraud Review",
        "assigned_team": "Fraud Investigation Unit",
    },
    "This is my third claim this month, similar to the last one": {
        "category": "Fraud Review",
        "assigned_team": "Fraud Investigation Unit",
    },
    "The other driver and I settled privately in cash but now my policy renewal shows an open claim against me and the garage is billing my insurer for repairs I already paid for myself": {
    # Genuinely ambiguous by design — model has landed on Fraud Review, Litigation,
    # or Insufficient Information across iterations, all defensible reads. What
    # matters is a substantive, non-trivial category with real reasoning, not a
    # crash or a forced default.
    },

    "Does my policy cover rental car reimbursement?": {
        "category": "General Inquiry",
        "assigned_team": "Customer Support Team",
    },

    "What's the weather like today?": {
        "category": "Out of Scope",
        "assigned_team": "Automated Response",
    },
    "12345": {
        "assigned_team": "Automated Response",
    },
    "": {
        "assigned_team": "Automated Response",
    },
}


@pytest.mark.parametrize("claim,expected", expected_results.items())
def test_claim_routing_correctness(claim, expected):
    result = load_and_route(claim)
    for key, value in expected.items():
        assert result[key] == value, (
            f"Claim: {claim!r}\n"
            f"Expected {key}={value!r}, got {result[key]!r}\n"
            f"Full result: {result}"
        )

def test_angry_tone_routes_correctly():
    """mentor's exact test input: message HAS a reference ('nothing works',
    '3 days'), so tone alone must not push it to Insufficient Information."""
    result = load_and_route("This is RIDICULOUS, nothing works and I've been waiting 3 days!!!")
    assert result["category"] not in {"Litigation", "Fraud Review", "Personal Injury"}
    assert result["assigned_team"] == "Customer Support Team"


def test_short_message_graceful_fallback():
    """'broken' has zero reference, must fall back gracefully via automation,
    not crash and not consume human review time."""
    result = load_and_route("broken")
    assert result["category"] in {"Insufficient Information", "Out of Scope"}
    assert result["assigned_team"] == "Automated Response"
    assert result["confidence"] == "Low"


def test_ambiguous_claim_reasoning_justifies_choice():
    """a claim fitting two categories must have reasoning that explains
    the tiebreak, not just state a category."""
    result = load_and_route("Another car hit mine and I think I hurt my back a little")
    assert result["category"] == "Personal Injury"
    assert len(result["reasoning"]) > 20
    reasoning_lower = result["reasoning"].lower()
    assert any(word in reasoning_lower for word in ["injury", "precedence", "takes", "over", "rule"]), (
        f"Reasoning does not appear to justify the tiebreak: {result['reasoning']}"
    )


def test_priority_defensibility_known_severity():
    """known-severity tickets must land on defensible, contrasting priorities."""
    severe = load_and_route("There has been a fatality in this accident")
    assert severe["priority"] == "High"

    trivial = load_and_route("Does my policy cover rental car reimbursement?")
    assert trivial["priority"] == "Low"


def test_pure_venting_does_not_reach_humans():
    """Design rule — pure venting with zero reference must not consume Manual Review time."""
    result = load_and_route("I am angry")
    assert result["assigned_team"] == "Automated Response"


def test_message_with_concrete_reference_is_not_insufficient_info():
    """Design rule — ANY concrete reference (car, claim, time waited) must route
    past Rule 10, regardless of how emotional the tone is."""
    result = load_and_route("THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!")
    assert result["category"] != "Insufficient Information"
    assert result["assigned_team"] == "Customer Support Team"

def test_ambiguous_multi_signal_claim_gets_substantive_handling():
    """Genuinely ambiguous, content-rich claim — any of several categories is
    defensible; what matters is it's handled substantively, not trivially dismissed."""
    result = load_and_route(
        "The other driver and I settled privately in cash but now my policy renewal "
        "shows an open claim against me and the garage is billing my insurer for "
        "repairs I already paid for myself"
    )
    assert result["category"] in {"Fraud Review", "Litigation", "Insufficient Information"}
    assert len(result["reasoning"]) > 20