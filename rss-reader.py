from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import feedparser
import requests
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rss_feeds.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Needed for flash messages
db = SQLAlchemy(app)

class RSSFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False)
    website_name = db.Column(db.String(200))  # New field for website name
    icon = db.Column(db.String(200))  # New field for icon URL
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
    img = db.Column(db.String(200))
    link = db.Column(db.String(200), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    account_id = db.Column(db.Integer)  # Assuming you have some sort of account system
    is_unread = db.Column(db.Boolean, default=True)
    is_starred = db.Column(db.Boolean, default=False)
    is_read_later = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<FeedEntry {self.title}>'

def is_valid_rss(url):
    try:
        feed = feedparser.parse(url)
        return bool(feed.entries)
    except Exception as e:
        return False

def get_feed_contents(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        existing_entry = FeedEntry.query.filter_by(link=entry.link).first()
        if not existing_entry:
            new_entry = FeedEntry(
                title=entry.title,
                author=entry.author,
                raw_description=entry.description,
                short_description=entry.summary,
                full_content=entry.content[0].value if hasattr(entry, 'content') else '',
                img=entry.enclosures[0].href if hasattr(entry, 'enclosures') and entry.enclosures else '',
                link=entry.link,
                feed_id=RSSFeed.query.filter_by(url=url).first().id
            )
            entries.append(new_entry)
    return entries

def sort_articles_by(sort_by):
    feeds = RSSFeed.query.all()
    feed_contents = {}
    
    if not feeds:  # If there are no feeds, return empty lists
        return [], {}

    for feed in feeds:
        if sort_by == 'link':
            sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.link).all()
        elif sort_by == 'title':
            sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.title).all()
        else:
            sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.date.desc()).all()
        
        feed_contents[feed.id] = sorted_entries

    return feeds, feed_contents

@app.route('/')
def index():
    sort_by = request.args.get('sort_by', default='datetime')
    feeds, feed_contents = sort_articles_by(sort_by)

    return render_template('rss.html', feeds=feeds, feed_contents=feed_contents)

@app.route('/add', methods=['POST'])
def add_feed():
    url = request.form['url']
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            website_name = soup.title.string.strip() if soup.title else 'Unknown Website'
            icon_tag = soup.find("icon")
            icon_url = icon_tag.text if icon_tag else "https://cdn-icons-png.flaticon.com/512/4076/4076373.png"
            new_feed = RSSFeed(url=url, website_name=website_name, icon=icon_url)
            db.session.add(new_feed)
            db.session.commit()
            flash('RSS feed added successfully!', 'success')
        else:
            flash('Failed to fetch RSS feed data!', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete_feed(id):
    feed_to_delete = RSSFeed.query.get_or_404(id)
    
    # Delete associated feed entries
    feed_entries_to_delete = FeedEntry.query.filter_by(feed_id=id).all()
    for entry in feed_entries_to_delete:
        db.session.delete(entry)
    
    db.session.delete(feed_to_delete)
    db.session.commit()
    flash('RSS feed deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/refresh')
def refresh_feed():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        entries = get_feed_contents(feed.url)
        db.session.add_all(entries)
    db.session.commit()
    flash('Articles refreshed successfully!', 'success')
    return redirect(url_for('index'))

# app.py (continuation)

@app.route('/toggle_unread/<int:id>', methods=['POST'])
def toggle_unread(id):
    entry = FeedEntry.query.get_or_404(id)
    entry.is_unread = not entry.is_unread  # Toggle the state
    db.session.commit()
    flash('Article marked as unread!' if entry.is_unread else 'Article marked as read!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle_starred/<int:id>', methods=['POST'])
def toggle_starred(id):
    entry = FeedEntry.query.get_or_404(id)
    entry.is_starred = not entry.is_starred  # Toggle the state
    db.session.commit()
    flash('Article starred!' if entry.is_starred else 'Article unstarred!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle_read_later/<int:id>', methods=['POST'])
def toggle_read_later(id):
    entry = FeedEntry.query.get_or_404(id)
    entry.is_read_later = not entry.is_read_later  # Toggle the state
    db.session.commit()
    flash('Article marked to read later!' if entry.is_read_later else 'Article removed from read later!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
