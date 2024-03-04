# routes.py
from flask import Flask,render_template, request, redirect, url_for, flash
from models import RSSFeed, FeedEntry, db
from helpers import is_valid_rss, get_feed_contents, sort_articles_by
import requests
from bs4 import BeautifulSoup


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rss_feeds.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Needed for flash messages

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
            refresh_feed()
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

# Toggle Buttons
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
