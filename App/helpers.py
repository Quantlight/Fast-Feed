# helpers.py
import feedparser
from models import RSSFeed, FeedEntry
import article_parser
import requests
import re
from summarizer import ai_summarizer
import wikipedia
from bs4 import BeautifulSoup

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
        full_content = article_content(entry.link)
        full_content = remove_blank_lines(full_content)
        _summarized_content = ai_summarizer(full_content)
        print(_summarized_content)
        if not existing_entry:
            new_entry = FeedEntry(
                title=entry.title,
                author=entry.author,
                raw_description=entry.description,
                short_description=entry.summary,
                full_content=entry.content[0].value if hasattr(entry, 'content') else '',
                summarized_content=_summarized_content,
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

def article_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }

    try:
        # Requestion information from website by providing url and headers using requests.
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        html = response.text
        # Sending the given html to the article_parser to extract only useful information and convert it into markdown format. 
        title, content = article_parser.parse(url=url, html=html, output='markdown', timeout=5)
        return content
    
    # Handle all the errors while visiting the website.
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the article: {e}")
        # Return nothing.
        return ""
    
def remove_blank_lines(_full_content):
    return re.sub(r'^\s*\n', '', _full_content, flags=re.MULTILINE)

def extract_video_id(video_link):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})(?:\S+)?'
    match = re.search(pattern, video_link)
    if match:
        return match.group(1)
    else:
        return None

def remove_citations(text):
    # Remove citation patterns like [34], [35], [21][36][37], etc.
    cleaned_text = re.sub(r'\[\d+\](\[\d+\])*', '', text)
    # remove \n characters
    cleaned_text = cleaned_text.replace('\n', ' ')
    return cleaned_text

def extract_text_from_wikipedia(wiki_link):
    try:
        r = requests.get(wiki_link)
        soup = BeautifulSoup(r.text,'html.parser').select('body')[0]
        paragraphs = []
        
        for tag in soup.find_all():
            # For Paragraph use p tag
            if tag.name=="p":
                text = remove_citations(tag.text)
                # use text for fetch the content inside p tag
                paragraphs.append(text)
        
        output = ""
        for i in range(len(paragraphs)):
            output += paragraphs[i]
            if i < len(paragraphs) - 1:
                output += ''
        #print(output, '\n\n')   
        return output
        
    except wikipedia.exceptions.PageError as e:
        print(f"Error: {e}")
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Error: {e}")
