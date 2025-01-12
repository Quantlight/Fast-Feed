from trafilatura import fetch_url, extract

def fetch_content(link):
    """
    Fetches and extracts content from a given link using Trafilatura.

    Args:
        link (str): The URL of the page to fetch content from.

    Returns:
        str: Extracted content in markdown format if available, otherwise None.
    """
    content = fetch_url(link)
    if content:
        result = extract(
            content,
            favor_precision=True,
            include_links=True,
            include_images=True,
            include_tables=True,
            output_format='html'
        )
        return result
    return None

