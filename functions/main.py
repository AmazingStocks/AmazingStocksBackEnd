# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app, auth, credentials, firestore
from flask import Flask, abort, request
import json
import tradesignals
import back_trade

# Initialize the Firebase Admin SDK (adjust the credentials as needed)
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)


app = Flask(__name__)

def verify_firebase_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        abort(401, description="Missing or invalid token")
    token = auth_header.split('Bearer ')[1]
    try:
        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        abort(401, description=f"Token verification failed: {e}")

@app.route('/')
def home():
	return 'Hello from the home page!'

@app.route('/about')
def about():
	return 'This is the about page!'

@app.route('/tradesignals')  # Original route remains, if needed
def contact():
	return tradesignals.main("data/tickers_nse50.txt")


@app.route('/tradesignals/getresult/<process_id>')
def tradesignals_process(process_id):
    # Call get_backtest_status with the provided process_id
    status = tradesignals.get_backtest_status(process_id)
    if status is None:
        return "Process ID not found", 404
    return status

@app.route('/get-tickers/<segment>', methods=['GET'])
def tget_tickers(segment):
    # Call get_all_tickers with the provided segment parameter
    tickers = tradesignals.get_all_tickers(segment)
    # Return tickers as JSON if not already a string
    return tickers 

@app.route('/tradesignals/<segment>', methods=['POST'])
def tradesignals_segment(segment):
    # Call run_backtests with the provided segment parameter
    signals = tradesignals.run_backtests(segment)
    # Return signals as JSON if not already a string
    return signals 

@app.route('/tradesignal-single/<symbol>', methods=['POST'])
def tradesignal_single(symbol):
    # Call run_backtests with the provided symbol parameter
    signals = tradesignals.run_backtests(symbol, single=True)
    # Return signals as JSON if not already a string
    return signals 

@app.route('/backtrade/<symbol>', methods=['POST'])
def backtrade(symbol):
    return back_trade.backtest(symbol)


@https_fn.on_request(
    timeout_sec=300,
    memory=1024
)
def amazing_stocks_be(req: https_fn.Request) -> https_fn.Response:
	#decoded_token = verify_firebase_token(req)
	with app.request_context(req.environ):
		response = app.full_dispatch_request()
	return response