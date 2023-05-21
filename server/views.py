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
from .database.datamanager import get_user_listening_history, get_user_activities, listening_history_to_dict, \
    get_listening_sessions_for_activity, set_listening_session_activity_by_id, \
    create_activity, get_songs_for_listening_session, datetime_to_epoch, create_default_activities, delete_activity
from .database.historytracker import update_user_history
from .database.playlistmanager import create_playlist, add_songs_from_listening_session_to_playlist
from .models import SpotifyToken, ListeningSession, Activity
from .utils.backgroundtasks import start_scheduler
from .utils.spotifyapiutil import make_authorized_request

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


@app.route('/callback/', methods=['POST'])
def callback():
    """
    This endpoint is the callback for the Spotify web API OAuth flow. It handles retrieving the authorization code from
    the url, using the code to get the Spotify access and refresh tokens, and creating tokens for the client.
    """
    # Headers for the request to get Spotify tokens
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

    # saving the access tokens, along with their spotify user id
    spotify_access_token = res_data.get('access_token')
    spotify_refresh_token = res_data.get('refresh_token')
    headers = {'Authorization': f'Bearer {spotify_access_token}'}
    me_res = requests.get(endpoints.ME_URL, headers=headers)
    me_res_data = me_res.json()
    spotify_user_id = me_res_data.get('id')

    existing_st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()
    if existing_st:
        # Old tokens already exist, so the user has logged in before. Update token
        existing_st.access_token = spotify_access_token
        existing_st.refresh_token = spotify_refresh_token
    else:
        # first time user. Create new token and create their default activities
        st = SpotifyToken(
            spotify_user_id=spotify_user_id,
            access_token=spotify_access_token,
            refresh_token=spotify_refresh_token
        )
        db.session.add(st)
        create_default_activities(spotify_user_id)

    db.session.commit()

    # Create and return access and refresh tokens for the client to use to authenticate future requests
    client_access_token = create_access_token(identity=spotify_user_id)
    client_refresh_token = create_refresh_token(identity=spotify_user_id)

    return jsonify(clientAccessToken=client_access_token, clientRefreshToken=client_refresh_token)


@app.route('/sessions/')
@jwt_required()
def unlabeled_sessions():
    """
    Returns all the listening sessions not yet labeled with an activity
    """
    spotify_user_id = get_jwt_identity()
    listening_sessions = get_listening_sessions_for_activity(spotify_user_id, None)
    return {'sessions': [{
        'id': s.id,
        'start_time_millis': datetime_to_epoch(s.start_time),
        'end_time_millis': datetime_to_epoch(s.end_time)
    } for s in listening_sessions]}


@app.route('/sessions/<activity_id>/')
@jwt_required()
def sessions(activity_id):
    """
    Returns all the listening sessions associated with this activity.
    The activity is specified by 'activity_id'
    """
    spotify_user_id = get_jwt_identity()
    activity_id = int(activity_id)
    listening_sessions = get_listening_sessions_for_activity(spotify_user_id, activity_id)
    return {'sessions': [{
        'id': s.id,
        'start_time_millis': datetime_to_epoch(s.start_time),
        'end_time_millis': datetime_to_epoch(s.end_time)
    } for s in listening_sessions]}


@app.route('/set_session_activity/', methods=['POST'])
@jwt_required()
def set_session_activity():
    """
    Labels a listening session with an activity, specified by the following url query parameters:
    'session_id': id of the session to modify
    'activity_id': id of the activity to label this session with
    """
    spotify_user_id = get_jwt_identity()
    session_id = int(request.args.get('session_id'))
    activity_id = int(request.args.get('activity_id'))
    set_listening_session_activity_by_id(int(session_id), int(request.args.get('activity_id')))
    add_songs_from_listening_session_to_playlist(spotify_user_id, int(session_id), activity_id)
    return {'result': 'success'}


@app.route('/session_songs/')
@jwt_required()
def get_listening_session_songs():
    """
    Return the list of all songs from the session, specified by the 'session_id' url query parameter
    """
    # returns the songs in a session, takes ?session_id=id query param
    session_id = request.args.get('session_id')
    spotify_user_id = get_jwt_identity()
    if spotify_user_id != ListeningSession.query.filter_by(id=session_id).first().spotify_user_id:
        # if the user is trying to access another user's session, abort the request
        abort(401)
    listening_session = ListeningSession.query.filter_by(id=session_id).first()
    songs = get_songs_for_listening_session(listening_session)
    return {'songs': [listening_history_to_dict(song) for song in songs]}


