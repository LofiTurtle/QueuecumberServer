from datetime import datetime, timezone
from urllib.parse import urlencode

from server import endpoints, db, app
from server.models import SpotifyToken, SongHistoryRecord
from server.utils.spotifyapiutil import make_authorized_get_request


# TODO make a dict to keep track of when history was last updated for users, and don't update again if it's too soon


def get_user_recently_played(spotify_user_id: str) -> list[dict]:
    url = endpoints.HISTORY_URL
    # get the played_at time for the most recent history record
    latest_history_record = \
        SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id) \
        .order_by(SongHistoryRecord.played_at.desc()).limit(1).first()

    # add "after" parameter if there is already listening history for this user
    url_params = {'limit': 50}

    if latest_history_record:
        latest_history_entry_time: datetime = latest_history_record.played_at.replace(tzinfo=timezone.utc)
        url_params['after'] = int(latest_history_entry_time.timestamp() * 1e3)

    url = url + f'/?{urlencode(url_params)}'

    res = make_authorized_get_request(spotify_user_id, url)
    # return the array
    return res.get('items')


def save_user_recently_played(spotify_user_id: str) -> None:
    app.logger.info('Fetching listening history for ' + spotify_user_id)
    song_history = get_user_recently_played(spotify_user_id)
    for song in song_history:
        try:
            played_at_date = datetime.strptime(song['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            played_at_date = datetime.strptime(song['played_at'], '%Y-%m-%dT%H:%M:%SZ')
        db.session.add(SongHistoryRecord(
            spotify_user_id=spotify_user_id,
            song_id=song['track']['id'],
            song_name=song['track']['name'],
            artist_name=song['track']['artists'][0]['name'],
            art_link=song['track']['album']['images'][0]['url'],
            played_at=played_at_date
        ))
    db.session.commit()


def update_user_history(spotify_user_id: str):
    save_user_recently_played(spotify_user_id)
    # TODO test this
    # create_listening_sessions(spotify_user_id)


def save_all_user_recently_played() -> None:
    with app.app_context():
        app.logger.info('Fetching listening history')
        for suid in [token.spotify_user_id for token in SpotifyToken.query.all()]:
            update_user_history(suid)
