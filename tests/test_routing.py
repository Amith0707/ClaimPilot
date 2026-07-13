import pytest
from model import load_and_route

REQUIRED_FIELDS = {"category", "priority", "assigned_team", "reasoning", "confidence"}

test_batch = [
    "broken",
    "help",
    "...",
    "THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!",
    "I am SO ANGRY right now, this whole company is a joke",
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
    "12345",
    "What's the weather like today?",
    "",  # true blank input 
]

# Important part
@pytest.mark.parametrize("claim", test_batch)
def test_claim_routing_returns_valid_json(claim):
    """Each claim should return a valid dict with all required fields no crashes, no missing fields."""
    result = load_and_route(claim)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    missing = REQUIRED_FIELDS - result.keys()
    assert not missing, f"Missing fields: {missing}"

expected_results = {
    "broken": {
        "category": "Insufficient Information",
        "assigned_team": "Manual Review Team",
    },
    "help": {
        "category": "Out of Scope",
        "assigned_team": "Automated Response",
    },
    "...": {
        "category": "Insufficient Information",
        "assigned_team": "Manual Review Team",
    },
    "THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "High",
    },
    "I am SO ANGRY right now, this whole company is a joke": {
        "assigned_team": "Customer Support Team",
    },
    "Another car hit mine and I think I hurt my back a little": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "My lawyer said I should report that I hurt my shoulder in the crash": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "Minor scratch on my bumper, repair estimate is 8 lakh rupees": {
        "category": "Fraud Review",
        "assigned_team": "Fraud Investigation Unit",
    },
    "This is my third claim this month, similar to the last one": {
        "category": "Fraud Review",
        "assigned_team": "Fraud Investigation Unit",
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
    "Just checking on the status of claim number 4521": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
    },
    "I've called three times about claim 4521 and still no update, it's been THREE WEEKS": {
        "category": "Claim Status Inquiry",
        "assigned_team": "Customer Support Team",
        "priority": "High",
    },
    "Does my policy cover rental car reimbursement?": {
        "category": "General Inquiry",
        "assigned_team": "Customer Support Team",
    },
    "I hit another car and the other driver says their neck hurts": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "This is RIDICULOUS, my lawyer is involved because I got badly hurt and the other driver's damage claim looks fake to me": {
        "category": "Personal Injury",
        "assigned_team": "Injury Specialists",
    },
    "What's the weather like today?": {
        "category": "Out of Scope",
        "assigned_team": "Automated Response",
    },
    "12345": {
        "category": "Insufficient Information",
        "assigned_team": "Manual Review Team",
    },# blank input 
    "": {
        "category": "Out of Scope",
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

# Standalone test functions in here
def test_short_message_routes_to_manual_review():
    """very short/vague message should fall back gracefully, not crash or force a category."""
    result = load_and_route("broken")
    assert result["category"] == "Insufficient Information"
    assert result["assigned_team"] == "Manual Review Team"


def test_angry_tone_does_not_trigger_wrong_category():
    """angry tone alone should not misroute to Litigation/Fraud/Injury."""
    result = load_and_route("I am SO ANGRY right now, this whole company is a joke")
    assert result["category"] not in {"Litigation", "Fraud Review", "Personal Injury"}


def test_ambiguous_claim_reasoning_mentions_tradeoff():
    """Ambiguous claims should have reasoning that justifies the tiebreak."""
    result = load_and_route("Another car hit mine and I think I hurt my back a little")
    assert result["category"] == "Personal Injury"
    assert len(result["reasoning"]) > 20