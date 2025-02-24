# Hacksmiths News Summarizer

An AI agent that can autononously create news summaries by scrapping the news websites and using LLMs to generate short summaries of the news articles. The summaries of the news articles are published at (https://hacksmiths-demo-elbyronn.wasmer.app)[https://hacksmiths-demo-elbyronn.wasmer.app].

## Features

- Automatic web scraping
- Automatic generation of news summaries
- Used an open source fine-tuned LLM
- SEO Optimization
- Multiligual Support
- Supports multiple nested topics
    - Maharashtra
        - Mumbai
        - Pune
    - Sports
        - Cricket
        - Football

## Running the code

### Setup environment variables

Place the code below in a `.env` file after specifying the Wordpress username and password.
```env
WP_URL="https://hacksmiths-demo-elbyronn.wasmer.app/wp-json/wp/v2/"
WP_USER="..."
WP_PASSWORD="..."
```

### Install dependencies
```sh
pip install -r requirements.txt
```

### Run the program
```sh
python news_summarizer.py
```

## Methodology

We used the JSON API of popular news websites to get a list of urls of articles. Currently only 2 websites are suppported. Since the API of websites are different, we made a generalized approach to access data. Each API's url format was identified first, then within the output JSON, exact sequence of keys that would lead to the article url was also noted. This is stored in `sites.yaml`. This kind of format helps to easily add more websites later.

These article urls were then provided to the library (`newspaper3k`)[https://newspaper.readthedocs.io/en/latest] which helps to extract the title, content, date, etc from the article urls. The content was then passed to a LLM for summarization. Since we wanted this to run fast, we decided on using a small model but one that is heavily fine-tuned for news summarization. We finally decided on (`minhtoan/t5-finetune-cnndaily-news`)[https://huggingface.co/minhtoan/t5-finetune-cnndaily-news] from Hugging Face.

For a CMS, we decided on Wordpress since it was the most famous one. A News based theme was decided to give it a good look and feel. We have hosted the wordpress site using Wasmer. Wordpress plugins were used for adding SEO Optimization and Multilingual Support with the help of Google Translate.
