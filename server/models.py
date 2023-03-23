from server import db

# TODO idk if any of this is correct
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)