from server import app
from server.database.playlistmanager import create_playlist, add_songs_to_playlist
from server.models import Activity

with app.app_context():
    suid = 'shmexysmusic'
    activity_id = 1
    create_playlist(suid, activity_id)
    playlist_id = Activity.query.filter_by(id=activity_id).first().activity_playlist.spotify_playlist_id
    add_songs_to_playlist(suid, playlist_id, ['0D582Sb7ppcgPrnVQ6ZAyj'])
