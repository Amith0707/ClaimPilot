import time
from flask import Flask,render_template,request
from model import load_and_route

app=Flask(__name__)

@app.route("/",methods=['GET','POST'])
def index():
    result=None
    claim_text=""
    elapsed_ms=None

    if request.method=='POST':
        claim_text=request.form.get("claim_text","").strip()
        start=time.time()
        result=load_and_route(claim_text)
        elapsed_ms=round((time.time()-start)*1000)

    return render_template(
        "index.html",
        result=result,
        claim_text=claim_text,
        elapsed_ms=elapsed_ms
    )

if __name__=="__main__":
    app.run(debug=True,port=5000)