# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app
from flask import Flask

import tradesignals

initialize_app()  # if needed
app = Flask(__name__)

@app.route('/')
def home():
	return 'Hello from the home page!'

@app.route('/about')
def about():
	return 'This is the about page!'

@app.route('/tradesignals')
def contact():
	return tradesignals.main("data/tickers_nse50.txt")
 	# return "Hello from the tradesignals page!"
  
@https_fn.on_request(
    timeout_sec=300,
    memory=1024
)
def amazing_stocks_be(req: https_fn.Request) -> https_fn.Response:
	with app.request_context(req.environ):
		response = app.full_dispatch_request()
	return response