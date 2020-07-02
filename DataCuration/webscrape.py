import logging
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.cli import tqdm

from util import create_folder


def verify_url(url):
    if url.count('//') == 1:
        return True
    return False


def get_content(url, retry=0):
    """
    Gets the content of the website parsed using html parser using Beautiful Soup.

    :param url: URL to be parsed for.
    :param retry: How many retries have happened
    :return: html code of the website and status code while accessing the website.
    """
    use = verify_url(url)
    logging.info("Requesting for {}".format(url))
    if use:
        try:
            response = requests.get(url)
            status_code = int(response.status_code)
            if status_code != 200:
                logging.info("GET request for URL {} returned status code of {}".format(url, status_code))
                if status_code == 403:
                    retry += 1
                    if retry <= 5:
                        logging.info("Retrying after 60 seconds")
                        time.sleep(60)
                        return get_content(url, retry=retry)
                    else:
                        raise TimeoutError("Waited for more than 5 minutes for server status to change, it didn't")
                return None, status_code
            content = BeautifulSoup(response.text, 'html.parser')
            return content, status_code
        except requests.exceptions.ConnectionError:
            logging.error("Connection failed for {}".format(url))
    return None, 404


def extract_subjects(url, subjects: dict):
    """
    Finds all the hyperlinks associated to the subjects.

    :param url: Main url of the ARXIV website
    :param subjects: dictionary of subjects for which url is needed where keys is subject name and value is list of years
    for which data needs to be extracted
    :return: List of urls related to subjects
    """
    content, status_code = get_content(url)
    if status_code != 200:
        return list()
    urls = content.find_all('a')
    if 'all' not in subjects.keys():
        urls = [x.get('href') for x in urls if str(x.text).lower() in subjects]
        if 'computing research repository' in subjects:
            idx = urls.index('/corr')
            urls[idx] = '/archive/cs'
    else:
        urls = [x.get('href') for x in urls if '/archive/' in str(x)]
        urls.append('/archive/cs')
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


def save_curated_data(content: dict, metadata: dict):
    """
    Creates a CSV file for the content extracted from 25 papers.

    :param content: Data extracted from 25 paper
    :param metadata: Other relevant information
    :return: None
    """
    df = pd.DataFrame(content)
    root_path = os.path.join(os.getcwd(), 'Curated_Data')
    create_folder(root_path)
    df.to_csv(os.path.join(root_path, '{}_{}_{}.csv'.format(metadata['Subject'], metadata['Month'], metadata['Year'])),
              index=False)


def start_curation(urls: list, skip_size: int):
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
        if idx < skip_size:
            continue
        if idx % 4 == 0:
            time.sleep(1)
        try:
            content, status_code = get_content(url)
        except TimeoutError:
            logging.error("Timed out waiting for server to respond")
            return curated_data
        if status_code == 200:
            title = find_title(content)
            abstract = find_abstract(content)
            subject = find_subject(content)
            curated_data['Title'].append(title)
            curated_data['Abstract'].append(abstract)
            curated_data['URL'].append(url)
            curated_data['Subjects'].append(subject)
    return curated_data


def extract_all_tag_link(arxiv_url, content):
    urls = content.find_all('a')
    url = [x.get('href') for x in urls if '?show=' in str(x)][0]
    url = arxiv_url + url
    return url


def extract_metadata(url):
    metadata = {
        "Subject": None,
        "Year": None,
        "Month": None,
    }
    content, status_code = get_content(url)
    if status_code != 200:
        return metadata
    subject_info_section = content.find_all("div", attrs={"id": "dlpage"})
    if len(subject_info_section) > 1:
        logging.exception("Something wrong with {}, found more than 1 headers for subject name".format(url))
    subject = subject_info_section[0].find('h1').text
    month_year_info = subject_info_section[0].find('h2').text
    info = month_year_info.split()
    year = info[-1]
    month = info[-2]
    metadata['Subject'] = subject
    metadata['Year'] = year
    metadata['Month'] = month
    return metadata


def already_processed(metadata, url):
    filename = os.path.join(os.path.join(os.getcwd(), 'Curated_Data'), "{}_{}_{}.csv".format(metadata['Subject'],
                                                                                             metadata['Month'],
                                                                                             metadata['Year']))
    if os.path.exists(filename):
        data = pd.read_csv(filename)
        size = len(data)
        total = int(url.split('=')[-1])
        if size != total:
            return False, size
        return True, 0
    return False, 0


def extract_arxiv_links(arxiv_url, url):
    """
    Responsible for extracting arxiv links from the website
    """
    content, status_code = get_content(url)
    if status_code != 200:
        return
    url = extract_all_tag_link(arxiv_url, content)
    metadata = extract_metadata(url)
    if 'pastweek' in url:
        raise AttributeError("Found wrong URL")
    processed, skip_size = already_processed(metadata, url)
    if not processed:
        content, status_code = get_content(url)
        if status_code != 200:
            return
        urls = content.find_all('a')
        urls = [x.get('href') for x in urls if '/abs/' in str(x)]
        urls = [arxiv_url+x for x in urls]
        time.sleep(1)
        curated_data = start_curation(urls, skip_size)
        save_curated_data(curated_data, metadata)


def extract_content_list_wise(arxiv_url, url):
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    urls = [x.get('href') for x in urls if '/list/' in str(x)]
    urls = [url for url in urls if 'recent' not in url]
    urls = [url for url in urls if '?' not in url]
    urls = [arxiv_url+x for x in urls]
    urls = list(set(urls))
    for url in tqdm(urls, "Years"):
        extract_arxiv_links(arxiv_url, url)


def extract_content_year_wise(arxiv_url, url, years):
    content, status_code = get_content(url)
    if status_code != 200:
        return
    urls = content.find_all('a')
    if years is None:
        urls = [x.get('href') for x in urls if '/year/' in str(x)]
    else:
        years = [str(x) for x in years]
        urls = [x.get('href') for x in urls if str(x.text) in years and '/year/' in str(x)]
    logging.info("Number of years found for {} is {}".format(url, len(urls)))
    urls = [arxiv_url+x for x in urls]
    for link in tqdm(urls, desc="Year for {}".format(url)):
        extract_content_list_wise(arxiv_url, link)

