from datetime import datetime

from server.database.datamanager import get_user_listening_history, save_listening_session


def create_listening_sessions(spotify_user_id: str) -> None:
    history = get_user_listening_history(spotify_user_id)
    start_time = -1
    previous_played_at = history[0].played_at
    current_played_at = history[0].played_at

    for i in range(len(history)):
        if start_time == -1:
            start_time = history[i].played_at

        current_played_at = history[i].played_at
        time_difference = current_played_at - previous_played_at

        if time_difference.total_seconds() >= 1800:
            save_listening_session(spotify_user_id, start_time, previous_played_at)
            start_time = current_played_at

        if i == (len(history)) - 1:
            save_listening_session(spotify_user_id, start_time, previous_played_at)
            start_time = -1
            #print("done")

        previous_played_at = current_played_at
