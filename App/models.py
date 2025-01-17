# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

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
    # Article Details
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False, default=datetime.now(timezone.utc))
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    raw_description = db.Column(db.Text)
    full_content = db.Column(db.Text)
    summarized_content = db.Column(db.Text)
    img = db.Column(db.String(200))
    link = db.Column(db.String(200), nullable=False)

    #IDs
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    account_id = db.Column(db.Integer)
    
    # flags
    is_unread = db.Column(db.Boolean, default=True)
    is_starred = db.Column(db.Boolean, default=False)
    is_read_later = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<FeedEntry {self.title}>'

class Translation(db.Model):
    # Use 'link' as the primary key and foreign key
    link = db.Column(db.String(200), db.ForeignKey('feed_entry.link'), primary_key=True)
    language = db.Column(db.String(10), primary_key=True)  # Composite primary key with 'language'

    # Translation fields
    title = db.Column(db.String(200), nullable=True)
    full_content = db.Column(db.Text, nullable=True)
    summarized_content = db.Column(db.Text, nullable=True)
    
    # Relationship for easier access
    feed_entry = db.relationship('FeedEntry', backref=db.backref('translations', lazy=True))

    def __repr__(self):
        return f'<Translation {self.language} for FeedEntry {self.link}>'

def init_db(app):
    db.init_app(app)