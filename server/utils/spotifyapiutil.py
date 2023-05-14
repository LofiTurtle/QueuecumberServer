import requests

from server import endpoints, app, db
from server.models import SpotifyToken


def refresh_tokens(spotify_user_id: str) -> bool:
    """
    Refreshes the access_token for a user.

    @param spotify_user_id: The user to refresh the token for
    @return: `True` if the token was successfully refreshed, `False` otherwise
    """
    # get refresh token
    st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()

    # construct and make request
    headers = {
        'grant_type': 'refresh_token',
        'refresh_token': st.refresh_token
    }
    res = requests.post(
        endpoints.TOKEN_URL,
        auth=(app.config.get('CLIENT_ID'), app.config.get('CLIENT_SECRET')),
        data=headers
    )
    res_data = res.json()

    # error checking
    if res.status_code != 200:
        app.logger.error(
            'Failed to refresh tokens: %s',
            res_data.get('error', 'No error information provided.')
        )
        return False

    # save new access token to db
    st.access_token = res_data.get('access_token')
    db.session.commit()
    return True


def get_authorization_header(spotify_user_id: str):
    st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()
    return {'Authorization': f'Bearer {st.access_token if st.access_token is not None else None}'}


def make_authorized_request(spotify_user_id: str, url: str, request_type: str = 'GET', body: dict = None) -> dict:
    """
    Make a GET request to Spotify using valid credentials.

    @param spotify_user_id: user to make request for
    @param url: url to make the request to (including params)
    @param request_type: Type of request to make. Valid types are
    @param body: Body of request. Only used if `request_type` supports a message body
    @return: HTTP response as dict
    """
    if request_type == 'GET':
        request_method = requests.get
    elif request_type == 'POST':
        request_method = requests.post
    else:
        raise ValueError('')
    res = request_method(url, headers=get_authorization_header(spotify_user_id), json=body)
    if res.status_code == 401:
        # "401 Unauthorized" likely means expired token, so try to get a new one
        if not refresh_tokens(spotify_user_id):
            # Refreshing token didn't work
            app.logger.error(f'Couldn\'t refresh token for user: {spotify_user_id}')
            raise RuntimeError(f'Couldn\'t refresh token for user: {spotify_user_id}')
        # retry the request
        res = request_method(url, headers=get_authorization_header(spotify_user_id), json=body)
    elif res.status_code >= 400:
        # some other error occurred
        app.logger.error(f'Error making request to: {url} for {spotify_user_id}.\n' +
                         f'Status code {res.status_code}. Message: {res.json()["error"]["message"]}')
        raise RuntimeError(f'Error making request to: {url} for {spotify_user_id}')
    return res.json()
