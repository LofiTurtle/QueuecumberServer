from urllib.parse import urlencode

import requests
from apscheduler.schedulers import SchedulerAlreadyRunningError
from flask import (
    abort,
    make_response,
    redirect,
    request,
    jsonify,
)
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager

from server import app
from . import endpoints, db
from .database.datamanager import get_user_listening_history, get_user_activities, listening_history_to_dict
from .database.historytracker import update_user_history
from .models import SpotifyToken
from .utils.backgroundtasks import start_scheduler
from .utils.spotifyapiutil import make_authorized_get_request

jwt = JWTManager(app)


@app.route('/login/')
def login():
    """
    Handle logging in and authenticating with Spotify
    """

    # API scopes that our application will need
    scope = 'playlist-modify-private playlist-modify-public ' \
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

    existing_st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()
    if existing_st:
        existing_st.access_token = spotify_access_token
        existing_st.refresh_token = spotify_refresh_token
    else:
        st = SpotifyToken(
            spotify_user_id=spotify_user_id,
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
    return jsonify(activities=["this is an activity", "Here's another", "wow a third one"])


@app.route('/activity_playlists/')
@jwt_required()
def activity_playlists():
    # TODO do this
    return jsonify(playlists=["this is an activity playlist"])


@app.route('/homepage_info/')
@jwt_required()
def homepage_info():
    spotify_user_id = get_jwt_identity()

    user_activities = get_user_activities(spotify_user_id, limit=3)
    user_activities_dicts = [{
        'name': activity.activity_name
    } for activity in user_activities]

    # TODO do this for real when playlists are working
    user_playlists_dicts = ['playlist 1', 'playlist B', 'playlist III']

    update_user_history(spotify_user_id)
    user_listening_history = get_user_listening_history(spotify_user_id, limit=3)
    user_listening_history_dicts = [listening_history_to_dict(lh) for lh in user_listening_history]

    # info is first 3 activities, 3 playlists (TBD), and last 3 songs listened to
    info = {
        'activities': user_activities_dicts,
        'playlists': user_playlists_dicts,
        'history': user_listening_history_dicts
    }

    return info


@app.route('/history/')
@jwt_required()
def history():
    # TODO add limit and index params
    spotify_user_id = get_jwt_identity()
    update_user_history(spotify_user_id)
    listening_history = get_user_listening_history(spotify_user_id)
    lh_list = []
    for lh in listening_history:
        lh_list.append(listening_history_to_dict(lh))
    return {'history_items': lh_list}


@app.route('/user/')
@jwt_required()
def user():
    # starts the scheduler. It's weird to put it here, but flask is weird so getting it to run on its own won't work
    try:
        start_scheduler()
    except SchedulerAlreadyRunningError:
        pass

    spotify_user_id = get_jwt_identity()
    # st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()
    # headers = {'Authorization': f'Bearer {st.access_token}'}
    # res = requests.get(endpoints.ME_URL, headers=headers)
    # res_data = res.json()

    return make_authorized_get_request(spotify_user_id, endpoints.ME_URL)
