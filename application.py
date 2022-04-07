from flask import Flask
from yahoo_fin import stock_info as si
from flask_awscognito import AWSCognitoAuthentication
import os


application = Flask(__name__)

application.config['AWS_DEFAULT_REGION'] = os.environ['AWS_DEFAULT_REGION']
application.config['AWS_COGNITO_DOMAIN'] = os.environ['AWS_COGNITO_DOMAIN']
application.config['AWS_COGNITO_USER_POOL_ID'] = os.environ['AWS_COGNITO_USER_POOL_ID']
application.config['AWS_COGNITO_USER_POOL_CLIENT_ID'] = os.environ['AWS_COGNITO_USER_POOL_CLIENT_ID']
application.config['AWS_COGNITO_USER_POOL_CLIENT_SECRET'] = os.environ['AWS_COGNITO_USER_POOL_CLIENT_SECRET']
application.config['AWS_COGNITO_REDIRECT_URL'] = os.environ['AWS_COGNITO_REDIRECT_URL']

aws_auth = AWSCognitoAuthentication(application)



@application.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@application.route("/getallSymbols", methods=["GET"])
@aws_auth.authentication_required
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