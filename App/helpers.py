# helpers.py
import feedparser
from models import RSSFeed, FeedEntry
import article_parser
import requests
import re
from summarizer import ai_summarizer
import wikipedia
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
from urllib.parse import urljoin, urlparse


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
        content = print_elements_from_url(entry.link)
        if not existing_entry:
            new_entry = FeedEntry(
                title = entry.title,
                date = format_datetime(entry.published) if hasattr(entry, 'published') else None,
                author = entry.author if hasattr(entry, 'author') else 'None',
                raw_description=entry.description,
                short_description=content,
                full_content=entry.content[0].value if hasattr(entry, 'content') else '',
                img=entry.enclosures[0].href if hasattr(entry, 'enclosures') and entry.enclosures else '',
                link=entry.link,
                feed_id=RSSFeed.query.filter_by(url=url).first().id
            )
            entries.append(new_entry)
    return entries

def summarize_content(url):
    feed = feedparser.parse(url)
    entries = []
    
    for entry in feed.entries:
        existing_entry = FeedEntry.query.filter_by(link=entry.link).first()
        if existing_entry and not existing_entry.summarized_content:
            full_content = print_elements_from_url(entry.link)
            full_content = remove_blank_lines(full_content)
            summarized_content = ai_summarizer(full_content)
            print(summarized_content)
            existing_entry.summarized_content = summarized_content
            entries.append(existing_entry)  # Append existing entry for tracking updated entries
    
    return entries

def sort_articles_by(sort_by, sort_order, limit=20, offset=0):
    feeds = RSSFeed.query.all()
    feed_contents = {}
    if not feeds:
        return [], {}

    for feed in feeds:
        if sort_by == 'link':
            if sort_order == 'asc':
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.feed_id.asc()).limit(limit).offset(offset).all()
            else:
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.feed_id.desc()).limit(limit).offset(offset).all()
        elif sort_by == 'title':
            if sort_order == 'asc':
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.title.asc()).limit(limit).offset(offset).all()
            else:
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.title.desc()).limit(limit).offset(offset).all()
        else:
            if sort_order == 'asc':
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.date.asc()).limit(limit).offset(offset).all()
            else:
                sorted_entries = FeedEntry.query.filter_by(feed_id=feed.id).order_by(FeedEntry.date.desc()).limit(limit).offset(offset).all()
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

# Get icon of the website
def get_favicon(url):
    # Get the domain from the URL
    domain = get_domain(url)
    if domain:
        favicon_url = f"https://{domain}/favicon.ico"
        try:
            # Attempt to fetch the favicon
            response = requests.get(favicon_url)
            if response.status_code == 200:
                return favicon_url
            else:
                return "https://cdn-icons-png.flaticon.com/512/4076/4076373.png"
        except requests.RequestException:
            # Return default favicon URL if there's an error fetching the favicon
            return "https://cdn-icons-png.flaticon.com/512/4076/4076373.png"
    else:
        # Return default favicon URL if domain extraction fails
        return "https://cdn-icons-png.flaticon.com/512/4076/4076373.png"

# Get the domain only which will exclude all the additional parameters
def get_domain(url):
    # Regular expression pattern to extract domain from URL
    pattern = r"https?://(?:www\.)?([a-zA-Z0-9.-]+).*"
    match = re.match(pattern, url)
    if match:
        return match.group(1)
    else:
        return None
    
def format_datetime(dateTimeString):
    try:
        date = parser.parse(dateTimeString)
        formatted_date = date.strftime("%A, %B %d, %Y %I:%M %p")
        return formatted_date
    except ValueError:
        return "Invalid datetime format"
    
# Extract contents from urls
def check_keywords(content):
    parent_element = content.find_parent(class_=lambda x: x and ('comment' in x or 
                                                                 'Popular' in x or 
                                                                 'LinkStackWrapper' in x or 
                                                                 'Footer' in x or 
                                                                 'answers' in x or 
                                                                 'copyright' in x or 
                                                                 'more' in x or 
                                                                 'newsletter' in x or 
                                                                 'basis' in x or 
                                                                 'hidden' in x))
    return parent_element is not None

def get_img_src(img_src, url):
    base_url = urljoin(url, '/')  # Get the base URL
    if img_src.startswith('/'):
        # Relative URL from the root
        img_url = urljoin(base_url, img_src)
    elif img_src.startswith('http'):
        img_url = img_src
    else:
        # Relative URL from the current page
        img_url = url + '/' + img_src
    return img_url
    
def print_elements_from_url(url):
    # Send a GET request to the URL and get the HTML content
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        result = []

        contents = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'img'])
        result.append("Content:")
        for content in contents:
            if not check_keywords(content):
                    if content.name == 'img':
                        img_src = get_img_src(content['src'], url)
                        result.append(f"<img src='{img_src}'>")
                    else:
                        result.append(content.text.strip())

        return '\n'.join(result)  # Concatenate the list items into a single string with newline characters
    else:
        return f"Failed to fetch the URL. Status code: {response.status_code}"