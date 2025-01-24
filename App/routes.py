# routes.py
import os
from flask import Blueprint,render_template, request, redirect, url_for, flash, session, jsonify
from models import RSSFeed, FeedEntry, Translation, db
from helpers import is_valid_rss, get_feed_contents, sort_articles_by, extract_video_id, extract_text_from_wikipedia, summarize_content, get_domain, get_favicon
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from summarizer import ai_summarizer
import urllib.parse
from translator import translate_html_components
from similarity import *
from app import create_app 

main = Blueprint('main', __name__)

@main.route('/')
def index():
    sort_by = request.args.get('sort_by', default='datetime')  # Default sort by datetime
    sort_order = request.args.get('sort_order', default='desc')  # Default to descending order
    feeds, sorted_entries = sort_articles_by(sort_by, sort_order)

    return render_template('rss.html', feeds=feeds, sorted_entries=sorted_entries)


@main.route('/<page_name>')
def load_page(page_name):
    return render_template(page_name)

@main.route('/add', methods=['POST'])
def add_feed():
    url = request.form['url']
    title = request.form['title']
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/122.0.2365.106'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            website_name = title if title else soup.title.string.strip() if soup.title else 'Unknown Website'
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
    return redirect(url_for('main.index'))


@main.route('/delete/<int:id>')
def delete_feed(id):
    feed_to_delete = RSSFeed.query.get_or_404(id)
    
    # Delete associated feed entries
    feed_entries_to_delete = FeedEntry.query.filter_by(feed_id=id).all()
    for entry in feed_entries_to_delete:
        db.session.delete(entry)
    
    db.session.delete(feed_to_delete)
    db.session.commit()
    flash('RSS feed deleted successfully!', 'success')
    return redirect(url_for('main.index'))

@main.route('/refresh')
def refresh_feed():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        entries = get_feed_contents(feed.url)
        db.session.add_all(entries)
    db.session.commit()
    flash('Articles refreshed successfully!', 'success')
    return redirect(url_for('main.index'))

@main.route('/summarize')
def summarize():
    feeds = RSSFeed.query.all()
    all_entries = []
    
    for feed in feeds:
        # Summarize all articles from each feed
        all_entries.extend(summarize_content(feed.url))  # Uses the same function to summarize the feed
    
    db.session.commit()  # Commit changes for all summarized entries
    flash('Articles Summarized successfully!', 'success')
    return redirect(url_for('main.index'))


# Summarization code for single article

@main.route('/summarize/<path:link>', methods=['GET'])
def summarize_single_article(link):
    try:
        # Decode the link parameter (if needed)
        decoded_link = urllib.parse.unquote(link)
        
        # Perform summarization for the single article
        entries = summarize_content(decoded_link)  # This will call the right summarization method based on the link
        
        if entries:
            flash('Article Summarized successfully!', 'success')
        else:
            flash('Failed to summarize content properly.', 'warning')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    # Redirect back to the original article page
    return redirect(url_for('main.link_page', param=link))

# Toggle Buttons
@main.route('/toggle_unread/<int:id>', methods=['POST'])
def toggle_unread(id):
    entry = FeedEntry.query.get_or_404(id)
    entry.is_unread = not entry.is_unread
    db.session.commit()
    return jsonify({
        'status': 'success',
        'is_unread': entry.is_unread,
        'message': 'Article marked as unread!' if entry.is_unread else 'Article marked as read!'
    })

@main.route('/toggle_starred/<int:id>', methods=['POST'])
def toggle_starred(id):
    user_id = session.get('user_id')
    entry = FeedEntry.query.get_or_404(id)
    entry.is_starred = not entry.is_starred
    db.session.commit()
    refresh_data(user_id)
    calculate_scores(user_id)
    return jsonify({
        'status': 'success',
        'is_starred': entry.is_starred,
        'message': f'Article {"starred" if entry.is_starred else "unstarred"}!'
    })

@main.route('/toggle_read_later/<int:id>', methods=['POST'])
def toggle_read_later(id):
    entry = FeedEntry.query.get_or_404(id)
    entry.is_read_later = not entry.is_read_later
    db.session.commit()
    return jsonify({
        'status': 'success',
        'is_read_later': entry.is_read_later,
        'message': 'Article marked to read later!' if entry.is_read_later else 'Article removed from read later!'
    })

# Youtube summarize
@main.route('/youtube', methods=['GET', 'POST'])
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

@main.route('/youtube/<videolinkid>')
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

@main.route('/wikipedia', methods=['GET', 'POST'])
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

@main.route('/link/<path:param>', methods=['GET'])
def link_page(param):
    try:
        # Check if param is an integer (ID)
        if param.isdigit():
            feed = RSSFeed.query.get(int(param))  # Fetch feed by ID
            if not feed:
                flash(f'No feed found with the ID: {param}', 'error')
                return redirect(url_for('main.index'))

            # Get the specific feed entry by ID
            feed_contents = FeedEntry.query.filter_by(feed_id=feed.id).all()
            entry = next((entry for entry in feed_contents if entry.id == int(param)), None)
            if not entry:
                flash(f'No article found with the provided ID: {param}', 'error')
                return redirect(url_for('main.index'))

            # Check if lang parameter is provided
            lang = request.args.get('lang')
            if lang:
                # Check if the translation already exists
                translation = Translation.query.filter_by(link=entry.link, language=lang).first()
                
                if not translation:
                    # If translation doesn't exist, translate and save it
                    translated_title, translated_content, translated_summary = translate_html_components(
                        title=entry.title, content=entry.full_content, summary=entry.summarized_content, target_language=lang
                    )

                    # Save the translation in the database
                    translation = Translation(
                        link=entry.link,
                        language=lang,
                        title=translated_title,
                        full_content=translated_content,
                        summarized_content=translated_summary
                    )
                    db.session.add(translation)
                    db.session.commit()

                # Pass the translated content to the template
                return render_template('link_page.html', feed=feed, entry=entry, translation=translation)

            # If no lang parameter, show the original content
            return render_template('link_page.html', feed=feed, entry=entry)

        else:
            # Handle URL link case (if the param is not an ID)
            feed_entry = FeedEntry.query.filter_by(link=param).first()  # Fetch feed entry by URL (link)
            if feed_entry:
                # If feed entry is found, check for language translation
                lang = request.args.get('lang')
                if lang:
                    # Check if the translation already exists
                    translation = Translation.query.filter_by(link=feed_entry.link, language=lang).first()
                    
                    if not translation:
                        # Translate and store the new translation
                        translated_title, translated_content, translated_summary = translate_html_components(
                            title=feed_entry.title, content=feed_entry.full_content, summary=feed_entry.summarized_content, target_language=lang
                        )

                        translation = Translation(
                            link=feed_entry.link,
                            language=lang,
                            title=translated_title,
                            full_content=translated_content,
                            summarized_content=translated_summary
                        )
                        db.session.add(translation)
                        db.session.commit()

                    # Return the translated content
                    return render_template('link_page.html', feed=feed_entry.feed, entry=feed_entry, translation=translation)

                # If no lang parameter, show the original content
                return render_template('link_page.html', feed=feed_entry.feed, entry=feed_entry)

            # If no feed entry is found by URL, try fetching the associated RSS feed and its entries
            feed = RSSFeed.query.filter_by(url=param).first()
            if not feed:
                flash(f'No feed found for the given URL: {param}', 'error')
                return redirect(url_for('main.index'))

            feed_contents = FeedEntry.query.filter_by(feed_id=feed.id).all()
            return render_template('link_page.html', feed=feed, feed_contents=feed_contents, link=param)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.index'))
