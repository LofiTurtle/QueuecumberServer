import datetime

from server import db


# test code from documentation
# class Parent(db.Model):
#     __tablename__ = "parent_table"
#
#     id: db.Mapped[int] = db.mapped_column(primary_key=True)
#     child: db.Mapped["Child"] = db.relationship(back_populates="parent")
#
#
# class Child(db.Model):
#     __tablename__ = "child_table"
#
#     id: db.Mapped[int] = db.mapped_column(primary_key=True)
#     parent_id: db.Mapped[int] = db.mapped_column(db.ForeignKey("parent_table.id"))
#     parent: db.Mapped["Parent"] = db.relationship(back_populates="child")


# TODO refactor this and add other tables
class SpotifyToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String, unique=True, nullable=False)
    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=False)
