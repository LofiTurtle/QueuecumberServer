from datetime import datetime

from server.database.datamanager import get_user_listening_history, save_listening_session,\
    get_latest_listening_session, get_user_listening_history_after_date


def create_listening_sessions(spotify_user_id: str) -> None:
    """
    Goes through the user's listening history, creating new unlabeled listening sessions
    @param spotify_user_id: The id of the user to create listening sessions for
    """
    latest_listening_session = get_latest_listening_session(spotify_user_id)
    if latest_listening_session is None:
        history = get_user_listening_history(spotify_user_id)
    else:
        history = get_user_listening_history_after_date(spotify_user_id, latest_listening_session.end_time)
    history.reverse()

    if len(history) == 0:
        return

    min_songs = 3
    start_time: datetime = history[0].played_at
    start_index = 0
    previous_played_at: datetime = history[0].played_at

    for i in range(len(history)):
        current_played_at: datetime = history[i].played_at
        time_difference = current_played_at - previous_played_at

        if time_difference.total_seconds() >= 1800:
            if i - start_index >= min_songs:
                # only create a listening session if there are more than min_songs songs
                save_listening_session(spotify_user_id, start_time, previous_played_at)
            start_time = current_played_at
            start_index = i

        if i == len(history) - 1:
            if (datetime.now() - current_played_at).total_seconds() >= 1800 and i - start_index >= min_songs:
                save_listening_session(spotify_user_id, start_time, current_played_at)

        previous_played_at = current_played_at
