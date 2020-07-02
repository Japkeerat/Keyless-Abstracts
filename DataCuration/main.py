import logging
import os

from tqdm.cli import tqdm

from DataCuration.webscrape import extract_subjects, extract_content_year_wise
from util import create_folder


def main(config):
    """
    Responsible for the whole webscrape of the ARXIV website.

    :param config:  YAML config file content
    :return: None
    """
    url_list = extract_subjects(config['Arxiv_Website'], config['Subjects'])
    logging.info("Number of subjects found is {}".format(len(url_list)))
    if len(url_list) != 0:
        if 'all' not in config['Subjects']:
            idx = 0
            keys = list(config['Subjects'].keys())
            for url in tqdm(url_list, desc="Subjects"):
                extract_content_year_wise(config['Arxiv_Website'], url, config['Subjects'][keys[idx]])
                logging.info("Done with {}".format(url))
        else:
            for url in tqdm(url_list, desc="Subjects"):
                extract_content_year_wise(config['Arxiv_Website'], url, None)
                logging.info("Done with {}".format(url))
    logging.info("Done")


if __name__ == "__main__":
    create_folder(os.path.join(os.getcwd(), 'logs'))
    logging.basicConfig(filename='logs/DataCuration.log',
                        filemode='w',
                        level=logging.INFO,
                        format='%(asctime)s: '
                               '%(filename)s: '
                               '%(levelname)s: '
                               '%(funcName)s(): '
                               '%(lineno)d:\t'
                               '%(message)s')
    conf = {
        "Arxiv_Website": "http://export.arxiv.org",
        "Subjects": {"all": ["all"]},
    }
    main(conf)
