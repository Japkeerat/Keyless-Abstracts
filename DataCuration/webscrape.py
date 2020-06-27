import logging
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.cli import tqdm

from util import create_folder

_batch = 0


def get_content(url):
    """
    Gets the content of the website parsed using html parser using Beautiful Soup.

    :param url: URL to be parsed for.
    :return: html code of the website and status code while accessing the website.
    """
    response = requests.get(url)
    status_code = int(response.status_code)
    if status_code != 200:
        logging.info("GET request for URL {} returned status code of {}".format(url, status_code))
        return None, status_code
    content = BeautifulSoup(response.text, 'html.parser')
    return content, status_code


def extract_subjects(url):
    """
    Finds all the hyperlinks associated to the subjects.

    :param url: Main url of the ARXIV website
    :return: List of urls related to subjects
    """
    content, status_code = get_content(url)
    if status_code != 200:
        return list()
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/archive/' in str(x)]
    urls = [url+x for x in urls]
    return urls


def find_title(content):
    """
    On the webpage of the paper, extracts the title of the paper
    """
    title = content.find_all('h1', attrs={'class': 'title'})[0]
    data = title.text.split('\n')[-1]
    return data


def find_abstract(content):
    """
    From the webpage of the paper, extracts the abstract of the paper
    """
    abstract = content.find_all('blockquote', attrs={'class': 'abstract'})[0]
    abstract = abstract.text.split('\nAbstract: ')[-1]
    return abstract


def find_subject(content):
    """
    From the webpage of the paper, extract the subject associated to the paper
    """
    subject = content.find_all('span', attrs={'class': 'primary-subject'})[0]
    subject = subject.text.split('\n')[-1]
    return subject


def save_curated_data(content: dict, batch: int):
    """
    Creates a CSV file for the content extracted from 25 papers.

    :param content: Data extracted from 25 paper
    :param batch: Batch ID.
    :return: None
    """
    df = pd.DataFrame(content)
    root_path = os.path.join(os.getcwd(), 'Curated_Data')
    create_folder(root_path)
    df.to_csv(os.path.join(root_path, 'curated_dataset_{}.csv'.format(batch)), index=False)


def start_curation(urls: list):
    """
    Curates data from the webpages from a given list of urls
    """
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
    return curated_data


def extract_arxiv_links(arxiv_url, url, batch):
    """
    Responsible for extracting arxiv links from the website
    """
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/abs/' in str(x)]
    urls = [arxiv_url+x for x in urls]
    time.sleep(1)
    curated_data = start_curation(urls)
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
    logging.info("Number of years found for {} is {}".format(url, len(urls)))
    urls = [arxiv_url+x for x in urls]
    for link in tqdm(urls, desc="Year for {}".format(url)):
        extract_content_list_wise(arxiv_url, link)
