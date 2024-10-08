import os
import time
from urllib.parse import urljoin
import openai
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import base64
from dotenv import load_dotenv
import logging
from bs4 import BeautifulSoup
import requests
import re
import batch_rename, png_convert


# Load API key from .env file
load_dotenv()

#global variables
api_key = os.getenv('OPENAI_API_KEY')
tokens = float(os.getenv('TOKENS'))
budget = 1
remaining_budget = budget - tokens
add_api = False
api_test = False
use_key = api_key
cost = float(0.000)
costr = float(0.000)
progress = 0
language = {"f":"French","e":"English" }
language_key = simpledialog.askstring("Select output language", "Input 'f' for french and 'e' for english")


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

### Settings ###

#Define prompt text for request to chatGPT

prompt = str("Generate a caption and a file name for this image based on its context. "
             f"The caption and file name needs to be in {language[language_key]}"
             "Please segregate the outputs as 'Caption: <caption>' and 'File name: <file_name>'."
             "Caption should be: 7-10 words, minimize the use of verbs and avoid abusing such words as: "
             "and, a, the, upon, throughout and other such complicated words. "
             "Don't use numbers, special characters, accents, uppercase, points, hyphens etc. "
             "JUST letters. "
             "If too much elements on the pic, describe the overall scene (it could be "
             "about the location, the character, the weather…). "
             "The description should form a short logical sentence. prioritize sentence "
             "structure over reaching the max word count. "
             "The filename should be: based on context, be in lowercase, and use hyphens instead of spaces, and be 4 words. "
             )

imgquality = "low"

#Check if APIkey is defined or not, if not defined request user to add. if defined ask user if they want to update
def apikey_check(key):
    if key == "":
        api_key = simpledialog.askstring("Input",
                                         "No API Key stored in .env file, please input an openAI API key")
        add_api = True
        return api_key, add_api
    else:
        add_api = False
        if remaining_budget <= 0.1:
            add_api = messagebox.askyesnocancel("A",
                                            "Invalid API key, would you like to chnage change the openAI API key?")
        if add_api:
            api_key = simpledialog.askstring("Input API Key",
                                             "Enter an openAI API key: ")
            if api_key == None:
                api_key = key
                return api_key, add_api
            return api_key, add_api

        else:
            api_key = key
            return api_key, add_api

#function to generate captions and file names using GPT-4o Vision
def generate_caption_and_filename(image_path):
    global use_key, tokens, cost, costr, api_test

    if image_path.startswith('http'):
        image = image_path
        # Regular expression to find the part of the URL after the image extension
        match = re.search(r'\.(png|jpg|jpeg|gif)(\?.*)$', image)
        if match:
            # Extract the part of the URL before the suffix
            base_url = image[:match.start()]
            extension = match.group(1)
            image = base_url + "." + extension


    else:
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            image = f"data:image/jpeg;base64,{image_data}"

    # Define the request payload
    data = {
        "model": "gpt-4o-mini",
        "temperature": 0.95,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"{image}",
                            "detail": f"{imgquality}"

                        }
                    }
                ]
            }
        ],
        "max_tokens": 35,
    }

    # Attempt to call GPT-4o Vision API with retry on rate limit error
    for attempt in range(3):  # Retry up to 3 times
        try:
            with requests.post("https://api.openai.com/v1/chat/completions", json=data, headers={
                "Authorization": f"Bearer {use_key}"
            }) as response:
                if response.status_code == 200:
                    api_test = True
                    response_json = response.json()
                    # Extract and format the caption and file name
                    response_text = response_json['choices'][0]['message']['content'].strip()
                    #tokens += estimator.count_tokens(response_text)
                    usage = (response_json['usage'])
                    promptcost = usage['prompt_tokens'] * 0.00000015 * 5
                    completioncost = usage['completion_tokens'] * 0.0000006 * 5
                    cost += promptcost + completioncost
                    costr = round(cost, 5)
                    try:
                        caption = response_text.split('Caption: ')[1].split('File name: ')[0].strip()
                    except:
                        print(f"Couldn't generate caption from response: {response_text}'")
                    # Normalize to lowercase and use regex to find the file name
                    match = re.search(r'file\s*name:\s*(.*)', response_text, re.IGNORECASE)
                    file_name = match.group(1).strip()
                    try:
                        print(f'filename: {file_name}, caption: {caption}')
                        return caption, file_name
                    except:
                        print(f"couldn't process response '{response_text}'")
                        caption = "Error, no caption"
                        file_name = "Error, no filename"
                        return caption, file_name


                elif response.status_code == 401:
                    print('Incorrect apiKey provided')
                    messagebox.showwarning(title="API key error", message="Incorrect apiKey provided, please provide a correct API key")
                    use_key = apikey_check("")
                    time.sleep(1)
                else:
                    logging.error(f"Failed to get a valid response: {response.content}")
                    time.sleep(5)
        except openai.RateLimitError as e:
            logging.warning(f"Rate limit exceeded: {e}. Retrying in 10 seconds...")
            print(f'Rate limit exceeded: {e}. Retrying in 10 seconds...')
            time.sleep(10)  # Wait for 10 seconds before retrying
        except openai.OpenAIError as e:
            logging.error(f"OpenAI error: {e}.")
            return "error-processing-image.jpg", "error-processing-image.jpg"
    logging.error(f"Failed to process image after multiple attempts: {image_path}")
    return "error-processing-image.jpg", "error-processing-image.jpg"


