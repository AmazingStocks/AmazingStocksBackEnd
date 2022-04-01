from flask import Flask
from yahoo_fin import stock_info as si

application = Flask(__name__)

@application.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@application.route("/getallSymbols", methods=["GET"])
def getAllSymbols():
    lst = si.tickers_nifty50()
    ret = dict()
    ret['symbols'] = lst
    return ret


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()