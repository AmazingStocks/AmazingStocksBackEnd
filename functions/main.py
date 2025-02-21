# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app, auth, credentials
from flask import Flask, abort, request
import json
import tradesignals

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

@app.route('/tradesignals/<segment>')
def tradesignals_segment(segment):
    # Call run_backtests with the provided segment parameter
    signals = tradesignals.run_backtests(segment)
    # Return signals as JSON if not already a string
    return signals if isinstance(signals, str) else json.dumps(signals)

@https_fn.on_request(
    timeout_sec=300,
    memory=1024
)
def amazing_stocks_be(req: https_fn.Request) -> https_fn.Response:
	#decoded_token = verify_firebase_token(req)
	with app.request_context(req.environ):
		response = app.full_dispatch_request()
	return response