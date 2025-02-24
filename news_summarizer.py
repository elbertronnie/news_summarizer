import base64
import os
import re
import time
import requests
import yaml
from urllib.parse import urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from newspaper import Article
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

load_dotenv()


# Function to load YAML file
def load_yaml(file_path):
    try:
        # Open the YAML file and load its contents
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)  # Use safe_load for security reasons
        return data
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None


# Function to scrape JSON data
def make_request(url):
    # Send GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        
        return data
    else:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
        return None


def generate_url(base_url, topic, index):
    # Use string formatting to substitute the placeholders in the provided URL
    url = base_url.format(topic=topic, index=index)    
    return url


def get(data, path):
    x = data
    for key in path:
        x = x[key]
    return x


def normalize_url(domain, url):
    if url[0] == '/':
        return domain + url
    else:
        return url


tokenizer = AutoTokenizer.from_pretrained("minhtoan/t5-finetune-cnndaily-news")  
model = AutoModelForSeq2SeqLM.from_pretrained("minhtoan/t5-finetune-cnndaily-news")

def summarize(text):
    tokenized_text = tokenizer.encode('summarize: ' + text, return_tensors="pt")
    model.eval()
    summary_ids = model.generate(tokenized_text, max_length=300, min_length=100)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


wordpress_credentials = os.getenv("WP_USER") + ':' + os.getenv("WP_PASSWORD")
wordpress_header = {'Authorization': 'Basic ' + base64.b64encode(wordpress_credentials.encode()).decode('utf-8')}
wordpress_url = os.getenv("WP_URL")

categories_data = requests.get(wordpress_url+"categories", headers=wordpress_header).json()
categories = { category["slug"]: category["id"] if category["parent"] == 0 else [category["id"], category["parent"]] for category in categories_data }


def get_wordpress_post_urls():
    data = {
        "after": (datetime.now() - timedelta(days=1)).isoformat()
    }
    response = requests.get(wordpress_url+"posts", headers=wordpress_header, json=data)
    return {re.search(r"Source:\s(https?://[^<]+)", str(article["content"])).group(1) for article in response.json()}


def create_wordpress_post(data):
    response = requests.post(wordpress_url+"posts", headers=wordpress_header, json=data)
    print(response)


def upload_media(image_url):
    image_response = requests.get(image_url)

    if image_response.status_code == 200:
        media_headers = {
            'Content-Type': image_response.headers['Content-Type'],
            'Content-Disposition': f'attachment; filename={content_to_name[image_response.headers['Content-Type']]}',
            **wordpress_header
        }
        
        media_response = requests.post(wordpress_url+'media', headers=media_headers, data=image_response.content)

        if media_response.status_code == 201:
            return media_response.json()['id']
    
    return None


yaml_data = load_yaml("sites.yaml")
pages = 1
topics = ["mumbai", "pune", "cricket", "football", "maharashtra", "sport"]
content_to_name = {
    "image/jpeg": "image.jpg",
    "image/png": "image.png",
    "image/webp": "image.webp",
}

while True:
    past_urls = get_wordpress_post_urls()
    for topic in topics:
        article_links = []

        for site in yaml_data.values():
            base_url = site['api_url']
            parsed_url = urlparse(base_url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

            for index in range(site['index_start'], site['index_start'] + pages*site['index_step'], site['index_step']):
                url = generate_url(base_url, topic, index)
                data = make_request(url)
                data = get(data, site['api_path'])
                result = [ normalize_url(domain, get(value, site['api_foreach_path'])) for value in data ]
                if 'filter_out' in site:
                    article_links = article_links + [link for link in result if site['filter_out'] not in link]
                else:
                    article_links = article_links + result

        for url in article_links:
            if url in past_urls:
                continue
            
            article = Article(url=url, language='en')
            article.download()
            article.parse()

            image_id = upload_media(article.top_image)

            data = {}
            data["status"] = "publish"
            data["title"] = article.title
            data["content"] = summarize(article.text) + f"\n\nSource: {url}"
            data["categories"] = categories[topic]
            if article.publish_date is not None:
                data["date"] = article.publish_date.isoformat()
            if image_id is not None:
                data["featured_media"] = image_id
            create_wordpress_post(data)

    time.sleep(3600)
