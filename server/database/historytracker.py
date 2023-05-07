from datetime import datetime

from server import db
from server.models import SongHistoryRecord, SpotifyToken, Activity, ListeningSession


def get_user_recently_played(spotify_user_id: str, after: datetime) -> list[dict]:
    # TODO return the json array of recently played tracks
    pass


def save_user_recently_played(spotify_user_id: str) -> None:
    # TODO find most recent history entry for user, call get_user_recently_played, and save results to db
    pass


def save_all_user_recently_played() -> None:
    for suid in [token.spotify_user_id for token in SpotifyToken.query.all()]:
        save_user_recently_played(suid)
