from googletrans import Translator
from lxml import html
from html import unescape

def translate_html_components(title=None, content=None, summary=None, target_language='en'):
    translator = Translator()

    def translate_html_content(html_content):
        if not html_content:
            return html_content

        tree = html.fromstring(html_content)

        # Collect all texts (node.text and tail) and their node references.
        texts_to_translate = []
        nodes = []  # Each entry is a tuple (node, attribute) where attribute is 'text' or 'tail'

        def traverse(node):
            if node.text and node.text.strip():
                texts_to_translate.append(node.text)
                nodes.append((node, 'text'))
            for child in node:
                traverse(child)
                if child.tail and child.tail.strip():
                    texts_to_translate.append(child.tail)
                    nodes.append((child, 'tail'))

        traverse(tree)

        translations = []
        if texts_to_translate:
            try:
                # Attempt batch translation.
                batch_result = translator.translate(texts_to_translate, dest=target_language)
                # Ensure we have a list.
                if not isinstance(batch_result, list):
                    batch_result = [batch_result]
                translations = batch_result
            except Exception as e:
                print(f"Batch translation failed: {e}")
                # Fallback: translate texts one by one.
                for text in texts_to_translate:
                    try:
                        trans = translator.translate(text, dest=target_language)
                        translations.append(trans)
                    except Exception as ex:
                        print(f"Error translating '{text}': {ex}")
                        translations.append(type('Dummy', (), {'text': text})())  # Fallback to original text

        # Verify that translations and nodes match.
        if len(translations) != len(nodes):
            print("Warning: number of translations does not match the number of text nodes.")
        else:
            for (node, attr), trans in zip(nodes, translations):
                try:
                    if attr == 'text':
                        node.text = trans.text
                    else:  # 'tail'
                        node.tail = trans.text
                except Exception as e:
                    print(f"Error assigning translated text: {e}")

        translated_html = html.tostring(tree, pretty_print=True, method="html").decode('utf-8')
        return unescape(translated_html)

    translated_title = translate_html_content(title) if title else None
    translated_content = translate_html_content(content) if content else None
    translated_summary = translate_html_content(summary) if summary else None

    return translated_title, translated_content, translated_summary

# # Example usage:
# if __name__ == "__main__":
#     html_content = """
#     <html>
#       <head><title>Hola Mundo</title></head>
#       <body>
#         <p>Este es un párrafo de ejemplo.</p>
#         <p>Otro párrafo con <strong>texto importante</strong> y más detalles.</p>
#       </body>
#     </html>
#     """
#     translated_title, translated_content, _ = translate_html_components(title=html_content, content=html_content, target_language='en')

# print("Translated Title:", translated_title)
# print("Translated Content:", translated_content)
# print("Translated Summary:", translated_summary)