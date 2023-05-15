from datetime import datetime

from server import db
from server.models import SongHistoryRecord, Activity, ListeningSession, ActivityPlaylist


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


def get_user_listening_history(spotify_user_id: str, limit: int = None) -> list[SongHistoryRecord]:
    """
    Get the saved listening history for a user
    @param spotify_user_id: The user to get history for
    @param limit: The max number of entries to return (newest first)
    @return: The list of SongHistoryRecord objects
    """
    if limit:
        result = SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id) \
            .order_by(SongHistoryRecord.played_at.desc()).limit(limit).all()
    else:
        result = SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id) \
            .order_by(SongHistoryRecord.played_at.desc()).all()
    return result


def get_user_listening_history_after_date(spotify_user_id: str, after: datetime) -> list[SongHistoryRecord]:
    """
    Get the saved listening history for a user
    @param spotify_user_id: The user to get history for
    @param after: Only records after this date will be returned
    @return: The list of SongHistoryRecord objects
    """
    result = SongHistoryRecord.query\
        .filter(SongHistoryRecord.spotify_user_id == spotify_user_id)\
        .filter(SongHistoryRecord.played_at > after) \
        .order_by(SongHistoryRecord.played_at.desc()).all()
    return result


def listening_history_to_dict(listening_history_record: SongHistoryRecord) -> dict:
    """
    Converts a SongHistoryRecord object to a dictionary
    @param listening_history_record: The SongHistoryRecord database object
    @return: A dictionary containing a key for each attribute
    """
    played_at_milliseconds = datetime_to_epoch(listening_history_record.played_at)
    return {
        'spotify_user_id': listening_history_record.spotify_user_id,
        'song_id': listening_history_record.song_id,
        'song_name': listening_history_record.song_name,
        'artist_name': listening_history_record.artist_name,
        'art_link': listening_history_record.art_link,
        'played_at_millis': played_at_milliseconds
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


def set_listening_session_activity_by_id(listening_session_id: int, activity_id: int):
    ls = ListeningSession.query.filter_by(id=listening_session_id).first()
    a = Activity.query.filter_by(id=activity_id).first()
    set_listening_session_activity(ls, a)


def get_latest_listening_session(spotify_user_id: str) -> ListeningSession:
    """
    Get the most recent listening session
    @param spotify_user_id: The spotify user to get the listening session for
    @return: The ListeningSession object
    """
    return ListeningSession.query.filter_by(spotify_user_id=spotify_user_id) \
        .order_by(ListeningSession.end_time.desc()).first()


def get_listening_sessions_for_activity(spotify_user_id: str, activity_id: int = None) -> list[ListeningSession]:
    """
    Returns listening sessions for activity, or unlabeled listening sessions if activity_id=None
    @param spotify_user_id: The spotify user to get listening sessions for
    @param activity_id: id of activity, or None
    @return: list of ListeningSession objects
    """
    return ListeningSession.query.filter(ListeningSession.activity_id == activity_id).all()


def get_songs_for_listening_session(ls: ListeningSession) -> list[SongHistoryRecord]:
    return SongHistoryRecord.query.filter(
        (SongHistoryRecord.played_at >= ls.start_time) &
        (SongHistoryRecord.played_at <= ls.end_time) &
        (SongHistoryRecord.spotify_user_id == ls.spotify_user_id)
    ).all()


def create_activity(spotify_user_id: str, activity_name: str) -> Activity:
    a = Activity(spotify_user_id=spotify_user_id, activity_name=activity_name)
    db.session.add(a)
    db.session.commit()
    return a


def delete_activity(activity_id: int):
    a = Activity.query.filter_by(id=activity_id).first()
    db.session.delete(a)
    db.session.commit()


def create_default_activities(spotify_user_id: str) -> None:
    """
    Creates the default activities for a new user.
    @param spotify_user_id: The new user's id
    """
    default_activities = ['Driving', 'Studying', 'Working Out']
    for activity_name in default_activities:
        create_activity(spotify_user_id, activity_name)


def get_user_activities(spotify_user_id: str, limit: int = None) -> list[Activity]:
    if limit:
        result = Activity.query.filter(Activity.spotify_user_id == spotify_user_id).limit(limit).all()
    else:
        result = Activity.query.filter(Activity.spotify_user_id == spotify_user_id).all()
    return result


def datetime_to_epoch(date_time: datetime):
    """
    Converts a datetime object to milliseconds since the epoch
    @param date_time:
    @return:
    """
    return int((date_time - datetime.utcfromtimestamp(0)).total_seconds() * 1000)
