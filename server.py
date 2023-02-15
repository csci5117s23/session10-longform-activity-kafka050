import flask
import os
import json
import db
app = flask.Flask(__name__)


from authlib.integrations.flask_client import OAuth
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

@app.before_first_request
def setup():
   db.setup()

@app.route("/")
def home():
    return flask.render_template('home.html')

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=flask.url_for("callback", _external=True)
    )
@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    flask.session['name'] = token['userinfo']['given']
    flask.session['uid'] = token['userinfo']['sid']
    flask.session['email'] = token['userinfo']['email']
    flask.session['picture'] = token['userinfo']['picture']
    return flask.redirect("/")

@app.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect(
        "https://"
        + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + flask.urlencode(
            {
                "returnTo": flask.url_for("home", _external=True),
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=flask.quote_plus,
        )
    )

@app.route('/survey', methods=['GET'])
def survey():
   return flask.render_template('survey.html') 

@app.route('/survey', methods=['POST'])
def response():
   # upload results to psql database
   user_name = flask.request.form.get("name")
   topping = flask.request.form.get("type")
   chain = flask.request.form.get("chain")
   suggestion = flask.request.form.get("suggestion")
   if not suggestion:
      db.add_survey_response_no_suggestion(user_name, topping, chain)
   else:
      db.add_survey_response_with_suggestion(user_name, topping, chain, suggestion)
   return flask.redirect('/thanks')

@app.route('/decline', methods=['GET'])
def decline():
   return flask.render_template('decline.html')

@app.route('/thanks', methods=['GET'])
def thanks():
   return flask.render_template('thanks.html')

@app.route('/api/results', methods=['GET'])
def results():
   reverse = flask.request.args.get('reverse')
   results = None
   if reverse == 'true':
      # SQL to retrieve reverse order
      print("getting reverse")
      results = db.get_all_survey_responses_reverse()
   else:
      # SQL to retrieve normal order
      print("getting in order")
      results = db.get_all_survey_responses()
   return results