def process_images(image_paths, imgcount):
    global progress
    results = []
    workload = 100/imgcount
    with requests.Session():
        for image_path in image_paths:
            try:
                result = generate_caption_and_filename(image_path)
                results.append(result)
                progress += workload
                rprogress = round(progress, 2)
                print(f'processing {rprogress}%')
            except:
                print(f"error processing image, exiting loop")
                #break
    return results


def save_results_to_file(url, results):
    with open("captions_and_filenames.txt", "w") as f:
        f.write(f"Source URL: {url}\n\n")
        for image_path, caption, new_file_name in results:
            # Normalize the path and then extract the filename
            normalized_path = os.path.normpath(image_path)
            original_file_name = os.path.basename(normalized_path)
            f.write(f"Original:{original_file_name}  New File Name:{new_file_name} Caption:{caption}\n")
        f.write(f'Total cost for this query was approximately: {costr}€')

def process_all_images(image_paths, imgcount, url=None, path=None):
    print(url)
    # Process images synchronously
    captions_and_filenames = process_images(image_paths, imgcount)

    results = []
    for image_path, (caption, file_name) in zip(image_paths, captions_and_filenames):
        file_extension = os.path.splitext(image_path)[1]
        new_file_name = file_name, file_extension
        results.append((image_path, caption, new_file_name))

    if url != "":
        save_results_to_file(url, results)
        logging.info(f"Results saved to captions_and_filenames.txt")
    else:
        # Print the list of original file names, captions, and new file names
        for original, caption, new in results:
            print(f"Original: {original}, Caption: {caption}, New File Name: {new}")

        save_results_to_file(path, results)
        logging.info(f"Results saved to captions_and_filenames.txt")

        # Ask the user for confirmation
        root = tk.Tk()
        root.withdraw()  # Hide the root window






''' 
def select_images_from_website(use_key):
    url = simpledialog.askstring("Input", "Please enter the website URL:")
    if not url:
        return

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    image_paths = [img['src'] for img in soup.find_all('img') if img.get('src')]

    # Filter out data URLs and make relative URLs absolute
    image_paths = [
        img if img.startswith(('http', 'https')) else urljoin(url, img)
        for img in image_paths
        if not img.startswith('data:')
    ]

    ttlimages = len(image_paths)

    if not image_paths:
        messagebox.showinfo("No images found", "No images found on the provided URL.")
        return

    # Here you would call your function to process all images
    # Assuming it is already defined in your script
    path = ""
    process_all_images(image_paths, ttlimages, url, path)

'''

from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests


def select_images_from_website(use_key):
    url = simpledialog.askstring("Input", "Please enter the website URL:")
    if not url:
        return

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get all image tags
    images = soup.find_all('img')

    # Extract image URLs from both `src` and `srcset` attributes
    image_paths = []

    for img in images:
        img_url = img.get('src')

        # Handle protocol-relative URLs (starting with //)
        if img_url and img_url.startswith('//'):
            img_url = 'https:' + img_url  # Prepend 'https:' to protocol-relative URLs

        # Extract the largest image from 'srcset' if available
        srcset = img.get('srcset')
        if srcset:
            # Split the 'srcset' values and take the last one (largest resolution)
            srcset_urls = [url.split()[0] for url in srcset.split(',')]
            largest_image_url = srcset_urls[-1]

            # Handle protocol-relative URLs in srcset as well
            if largest_image_url.startswith('//'):
                largest_image_url = 'https:' + largest_image_url

            # Use the largest image from srcset as the final URL
            img_url = largest_image_url

        # Add to image paths if a valid URL is found
        if img_url:
            image_paths.append(img_url)

    ttlimages = len(image_paths)

    if not image_paths:
        messagebox.showinfo("No images found", "No images found on the provided URL.")
        return

    # Here you would call your function to process all images
    path = ""
    process_all_images(image_paths, ttlimages, url, path)


