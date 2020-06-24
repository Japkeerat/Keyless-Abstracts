import logging
import os

import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup


def start_driver(driver_exe):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    path = os.path.join(os.getcwd(), 'Data', 'Driver', driver_exe)
    driver = webdriver.Edge(path)
    return driver


def visit_url(driver, url):
    driver.get(url)
    WebDriverWait(driver, timeout=10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'arxiv')))
    return driver


def fill_conditions(driver):
    """
    For a conditional search, execute click on checkboxes and relevant fields.
    :param driver:
    :return:
    """
    pass


def submit_form(driver):
    button = driver.find_elements_by_class_name('button')
    button[4].click()
    return driver


def save_info(titles, abstracts, batch):
    data = {
        'Title': titles,
        'Abstract': abstracts,
    }
    df = pd.DataFrame(data)
    path = os.path.join(os.getcwd(), 'results')
    if not os.path.exists(path):
        os.makedirs(path)
    file = os.path.join(path, 'output_df_{}.csv'.format(batch))
    df.to_csv(file, index=False)


def download_abstracts(driver, batch):
    content = BeautifulSoup(driver.page_source, 'html.parser')
    data = content.find_all('span', attrs={'class': 'abstract-full'})
    abstracts = [d.text for d in data]
    abstracts = [' '.join(abstract.split()[:-2]) for abstract in abstracts]
    data = content.find_all('p', attrs={'class': 'title'})
    titles = [d.text for d in data]
    titles = [title.strip() for title in titles]
    save_info(titles, abstracts, batch)


def next_page_exists(driver):
    content = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        data = content.find_all('a', attrs={'class': 'pagination-next'})
    except:
        logging.error('The end')
        return False
    if len(data) == 0:
        return False
    return True


def go_to_next_page(driver):
    button = driver.find_element_by_class_name('pagination-next')
    button.click()
    return driver


def start_webscrape(config):
    driver = start_driver(config['WebDriver'])
    driver = visit_url(driver, config['Arxiv_Website'])
    driver = submit_form(driver)
    page_number = 1
    download_abstracts(driver, page_number)
    while next_page_exists(driver):
        driver = go_to_next_page(driver)
        page_number += 1
        download_abstracts(driver, page_number)
    print(driver.current_url)
