from datetime import datetime

from server.database.datamanager import get_user_listening_history, save_listening_session, get_latest_listening_session


def create_listening_sessions(spotify_user_id: str) -> None:
    latest_listening_session = get_latest_listening_session(spotify_user_id)
    history = get_user_listening_history(spotify_user_id)
    start_time = -1
    previous_played_at = history[0].played_at
    current_played_at = history[0].played_at
    break_flag = False

    for i in range(len(history)):
        if start_time == -1:
            start_time = history[i].played_at

            while latest_listening_session.end_time >= start_time and break_flag is False:
                i += 1

                if i <= len(history) - 1:
                    start_time = history[i].played_at
                    previous_played_at = history[i].played_at
                else:
                    print("Listening sessions were up-to-date.")
                    break_flag = True

        if break_flag is False:
            current_played_at = history[i].played_at
            time_difference = current_played_at - previous_played_at

            if time_difference.total_seconds() >= 1800 and i < len(history) - 1:
                save_listening_session(spotify_user_id, start_time, previous_played_at)
                start_time = current_played_at

            if i == len(history) - 1:
                if time_difference.total_seconds() >= 1800:
                    save_listening_session(spotify_user_id, start_time, previous_played_at)
                print("done")

            previous_played_at = current_played_at
