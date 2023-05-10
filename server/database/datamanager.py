from datetime import datetime

from server import db
from server.database.historytracker import save_user_recently_played
from server.models import SongHistoryRecord, Activity, ListeningSession


def save_to_listening_history(spotify_user_id: str, song_id: str, song_name: str, artist_name: str, art_link: str,
                              played_at: datetime) -> None:
    lh = SongHistoryRecord(
        spotify_user_id=spotify_user_id,
        song_id=song_id,
        song_name=song_name,
        artist_name=artist_name,
        art_link=art_link,
        played_at=played_at
    )
    db.session.add(lh)
    db.session.commit()


def get_user_listening_history(spotify_user_id: str, limit: int = None, update: bool = True) -> list[SongHistoryRecord]:
    """
    Get the saved listening history for a user
    @param spotify_user_id: The user to get history for
    @param limit: The max number of entries to return (newest first)
    @param update: If true, fetches the most recent data from Spotify before returning
    @return: The list of SongHistoryRecord objects
    """
    if update:
        save_user_recently_played(spotify_user_id)

    if limit:
        result = SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id) \
            .order_by(SongHistoryRecord.played_at.desc()).limit(limit).all()
    else:
        result = SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id)\
            .order_by(SongHistoryRecord.played_at.desc()).all()
    return result


def listening_history_to_dict(listening_history_record: SongHistoryRecord) -> dict:
    """
    Converts a SongHistoryRecord object to a dictionary
    @param listening_history_record: The SongHistoryRecord database object
    @return: A dictionary containing a key for each attribute
    """
    return {
        'spotify_user_id': listening_history_record.spotify_user_id,
        'song_id': listening_history_record.song_id,
        'song_name': listening_history_record.song_name,
        'artist_name': listening_history_record.artist_name,
        'art_link': listening_history_record.art_link,
        'played_at': listening_history_record.played_at
        }


def save_listening_session(
    spotify_user_id: str,
    start_time: datetime,
    end_time: datetime,
    activity_id: int = None
) -> ListeningSession:
    ls = ListeningSession(
        spotify_user_id=spotify_user_id,
        start_time=start_time,
        end_time=end_time,
        activity_id=activity_id
    )
    db.session.add(ls)
    db.session.commit()
    return ls


def set_listening_session_activity(listening_session: ListeningSession, activity: Activity) -> None:
    listening_session.activity_id = activity.id
    db.session.commit()


def get_unlabeled_listening_sessions(spotify_user_id: str) -> list[ListeningSession]:
    return ListeningSession.query.filter(ListeningSession.activity_id == None).all()


def get_songs_for_listening_session(ls: ListeningSession) -> list[SongHistoryRecord]:
    return SongHistoryRecord.query.filter(
        (SongHistoryRecord.played_at >= ls.start_time) &
        (SongHistoryRecord.played_at <= ls.end_time) &
        (SongHistoryRecord.spotify_user_id == ls.spotify_user_id)
    ).all()


def save_activity(spotify_user_id: str, activity_name: str) -> Activity:
    a = Activity(spotify_user_id=spotify_user_id, activity_name=activity_name)
    db.session.add(a)
    db.session.commit()
    return a


def get_user_activities(spotify_user_id: str, limit: int = None) -> list[Activity]:
    if limit:
        result = Activity.query.filter(Activity.spotify_user_id == spotify_user_id).limit(limit).all()
    else:
        result = Activity.query.filter(Activity.spotify_user_id == spotify_user_id).all()
    return result


def get_activity_from_name(spotify_user_id: str, activity_name: str) -> Activity:
    return Activity.query.filter(
        (Activity.spotify_user_id == spotify_user_id) &
        (Activity.activity_name == activity_name)
    ).first()