def select_folder_and_process_images(use_key):
    global path
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file dialog to select a folder
    folder_path = filedialog.askdirectory()

    # List all image files in the selected folder
    image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

    ttlimages = len(image_paths)
    # Process the images
    url = ""
    path = folder_path
    print(path)
    process_all_images(image_paths, ttlimages, url, path)
    return path

def select_folder():
    global path
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file dialog to select a folder
    folder_path = filedialog.askdirectory()

    path = folder_path
    print(path)
    return path

def select_file():
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file dialog to select a folder
    filepath = filedialog.askopenfile().name
    return filepath


def update_api(add_api, use_key, tokens):
    global api_test

    # Define the .env file path, assuming it's in the same directory as your script
    env_file_path = ".env"

    # Read the existing .env file contents
    if os.path.exists(env_file_path):
        with open(env_file_path, "r") as env_file:
            lines = env_file.readlines()
    else:
        lines = []

    # Variables to track if the keys were found
    key_found = False
    tokens_found = False
    current_api_key = None

    # First pass to find the current OPENAI_API_KEY
    for line in lines:
        if line.startswith("OPENAI_API_KEY="):
            current_api_key = line.strip().split("=", 1)[1]
            break

    # Set tokens to 0 only if both add_api and api_test are True, and use_key is not equal to current_api_key
    if add_api and api_test and current_api_key != use_key:
        tokens = 0

    # Second pass to write the updated .env file
    with open(env_file_path, "w") as env_file:
        for line in lines:
            if line.startswith("OPENAI_API_KEY="):
                if add_api:
                    env_file.write(f"OPENAI_API_KEY={use_key}\n")
                else:
                    env_file.write(line)
                key_found = True
            elif line.startswith("TOKENS="):
                env_file.write(f"TOKENS={tokens}\n")
                tokens_found = True
            else:
                env_file.write(line)

        # If add_api is True and the API key was not found, append it
        if add_api and not key_found:
            env_file.write(f"OPENAI_API_KEY={use_key}\n")

        # If the TOKENS key was not found, append it
        if not tokens_found:
            env_file.write(f"TOKENS={tokens}\n")


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    if remaining_budget >= 0:
        use_key, add_api = apikey_check(api_key)
        # Initialize OpenAI client
        openai.api_key = use_key

        if add_api != None:
            source = simpledialog.askstring("Input",
                                             "If you'd like to load files from computer input 'c', if you would like to load files from a website, input 'w'")

            if source == 'c':
                select_folder_and_process_images(use_key)
                directory_path = path
                print(directory_path)
                rename = messagebox.askyesnocancel("Rename files","Would you also like to rename the files in the input folder based on the Chatgpt output?")
                # rename = True
                if rename == True:
                   batch_rename.rename_files("captions_and_filenames.txt")
                convert = messagebox.askyesnocancel("Convert","Would you also like to convert the output files in to PNG format?")
                if convert == True:
                    # Select input and output folders
                    input_folder = directory_path
                    output_folder = png_convert.select_folder("Select the folder to save PNG images")
                    # Convert images with optimization
                    png_convert.convert_jpeg_to_png(input_folder, output_folder, optimize=True)

            elif source == 'w':
                select_images_from_website(use_key)
            else:
                messagebox.showerror("Invalid input", "Please enter either 'c for computer' or 'w for website'.")

            consumed_tokens = tokens + costr
            update_api(add_api, use_key, consumed_tokens)
            messagebox.showinfo("Cost",f'Total cost for this query was approximately: {costr}€')
        else:
            messagebox.showerror("API KEY EXPIRED","API key expired, please contact Sani Vesanen to renew API key")
            use_key, add_api = apikey_check(api_key)
            # Initialize OpenAI client
            openai.api_key = use_key
            consumed_tokens = tokens + costr
            update_api(add_api, use_key, consumed_tokens)




if __name__ == "__main__":
    main()