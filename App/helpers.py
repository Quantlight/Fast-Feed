# helpers.py
import feedparser
from sqlalchemy import func
from models import RSSFeed, FeedEntry, db
import article_parser
import requests
import re
from summarizer import ai_summarizer
import wikipedia
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
from urllib.parse import urljoin, urlparse
import markdown2
from custom_scraper import fetch_content
from googletrans import Translator, LANGUAGES

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
            content = print_elements_from_url(entry.link)
            new_entry = FeedEntry(
                title = entry.title,
                date = format_datetime(entry.published) if hasattr(entry, 'published') else None,
                author = entry.author if hasattr(entry, 'author') else 'None',
                raw_description=entry.description,
                full_content=content,
                img=entry.enclosures[0].href if hasattr(entry, 'enclosures') and entry.enclosures else '',
                link=entry.link,
                feed_id=RSSFeed.query.filter_by(url=url).first().id
            )
            entries.append(new_entry)
    return entries

# def summarize_content(url):
#     feed = feedparser.parse(url)
#     entries = []
    
#     for entry in feed.entries:
#         existing_entry = FeedEntry.query.filter_by(link=entry.link).first()
#         if existing_entry and not existing_entry.summarized_content:
#             full_content = print_elements_from_url(entry.link)
#             full_content = remove_blank_lines(full_content)
#             summarized_content = ai_summarizer(full_content)
#             summarized_content = markdown2.markdown(summarized_content, extras=["markdown-urls"])
#             print(summarized_content)
#             existing_entry.summarized_content = summarized_content
#             entries.append(existing_entry)  # Append existing entry for tracking updated entries
    
#     return entries

def summarize_content(url):
    # Check if the URL is a feed URL or a single article URL
    if 'feed' in url or url.endswith('.xml') or 'rss' in url:
        # Handle RSS feed: Summarize all articles in the feed
        return summarize_feed(url)
    else:
        # Handle single article URL: Summarize only the specific article
        return summarize_single_article_content(url)

def summarize_feed(feed_url):
    feed = feedparser.parse(feed_url)
    entries = []

    for entry in feed.entries:
        # Summarize each article in the feed
        entries.extend(summarize_single_article_content(entry.link))  # Calls single article summarizer
    
    return entries
def summarize_single_article_content(article_url):
    # Find the article entry in the database
    existing_entry = FeedEntry.query.filter_by(link=article_url).first()
    
    # If the article exists and has not been summarized yet
    if existing_entry and not existing_entry.summarized_content:
        # Fetch the full content, clean it, and summarize it
        full_content = print_elements_from_url(article_url)
        full_content = remove_blank_lines(full_content)
        
        # Summarize content and convert to markdown
        summarized_content = ai_summarizer(full_content)
        summarized_content = markdown2.markdown(summarized_content, extras=["markdown-urls"])
        
        # Save the summarized content in the database
        existing_entry.summarized_content = summarized_content
        db.session.commit()
        
        return [existing_entry]  # Return as a list for consistency (for both single and multiple articles)
    
    return []  # Return empty list if no article found or already summarized


def sort_articles_by(sort_by, sort_order, limit=200, offset=0):
    # Query all feed entries across all feeds
    feeds = RSSFeed.query.all()
    query = FeedEntry.query
    
    # Apply sorting globally based on sort_by and sort_order
    if sort_by == 'link':
        if sort_order == 'asc':
            query = query.order_by(FeedEntry.link.asc())
        else:
            query = query.order_by(FeedEntry.link.desc())
    elif sort_by == 'title':
        if sort_order == 'asc':
            query = query.order_by(FeedEntry.title.asc())
        else:
            query = query.order_by(FeedEntry.title.desc())
    else:  # Default to sorting by date
        if sort_order == 'asc':
            query = query.order_by(func.datetime(FeedEntry.date).asc())  
        else:
            query = query.order_by(func.datetime(FeedEntry.date).desc()) 


    # Apply pagination
    sorted_entries = query.limit(limit).offset(offset).all()

    return feeds, sorted_entries

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

def get_favicon(url):
    # Helper function to fetch the favicon URL
    def fetch_favicon_from_url(url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.url
        except requests.RequestException:
            pass
        return None

    # Extract domain from the URL
    domain = urlparse(url).netloc
    if not domain:
        return "https://cdn-icons-png.flaticon.com/512/4076/4076373.png"

    # 1. Look for the favicon at the root of the domain
    favicon_url = fetch_favicon_from_url(f"https://{domain}/favicon.ico")
    if favicon_url:
        return favicon_url

    # 2. Look for <link rel="shortcut icon"> or <link rel="icon"> in HTML
    try:
        response = requests.get(f"https://{domain}")
        soup = BeautifulSoup(response.content, 'html.parser')

        # 3. Look for Apple touch icons
        apple_icon = soup.find('link', rel='apple-touch-icon') or soup.find('link', rel='apple-touch-icon-precomposed')
        if apple_icon and apple_icon.get('href'):
            apple_icon_url = urljoin(url, apple_icon['href'])
            if fetch_favicon_from_url(apple_icon_url):
                return apple_icon_url

        # Check for <link rel="shortcut icon">
        link = soup.find('link', rel='shortcut icon') or soup.find('link', rel='icon')
        if link and link.get('href'):
            favicon_url = urljoin(url, link['href'])
            if fetch_favicon_from_url(favicon_url):
                return favicon_url

    except requests.RequestException:
        pass

    # 4. Use Google's favicon service as a fallback
    return f"http://www.google.com/s2/favicons?domain={domain}"


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
    
def print_elements_from_url(url):
    content = fetch_content(url)
    return content

def translate_text(title, full_content, summarized_content, target_language='hi'): # Translate to Hindi
    """
    Translates the given text into a single target language.

    :param text: The text to translate
    :param target_language: The language code to translate the text into (e.g., 'es' for Spanish)
    :return: The translated text
    """    
    translator = Translator()
    translated_title = translator.translate(title, dest=target_language)
    translated_content = translator.translate(full_content, dest=target_language)
    translated_summary = translator.translate(summarized_content, dest=target_language)
    print(f"\n Title: {translated_title}\n Content: {translated_content}\n Summary: {translated_summary}\n")
    # return translated_title.text, translated_content.text, translated_summary.text