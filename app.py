import time
from flask import Flask, render_template, request, jsonify
from model import load_and_route
from db import init_db,save_claim,get_all_claims
app = Flask(__name__)
init_db()

DEMO_TICKETS = [
    "broken",
    "help",
    "...",
    "THIS IS RIDICULOUS!!! MY CAR HAS BEEN SITTING FOR WEEKS AND NO ONE IS HELPING ME!!!",
    "I am SO ANGRY right now, this whole insurance company is a joke",
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
    "There was a hit and run case my scooty got damaged and I have filed a court case on the person based on my lawyers suggestions",
    "What's the weather like today?",
    "My car was rear-ended at a signal. Passenger has minor neck pain. Police report attached.",
]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html",tickets=DEMO_TICKETS)

@app.route("/api/route", methods=["POST"])
def api_route():
    data = request.get_json()
    claim_text = data.get("claim_text", "").strip()

    start = time.time()
    result = load_and_route(claim_text)
    elapsed_ms = round((time.time() - start) * 1000)
    result["elapsed_ms"] = elapsed_ms
    save_claim(claim_text, result, elapsed_ms, source="single")
    print("Saved to DB successfully")

    return jsonify(result)

@app.route("/api/route-batch", methods=["POST"])
def api_route_batch():
    data = request.get_json()
    indices = data.get("indices", [])  # list of ticket indices to run, or empty = all

    tickets_to_run = (
        [DEMO_TICKETS[i] for i in indices] if indices else DEMO_TICKETS
    )

    results = []
    for claim_text in tickets_to_run:
        start = time.time()
        try:
            result = load_and_route(claim_text)
            elapsed_ms = round((time.time() - start) * 1000)
            result["elapsed_ms"] = elapsed_ms
            result["claim_text"] = claim_text
            result["error"] = None
            save_claim(claim_text, result, elapsed_ms, source="batch")
        except Exception as e:
            result = {
                "claim_text": claim_text,
                "error": str(e),
                "elapsed_ms": round((time.time() - start) * 1000)
            }
        results.append(result)

    return jsonify(results)

@app.route("/history")
def history():
    claims = get_all_claims(limit=50)
    return render_template("history.html", claims=claims)

if __name__ == "__main__":
    app.run(debug=True, port=5000)