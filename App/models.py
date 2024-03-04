# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class RSSFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False)
    website_name = db.Column(db.String(200))
    icon = db.Column(db.String(200))
    feed_entries = db.relationship('FeedEntry', backref='feed', lazy=True)

    def __repr__(self):
        return f'<RSSFeed {self.url}>'

class FeedEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    raw_description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    full_content = db.Column(db.Text)
    summarized_content = db.Column(db.Text)
    img = db.Column(db.String(200))
    link = db.Column(db.String(200), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    account_id = db.Column(db.Integer)
    is_unread = db.Column(db.Boolean, default=True)
    is_starred = db.Column(db.Boolean, default=False)
    is_read_later = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<FeedEntry {self.title}>'

def init_db(app):
    db.init_app(app)