import tiktoken
import base64

import getCaptionsandNames

tokensttl = 0

# Function to extract text content from the payload
def extract_text_content(messages):
    content = []
    for message in messages:
        if message["role"] == "user":
            for item in message["content"]:
                if item["type"] == "text":
                    content.append(item["text"])
    return " ".join(content)

# Function to count tokens in a string
def count_tokens(text, model_name='gpt-4'):
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    return len(tokens)


