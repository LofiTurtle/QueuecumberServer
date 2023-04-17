import datetime

from server import db


# test code from documentation
class Parent(db.Model):
    __tablename__ = "parent_table"

    id: db.Mapped[int] = db.mapped_column(primary_key=True)
    child: db.Mapped["Child"] = db.relationship(back_populates="parent")


class Child(db.Model):
    __tablename__ = "child_table"

    id: db.Mapped[int] = db.mapped_column(primary_key=True)
    parent_id: db.Mapped[int] = db.mapped_column(db.ForeignKey("parent_table.id"))
    parent: db.Mapped["Parent"] = db.relationship(back_populates="child")


# class User(db.Model):
#     id: db.Mapped[int] = db.Column(db.Integer, primary_key=True)
#     spotify_id: db.Mapped[str] = db.Column(db.String(128), unique=True, nullable=False)
#     spotify_token: db.Mapped['SpotifyToken'] = db.relationship(back_populates='user')
#
#
# class SpotifyToken(db.Model):
#     id: db.Mapped[int] = db.Column(db.Integer, primary_key=True)
#     user_id: db.Mapped[int] = db.mapped_column(db.ForeignKey('User.id'))
#     user: db.Mapped['User'] = db.relationship(back_populates='spotify_token')
#     access_token = db.Column(db.String(300), nullable=False)
#     refresh_token = db.Column(db.String(300), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#     expires_in = db.Column(db.Integer)
