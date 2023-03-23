from flask import (
    abort,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
import json
import requests
import secrets
import string
from urllib.parse import urlencode

from . import endpoints

from server import app

# TODO refactor all of this to use JWTs

# TODO the "session" is just a cookie. Use this to store all session state info (except JWTs) and have the app send
#  it in requests

jwt = JWTManager(app)


@app.route('/')
def index():  # put application's code here
    return redirect(url_for('show_history'))


@app.route('/login/')
def login():
    """
    Handle logging in and authenticating with Spotify
    """

    # generate random 16-character state string to identify this login request
    state = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))

    # API scopes that our application will need
    scope = ' playlist-modify-private playlist-modify-public ' \
            'user-read-recently-played'

    url_parameters = {
        'client_id': app.config.get('CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': app.config.get('REDIRECT_URI'),
        'state': state,
        'scope': scope
    }

    # android app will create a WebView for the user to log in, which will handle the redirect
    res = make_response(redirect(f'{endpoints.AUTH_URL}/?{urlencode(url_parameters)}'))
    res.set_cookie('spotify_auth_state', state)

    return res


@app.route('/logout/')
def logout():
    # TODO implement this (invalidate JWT)
    abort(404)


@app.route('/callback/')
def callback():
    spotify_state = request.args.get('state')
    login_state = request.cookies.get('spotify_auth_state')

    # check that state set during /login/ request matches spotify's auth server's state
    if spotify_state is None or spotify_state != login_state:
        app.logger.error('Error message: %s', repr(request.args.get('error')))
        app.logger.error('State mismatch: %s != %s', login_state, spotify_state)
        abort(400)

    # headers to get an access token with the authorization code
    auth_headers = {
        'grant_type': 'authorization_code',
        'code': request.args.get('code'),
        'redirect_uri': app.config.get('REDIRECT_URI')
    }

    res = requests.post(endpoints.TOKEN_URL,
                        auth=(app.config.get('CLIENT_ID'), app.config.get('CLIENT_SECRET')),
                        data=auth_headers)
    res_data = res.json()

    if res_data.get('error') or res.status_code != 200:
        app.logger.error(
            'Failed to receive token: %s',
            res_data.get('error', 'No error information received.'),
        )
        abort(res.status_code)

    session['tokens'] = {
        'access_token': res_data.get('access_token'),
        'refresh_token': res_data.get('refresh_token')
    }

    # TODO create JWT and save it to `session`

    return redirect(url_for('show_history'))


def get_token_header():
    if 'tokens' not in session:
        app.logger.error('No tokens in session')
        abort(400)
    return {'Authorization': f"Bearer {session['tokens'].get('access_token')}"}


@app.route('/history/')
def show_history():
    if 'tokens' not in session:
        # user is not logged in, redirect them to login page
        return redirect(url_for('login'))
    headers = get_token_header()
    parameters = {'limit': 50}

    res = requests.get(f'{endpoints.HISTORY_URL}/?{urlencode(parameters)}', headers=headers)
    res_data = res.json()

    if res.status_code != 200:
        app.logger.error(
            'Failed to get listening history info: %s',
            res_data.get('error', 'No error message returned.'),
        )
        abort(res.status_code)

    return [f'{track_info["track"]["name"]} - {track_info["track"]["artists"][0]["name"]} - {track_info["played_at"]}'
            for track_info in res_data['items']]


@app.route('/user/')
def user():
    if 'tokens' not in session:
        return redirect(url_for('login'))
    headers = get_token_header()
    res = requests.get(endpoints.ME_URL, headers=headers)
    res_data = res.json()

    return res_data
