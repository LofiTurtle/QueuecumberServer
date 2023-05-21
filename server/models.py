from server import db


class SpotifyToken(db.Model):
    """
    Database table to store the spotify access and refresh tokens for users
    """
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, unique=True, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)


class Activity(db.Model):
    """
    Table to store activities for users
    """
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    activity_name = db.Column(db.String, nullable=False, unique=True)
    listening_sessions = db.relationship('ListeningSession', lazy=True)
    activity_playlist = db.relationship('ActivityPlaylist', uselist=False, lazy=True)


class ListeningSession(db.Model):
    """
    Table to store listening sessions for users
    """
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=True)


class SongHistoryRecord(db.Model):
    """
    Table to store the songs users listen to
    """
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    song_id = db.Column(db.String, nullable=False)
    song_name = db.Column(db.String, nullable=False)
    artist_name = db.Column(db.String, nullable=False)
    art_link = db.Column(db.String)
    played_at = db.Column(db.DateTime, unique=True)


class ActivityPlaylist(db.Model):
    """
    Table to store the information about playlists associated with activities
    """
    id = db.Column(db.Integer, primary_key=True)
    spotify_user_id = db.Column(db.String, nullable=False)
    spotify_playlist_id = db.Column(db.String, nullable=False)
    playlist_url = db.Column(db.String, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), unique=True)
