import time

from server import app, db
from server.models import Activity, ListeningSession, SongHistoryRecord
from datetime import datetime

response = input('Are you sure you want to delete and recreate the database? y/n ')
if response != 'y':
    print('Aborting...')
    exit()


with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database initialized.')

    # a1 = Activity(spotify_id="myId", activity_name="Working Out")
    # db.session.add(a1)
    # db.session.commit()
    #
    # s1 = ListeningSession(
    #     start_time=datetime.fromtimestamp(time.time() - 3_000),
    #     end_time=datetime.fromtimestamp(time.time()),
    #     activity_id=a1.id
    # )
    # s2 = ListeningSession(
    #     start_time=datetime.fromtimestamp(time.time() - 10_000),
    #     end_time=datetime.fromtimestamp(time.time() - 5_000),
    #     activity_id=a1.id
    # )
    #
    # db.session.add(s1)
    # db.session.add(s2)
    # db.session.commit()
