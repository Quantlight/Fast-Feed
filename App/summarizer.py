import cohere
from cohere.error import *
from dotenv import load_dotenv
import time
import os
load_dotenv() 

def ai_summarizer(news_info):
    # Get Your own key from Cohere Website 
    cohere_api_key = os.getenv("API-KEY")
    co = cohere.Client(cohere_api_key)

    # Number of times to Retry when there is an error
    max_attempts = 7

    # Requesting AI to summarize the Information and defining the maximun amount of tokens to be recieved.
    for attempt in range(1, max_attempts + 1):
        try:
            summary = co.summarize(text=news_info,
                                   model="summarize-xlarge",
                                   length="long",
                                   format="bullets",
                                   temperature=0.9)

            return summary.summary
        except CohereAPIError as api_error:
            print(f"Error: {api_error.message}")
            if attempt < max_attempts:
                print(f"Retrying attempt {attempt + 1}...")
                time.sleep(1)  # Adding a small delay before retrying
            else:
                print(f"Maximum retry attempts reached. Unable to summarize.")
                break