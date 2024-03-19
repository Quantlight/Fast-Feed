# routes.py
from flask import Flask,render_template, request, redirect, url_for, flash
from models import RSSFeed, FeedEntry, db
from helpers import is_valid_rss, get_feed_contents, sort_articles_by, extract_video_id, extract_text_from_wikipedia, summarize_content, get_domain, get_favicon
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from summarizer import ai_summarizer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rss_feeds.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Needed for flash messages

@app.route('/')
def index():
    sort_by = request.args.get('sort_by', default='datetime')
    sort_order = request.args.get('sort_order', default='desc')  # Default to descending order
    feeds, feed_contents = sort_articles_by(sort_by, sort_order)

    return render_template('rss.html', feeds=feeds, feed_contents=feed_contents)

@app.route('/<page_name>')
def load_page(page_name):
    return render_template(page_name)

@app.route('/add', methods=['POST'])
def add_feed():
    url = request.form['url']
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            website_name = soup.title.string.strip() if soup.title else 'Unknown Website'
            icon_tag = soup.find("icon")
            icon_url = icon_tag.text if icon_tag else get_favicon(url)
            new_feed = RSSFeed(url=url, website_name=website_name, icon=icon_url)
            db.session.add(new_feed)
            db.session.commit()
            refresh_feed()
            flash('RSS feed added successfully!', 'success')
        else:
            error_status = response.status_code
            flash(f'Failed to fetch RSS feed data! error status code {error_status}', 'error')
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

@app.route('/summarize')
def summarize():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        entries = summarize_content(feed.url)
        db.session.add_all(entries)
        db.session.commit()
    flash('Articles Summarized successfully!', 'success')
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

# Youtube summarize
@app.route('/youtube', methods=['GET', 'POST'])
def youtube():
    if request.method == 'POST':
        video_link = request.form.get('video_link')
        video_id = extract_video_id(video_link)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ''
            for item in transcript_list:
                transcript += f"{item['text']} "

            summarized_transcript = ai_summarizer(transcript)
            return render_template('youtube.html', transcript=transcript, summary=summarized_transcript)

        except Exception as e:
            print(f"An error occurred: {e}")
            error_message = "Error processing the video. Please enter a valid YouTube video link."
            return render_template('youtube.html', error_message=error_message)

    return render_template('youtube.html')

@app.route('/youtube/<videolinkid>')
def get_youtube_summary(videolinkid):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(videolinkid)
        transcript = ''
        for item in transcript_list:
            transcript += f"{item['text']} "

        summarized_transcript = ai_summarizer(transcript)
        return render_template('youtube.html', transcript=transcript, summary=summarized_transcript)

    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "Error processing the video. Please enter a valid YouTube video link."
        return render_template('youtube.html', error_message=error_message)

@app.route('/wikipedia', methods=['GET', 'POST'])
def wikipedia_content():
    if request.method == 'POST':
        wiki_link = request.form['wiki_link']
        try:
            content = extract_text_from_wikipedia(wiki_link)

            summary = ai_summarizer(content)
            return render_template('wikipedia.html', content=content, summary=summary)

        except:
            print("Error Collecting info about wikipedia articles")
    return render_template('wikipedia.html')