@app.route('/activity/create/', methods=['POST'])
@jwt_required()
def create_activity_endpoint():
    """
    Create a new activity. Activity name is the 'activity_name' query parameter.
    """
    spotify_user_id = get_jwt_identity()
    activity_name = request.args.get('activity_name')
    create_activity(spotify_user_id, activity_name)
    return {'result': 'success'}


@app.route('/activity/delete/', methods=['POST'])
@jwt_required()
def delete_activity_endpoint():
    """
    Delete an activity. The id of the Activity to delete is in the 'activity_id' query parameter
    """
    spotify_user_id = get_jwt_identity()
    activity_id = int(request.args.get('activity_id'))
    if spotify_user_id != Activity.query.filter_by(id=activity_id).first().spotify_user_id:
        # if the user is trying to delete another user's activity, abort the request
        abort(401)
    delete_activity(activity_id)
    return {'result': 'success'}


@app.route('/activities/')
@jwt_required()
def activities():
    """
    Returns a list of all activities
    """
    spotify_user_id = get_jwt_identity()
    activities_list = [{
        'id': activity.id,
        'name': activity.activity_name
    } for activity in get_user_activities(spotify_user_id)]

    if len(activities_list) == 0:
        activities_list = [{
            'id': -1,
            'name': 'Test Activity'
        }]
    return {'activities': activities_list}


@app.route('/create_playlist/<activity_id>/', methods=['POST'])
@jwt_required()
def create_playlist_endpoint(activity_id):
    """
    Creates a playlist for the associated activity_id
    @param activity_id: The id of the activity to make a playlist for
    """
    # create a playlist for an activity
    spotify_user_id = get_jwt_identity()
    create_playlist(spotify_user_id, activity_id)
    return {'result': 'success'}


@app.route('/playlists/')
@jwt_required()
def playlists():
    """
    Returns the playlist information associated with each activity
    """
    spotify_user_id = get_jwt_identity()
    # We aren't storing the playlist name. Activity name will be used for display, and an empty playlist id implies no
    # playlist exists yet
    playlist_list = [{
        'playlist_id': user_activity.activity_playlist.id if user_activity.activity_playlist is not None else -1,
        'playlist_url': user_activity.activity_playlist.playlist_url if user_activity.activity_playlist is not None else "",
        'activity_name': user_activity.activity_name,
        'activity_id': user_activity.id
    } for user_activity in get_user_activities(spotify_user_id)]
    return {'playlists': playlist_list}


@app.route('/homepage_info/')
@jwt_required()
def homepage_info():
    """
    Returns the information shown in the previews on the homepage
    """
    spotify_user_id = get_jwt_identity()

    user_activities = get_user_activities(spotify_user_id, limit=3)
    user_activities_dicts = [{
        'name': activity.activity_name
    } for activity in user_activities]

    # add activity.name for each activity that has a corresponding playlist
    all_user_activities = get_user_activities(spotify_user_id)
    user_playlists_dicts = [activity.activity_name for activity in all_user_activities if activity.activity_playlist is not None]
    # limit to the first 3 elements
    user_playlists_dicts = user_playlists_dicts[:3]

    update_user_history(spotify_user_id)
    user_listening_history = get_user_listening_history(spotify_user_id, limit=3)
    user_listening_history_dicts = [listening_history_to_dict(lh) for lh in user_listening_history]

    # info is first 3 activities, 3 playlists, and last 3 songs listened to
    info = {
        'activities': user_activities_dicts,
        'playlists': user_playlists_dicts,
        'history': user_listening_history_dicts
    }

    return info


@app.route('/history/')
@jwt_required()
def history():
    """
    Return the list of all songs for this user
    """
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
    """
    Returns info about the current user's Spotify profile
    """
    # start the scheduler to handle collecting listening history in the background
    try:
        start_scheduler()
    except SchedulerAlreadyRunningError:
        pass

    spotify_user_id = get_jwt_identity()

    return make_authorized_request(spotify_user_id, endpoints.ME_URL)
