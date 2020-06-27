import logging
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.cli import tqdm

_batch = 0


def get_content(url):
    response = requests.get(url)
    status_code = int(response.status_code)
    print(url, status_code)
    if status_code != 200:
        logging.info("GET request for URL {} returned status code of {}".format(url, status_code))
        return None, status_code
    content = BeautifulSoup(response.text, 'html.parser')
    return content, status_code


def extract_subjects(url):
    content, status_code = get_content(url)
    if status_code != 200:
        return list()
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/archive/' in str(x)]
    urls = [url+x for x in urls]
    return urls


def find_title(content):
    title = content.find_all('h1', attrs={'class': 'title'})[0]
    data = title.text.split('\n')[-1]
    return data


def find_abstract(content):
    abstract = content.find_all('blockquote', attrs={'class': 'abstract'})[0]
    abstract = abstract.text.split('\nAbstract: ')[-1]
    return abstract


def find_subject(content):
    subject = content.find_all('span', attrs={'class': 'primary-subject'})[0]
    subject = subject.text.split('\n')[-1]
    return subject


def save_curated_data(content, batch):
    df = pd.DataFrame(content)
    root_path = os.path.join(os.getcwd(), 'Curated_Data')
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    df.to_csv(os.path.join(root_path, 'curated_dataset_{}.csv'.format(batch)), index=False)


def extract_arxiv_links(arxiv_url, url, batch):
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/abs/' in str(x)]
    urls = [arxiv_url+x for x in urls]
    time.sleep(1)
    curated_data = {
        'Title': [],
        'Abstract': [],
        'URL': [],
        'Subjects': [],
    }
    for idx, url in enumerate(urls):
        if idx % 4 == 0:
            time.sleep(1)
        content, status_code = get_content(url)
        if status_code == 200:
            title = find_title(content)
            abstract = find_abstract(content)
            subject = find_subject(content)
            curated_data['Title'].append(title)
            curated_data['Abstract'].append(abstract)
            curated_data['URL'].append(url)
            curated_data['Subjects'].append(subject)
    save_curated_data(curated_data, batch)


def extract_content_list_wise(arxiv_url, url):
    global _batch
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/list/' in str(x)]
    urls = [arxiv_url+x for x in urls]
    for url in urls:
        _batch += 1
        extract_arxiv_links(arxiv_url, url, _batch)


def extract_content_year_wise(arxiv_url, url):
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/year/' in str(x)]
    urls = [arxiv_url+x for x in urls]
    for url in urls:
        extract_content_list_wise(arxiv_url, url)


def start_web_scrape(config):
    url_list = extract_subjects(config['Arxiv_Website'])
    print(url_list)
    if len(url_list) != 0:
        for url in tqdm(url_list):
            extract_content_year_wise(config['Arxiv_Website'], url)
    pass
