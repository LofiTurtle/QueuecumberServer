from datetime import datetime

from server import endpoints, db
from server.database.datamanager import get_songs_for_listening_session
from server.models import Activity, ActivityPlaylist, ListeningSession
from server.utils.spotifyapiutil import make_authorized_request


def create_playlist(spotify_user_id: str, activity_id: int):
    """
    Create playlist in a user's spotify account, save it to the db, and add songs from all existing listening sessions.
    :param spotify_user_id: User to make a playlist for
    :param activity_id: The id of the Activity to associate this playlist with
    """
    playlist_activity: Activity = Activity.query.filter_by(id=activity_id).first()
    if playlist_activity.activity_playlist is not None:
        # a playlist already exists for this activity, don't create another
        return
    url = endpoints.PLAYLIST_CREATE_URL.format(user_id=spotify_user_id)
    payload = {'name': f'{playlist_activity.activity_name} Music', 'description': get_playlist_description()}
    playlist_details = make_authorized_request(spotify_user_id, url, 'POST', payload)
    playlist_id = playlist_details['id']

    save_playlist(
        spotify_user_id=spotify_user_id,
        spotify_playlist_id=playlist_id,
        activity_id=playlist_activity.id,
    )

    for ls in playlist_activity.listening_sessions:
        ls_songs = get_songs_for_listening_session(ls)
        add_songs_to_playlist(spotify_user_id, activity_id, [song.song_id for song in ls_songs])


def add_songs_to_playlist(spotify_user_id: str, activity_id: int, songs: list[str]) -> None:
    """
    Adds a list of songs to a playlist
    @param spotify_user_id: The owner of the playlist
    @param activity_id: id of the Activity whose playlist should be modified
    @param songs: ids of songs to add
    """
    spotify_playlist_id = Activity.query.filter_by(id=activity_id).first().activity_playlist.spotify_playlist_id
    add_tracks_url = endpoints.PLAYLIST_ADD_TRACKS_URL.format(playlist_id=spotify_playlist_id)
    song_uris = [f'spotify:track:{song}' for song in songs]
    for i in range(0, len(song_uris), 100):
        payload = {'uris': song_uris[i:i + 100]}
        make_authorized_request(spotify_user_id, add_tracks_url, 'POST', payload)

    playlist_modify_url = endpoints.PLAYLIST_MODIFY_URL.format(playlist_id=spotify_playlist_id)
    payload = {'description': get_playlist_description()}
    make_authorized_request(spotify_user_id, playlist_modify_url, 'POST', payload)


def add_songs_from_listening_session_to_playlist(spotify_user_id: str, listening_session_id: int,
                                                 activity_id: int) -> None:
    spotify_playlist_id = Activity.query.filter_by(id=activity_id).first().activity_playlist.spotify_playlist_id
    listening_session = ListeningSession.query.filter_by(id=listening_session_id).first()
    ls_songs = get_songs_for_listening_session(listening_session)
    add_songs_to_playlist(spotify_user_id, spotify_playlist_id, [song.song_id for song in ls_songs])


def get_playlist_description() -> str:
    d = datetime.now()
    return f'Playlist created by the Queuecumber app. Last updated on {d.month}/{d.day}/{d.year} at {d.hour}:{d.minute:02} {d:%p}'


def save_playlist(spotify_user_id: str, spotify_playlist_id, activity_id):
    ap = ActivityPlaylist(
        spotify_user_id=spotify_user_id,
        spotify_playlist_id=spotify_playlist_id,
        activity_id=activity_id
    )
    db.session.add(ap)
    db.session.commit()
