import cohere
from dotenv import load_dotenv
import time
import os

# Load environment variables
load_dotenv()

def ai_summarizer(news_info, length="long", format="bullets", temperature=0.9):
    """
    Summarizes the input text using the Cohere API.
    
    Parameters:
        news_info (str): The input text to summarize.
        length (str): Summary length ('short', 'medium', 'long'). Default is 'long'.
        format (str): Output format ('bullets', 'paragraph'). Default is 'bullets'.
        temperature (float): Sampling variability. Default is 0.9.
    
    Returns:
        str: The summarized text.
    """
    cohere_api_key = os.getenv("API-KEY")
    if not cohere_api_key:
        raise ValueError("Cohere API key not found in environment variables.")
    
    co = cohere.Client(cohere_api_key)
    max_attempts = 7

    for attempt in range(1, max_attempts + 1):
        try:
            summary = co.summarize(
                text=news_info,
                model="summarize-xlarge",
                length=length,
                format=format,
                temperature=temperature
            )
            return summary.summary
        except cohere.CohereError as api_error:
            print(f"Error: {api_error}")
            if attempt < max_attempts:
                print(f"Retrying attempt {attempt + 1}...")
                time.sleep(1)
            else:
                print("Maximum retry attempts reached. Unable to summarize.")
                return None
