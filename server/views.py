from flask import (
    abort,
    make_response,
    redirect,
    request,
    session,
    url_for, jsonify,
)
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
import json
import requests
import secrets
import string
from urllib.parse import urlencode

from . import endpoints, db
from .models import SpotifyToken

from server import app

# TODO refactor all of this to use JWTs

jwt = JWTManager(app)


@app.route('/')
def index():  # put application's code here
    return redirect(url_for('show_history'))


@app.route('/login/')
def login():
    """
    Handle logging in and authenticating with Spotify
    """

    # API scopes that our application will need
    scope = ' playlist-modify-private playlist-modify-public ' \
            'user-read-recently-played'

    url_parameters = {
        'client_id': app.config.get('CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': app.config.get('REDIRECT_URI'),
        'scope': scope
    }

    # android app will create a Chrome Custom Tab for the user to log in, which will handle the redirect
    # make_response() could be replaced with returning the redirect directly
    res = make_response(redirect(f'{endpoints.AUTH_URL}/?{urlencode(url_parameters)}'))

    return res


@app.route('/logout/')
def logout():
    # TODO implement this (invalidate JWT)
    abort(404)


@app.route('/callback/', methods=['POST'])
def callback():

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

    spotify_access_token = res_data.get('access_token')
    spotify_refresh_token = res_data.get('refresh_token')
    headers = {'Authorization': f'Bearer {spotify_access_token}'}
    me_res = requests.get(endpoints.ME_URL, headers=headers)
    me_res_data = me_res.json()
    spotify_user_id = me_res_data.get('id')

    existing_st = SpotifyToken.query.filter_by(spotify_id=spotify_user_id).first()
    if existing_st:
        existing_st.access_token = spotify_access_token
        existing_st.refresh_token = spotify_refresh_token
    else:
        st = SpotifyToken(
            spotify_id=spotify_user_id,
            access_token=spotify_access_token,
            refresh_token=spotify_refresh_token
        )
        db.session.add(st)
    db.session.commit()

    client_access_token = create_access_token(identity=spotify_user_id)
    client_refresh_token = create_refresh_token(identity=spotify_user_id)

    return jsonify(clientAccessToken=client_access_token, clientRefreshToken=client_refresh_token)


@app.route('/refresh/', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # TODO do this
    pass


@app.route('/sessions/')
@jwt_required()
def sessions():
    # TODO do this
    return jsonify(sessions=["this is a session"])


@app.route('/session/<session_id>/', methods=['POST'])
@jwt_required()
def session(session_id):
    # TODO do this
    print(f'would have updated/modified session id {session_id}')
    return jsonify(message='success')


@app.route('/activities/')
@jwt_required()
def activities():
    # TODO do this
    return jsonify(activities=["this is an activity"])


@app.route('/activity_playlists/')
@jwt_required()
def activity_playlists():
    # TODO do this
    return jsonify(playlists=["this is an activity playlist"])


def get_token_header():
    if 'tokens' not in session:
        app.logger.error('No tokens in session')
        abort(400)
    print(len(session['tokens'].get('access_token')), len(session['tokens'].get('refresh_token')))
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
@jwt_required()
def user():
    spotify_user_id = get_jwt_identity()
    st = SpotifyToken.query.filter_by(spotify_id=spotify_user_id).first()
    headers = {'Authorization': f'Bearer {st.access_token}'}
    res = requests.get(endpoints.ME_URL, headers=headers)
    res_data = res.json()

    return res_data
