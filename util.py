import os


def create_folder(path):
    """
    Creates a folder if not already present

    :param path:
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)
