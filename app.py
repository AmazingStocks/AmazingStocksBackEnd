

import chalice
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