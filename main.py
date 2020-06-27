import logging
import os

import yaml

from DataCuration.main import start_web_scrape
from util import create_folder


def load_config():
    """
    Loads the configuration file

    :return: Content of the configuration file
    """
    with open('config.yaml', 'r') as file:
        content = yaml.load(file, yaml.FullLoader)
    return content


def verify_configurations(conf: dict):
    """
    Verify the content loaded from configuration file is correct or not. It is checked in the
    beginning to prevent giving errors later in the code.

    :param conf: content of the configuration file
    :return: None
    """
    # TODO: Add checks for content of the configuration file.
    pass


def main():
    config = load_config()
    verify_configurations(config)
    start_web_scrape(config)


if __name__ == '__main__':
    create_folder(os.path.join(os.getcwd(), 'logs'))
    logging.basicConfig(filename='logs/DataCuration.log',
                        filemode='w',
                        level=logging.INFO,
                        format='%(filename)s: '
                               '%(levelname)s: '
                               '%(funcName)s(): '
                               '%(lineno)d:\t'
                               '%(message)s')

    main()
