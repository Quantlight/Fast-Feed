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
from datetime import datetime, timezone
from dateutil import parser
from urllib.parse import urljoin, urlparse
import markdown2
from custom_scraper import fetch_content
from googletrans import Translator, LANGUAGES
from flask import current_app as app
import statistics

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
                date=parse_datetime(entry.published) if hasattr(entry, 'published') else datetime.now(timezone.utc),                author = entry.author if hasattr(entry, 'author') else 'None',
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

def recommended_articles(min_count=3, max_count=10, min_threshold=0.0):
    """
    Returns a dynamic list of recommended articles based on the variance
    of similarity scores.
    
    Args:
        min_count (int): The minimum number of recommendations.
        max_count (int): The maximum number of recommendations.
        min_threshold (float): Minimum similarity score for an article to be considered.
    
    Returns:
        list: List of recommended FeedEntry objects.
    """
    # Retrieve all articles sorted by similarity score descending
    query = FeedEntry.query.order_by(FeedEntry.similarity_score.desc())
    candidate_articles = query.all()
    
    # Filter articles that meet the minimum similarity threshold.
    eligible_articles = [article for article in candidate_articles 
                         if article.similarity_score >= min_threshold]
    
    if not eligible_articles:
        return []
    
    # Compute the standard deviation (stdev) of similarity scores.
    scores = [article.similarity_score for article in eligible_articles]
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0
    
    # Define thresholds for the standard deviation.
    # If stdev is high (>= high_std_threshold), there's a big gap among scores → choose min_count.
    # If stdev is low (<= low_std_threshold), scores are similar → choose max_count.
    low_std_threshold = 0.05   # adjust based on your data range
    high_std_threshold = 0.2   # adjust based on your data range
    
    if stdev >= high_std_threshold:
        dynamic_limit = min_count
    elif stdev <= low_std_threshold:
        dynamic_limit = max_count
    else:
        # Linear interpolation: as stdev decreases from high_std_threshold to low_std_threshold,
        # the limit increases from min_count to max_count.
        ratio = (high_std_threshold - stdev) / (high_std_threshold - low_std_threshold)
        dynamic_limit = int(min_count + ratio * (max_count - min_count))
    
    # Ensure the dynamic limit stays between min_count and max_count.
    dynamic_limit = max(min_count, min(dynamic_limit, max_count))
    
    recommendation = eligible_articles[:dynamic_limit]
    print(recommendation)
    return recommendation

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
    elif sort_by == 'simi':
        if sort_order == 'asc':
            query = query.order_by(FeedEntry.similarity_score.asc())
        else:
            query = query.order_by(FeedEntry.similarity_score.desc())
    else:  # Default to sorting by date
        if sort_order == 'asc':
            query = query.order_by(FeedEntry.date.asc())  # Direct column access
        else:
            query = query.order_by(FeedEntry.date.desc())

    # Get the recommendation articles
    recommendation = recommended_articles()
    # Apply pagination
    sorted_entries = query.limit(limit).offset(offset).all()
    return feeds, sorted_entries, recommendation

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
        soup = BeautifulSoup(r.text,'lxml').select('body')[0]
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
        soup = BeautifulSoup(response.content, 'lxml')

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

def parse_datetime(dateTimeString):
    """Convert string to timezone-aware datetime object"""
    try:
        return parser.parse(dateTimeString).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)  # Fallback to current UTC time

@app.template_filter('format_datetime')
def format_datetime_filter(dt_or_str):
    """Jinja filter to display original feed datetime without timezone conversion"""
    try:
        # If already a datetime object (from database), format directly
        if isinstance(dt_or_str, datetime):
            return dt_or_str.strftime("%B %d, %Y %I:%M %p")
        
        # If string input (raw feed data), parse but keep original time
        dt = parser.parse(dt_or_str, ignoretz=True)
        return dt.strftime("%B %d, %Y %I:%M %p")
        
    except (ValueError, TypeError, AttributeError):
        return "Date unavailable"
    
def print_elements_from_url(url):
    content = fetch_content(url)
    return content

