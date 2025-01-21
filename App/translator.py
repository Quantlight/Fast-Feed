from googletrans import Translator
from lxml import html
from html import unescape

def translate_html_components(title=None, content=None, summary=None, target_language='en'):
    # Initialize the Google Translate API
    translator = Translator()

    # Function to translate HTML content
    def translate_html_content(html_content):
        if not html_content:
            return html_content  # Return as is if there's no content to translate

        # Parse the HTML content using lxml
        tree = html.fromstring(html_content)

        # Function to translate text inside tags
        def translate_element(element):
            # Translate the element's text if it exists and isn't empty
            if element.text and element.text.strip():  # Avoid translating None or empty strings
                try:
                    translated_text = translator.translate(element.text, dest=target_language).text
                    element.text = translated_text  # Replace the text with the translated text
                except Exception as e:
                    # Log the error, but do not interrupt the process
                    print(f"Error translating text: {e}")

            # Handle children (for nested tags like <strong>)
            for child in element:
                if child.text and child.text.strip():  # Check if child element has text
                    translate_element(child)  # Recursively translate text inside child elements

                # Check for tail text (text after the element's children)
                if child.tail and child.tail.strip():  # Check if there's tail text and it's not None or empty
                    try:
                        translated_tail = translator.translate(child.tail, dest=target_language).text
                        child.tail = translated_tail  # Replace the tail text with the translated text
                    except Exception as e:
                        # Log the error, but do not interrupt the process
                        print(f"Error translating tail text: {e}")

        # Traverse all elements and translate text nodes
        for element in tree.iter():
            if element.text:
                translate_element(element)

        # Convert the tree back to an HTML string (ensure proper encoding without entities)
        translated_html = html.tostring(tree, pretty_print=True, method="html").decode('utf-8')

        # Correct any unescaped HTML entities in the translated HTML
        translated_html = unescape(translated_html)  # Call unescape properly

        return translated_html

    # Translate each component if provided
    translated_title = translate_html_content(title) if title else None
    translated_content = translate_html_content(content) if content else None
    translated_summary = translate_html_content(summary) if summary else None

    return translated_title, translated_content, translated_summary

# # Example usage
# title = "<title>Example</title>"
# content = """
# <html>
#     <body>
#         <h1>Hello, world!</h1>
#         <p>This is an example of <strong>HTML</strong> content.</p>
#         <a href="https://hello.com">Click here</a>
#     </body>
# </html>
# """
# summary = "<p>This is a summary of the content.</p>"

# translated_title, translated_content, translated_summary = translate_html_components(title, content, summary, target_language='hi')

# print("Translated Title:", translated_title)
# print("Translated Content:", translated_content)
# print("Translated Summary:", translated_summary)