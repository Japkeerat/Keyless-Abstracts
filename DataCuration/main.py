import logging
import os
import time

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


def start_webscrape(config):
    driver = start_driver(config['WebDriver'])
    driver = visit_url(driver, config['Arxiv_Website'])
    driver = submit_form(driver)

