from datetime import datetime

from server import db
from server.models import SongHistoryRecord, SpotifyToken, Activity, ListeningSession


def get_token_header(spotify_user_id: str) -> dict[str, str]:
    st = SpotifyToken.query.filter_by(spotify_user_id=spotify_user_id).first()
    return {'Authorization': f'Bearer {st.access_token}'}


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


def get_user_listening_history(spotify_user_id: str) -> list[SongHistoryRecord]:
    return SongHistoryRecord.query.filter(SongHistoryRecord.spotify_user_id == spotify_user_id).all()


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


def get_user_activities(spotify_user_id: str) -> list[Activity]:
    return Activity.query.filter(Activity.spotify_user_id == spotify_user_id).all()


def get_activity_from_name(spotify_user_id: str, activity_name: str) -> Activity:
    return Activity.query.filter(
        (Activity.spotify_user_id == spotify_user_id) &
        (Activity.activity_name == activity_name)
    ).first()
