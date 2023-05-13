import time
from datetime import datetime

from server import app, db
from server.database.datamanager import save_listening_session, set_listening_session_activity, \
    save_to_listening_history, save_activity, get_songs_for_listening_session, \
    get_activity_from_name, get_listening_sessions_for_activity

response = input('Are you sure you want to delete and test adding stuff to the database? y/n ')
if response != 'y':
    print('Aborting...')
    exit()


with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database initialized.')

    a1 = save_activity(spotify_user_id="myId", activity_name="Working Out")

    s1 = save_listening_session(
        spotify_user_id="myId",
        start_time=datetime.fromtimestamp(time.time() - 3_000),
        end_time=datetime.fromtimestamp(time.time()),
        activity_id=a1.id
    )
    s2 = save_listening_session(
        spotify_user_id="myId",
        start_time=datetime.fromtimestamp(time.time() - 10_000),
        end_time=datetime.fromtimestamp(time.time() - 5_000)
    )
    set_listening_session_activity(s2, a1)
    s3 = save_listening_session(
        spotify_user_id="myId",
        start_time=datetime.fromtimestamp(time.time() - 30_000),
        end_time=datetime.fromtimestamp(time.time() - 25_000)
    )

    save_to_listening_history(
        spotify_user_id="myId",
        song_id="123song",
        song_name="cool bops",
        artist_name="cool guy",
        art_link="image.com/link",
        played_at=datetime.fromtimestamp(time.time() - 2_000)
    )

    print(get_songs_for_listening_session(s1))
    print(get_songs_for_listening_session(s2))
    print(get_activity_from_name("myId", "Working Out"))
    print(get_listening_sessions_for_activity("myId"))




