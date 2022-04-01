from flask import Flask
from yahoo_fin import stock_info as si

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/getallSymbols", methods=["GET"])
def getAllSymbols():
    lst = si.tickers_nifty50()
    ret = dict()
    ret['symbols'] = lst
    return ret


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = True
    app.run()