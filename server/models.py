from server import db


class SpotifyToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, unique=True, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)


class Activity(db.Model):
    # this might have issues with duplicate activity names if we don't handle id in the client.
    # maybe a unique constraint for the combination of user ID and activity name?
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, unique=True, nullable=False)
    activity_name = db.Column(db.String, nullable=False)
    listening_sessions = db.relationship('ListeningSession', lazy=True)
    activity_playlist = db.relationship('ActivityPlaylist', lazy=True)


class ListeningSession(db.Model):
    # each row is a single listening session for a user
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)


class SongHistoryRecord(db.Model):
    # each row is a single song in the user's listening history
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    song_id = db.Column(db.String, nullable=False)
    song_name = db.Column(db.String, nullable=False)
    artist_name = db.Column(db.String, nullable=False)
    art_link = db.Column(db.String)
    played_at = db.Column(db.DateTime, unique=True)


class ActivityPlaylist(db.Model):
    # each row represents a playlist in the user's spotify account
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    spotify_playlist_id = db.Column(db.String, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False, unique=True)
