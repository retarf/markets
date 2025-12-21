import os

from datetime import datetime

from constants import DATE_FORMAT, CSV


def get_ticker_from_file_name(file_name):
    return file_name.split(".")[0].split("_")[-1].upper()


def get_file_list(directory, extension):
    return [file for file in os.listdir(directory) if file.split(".")[-1] == extension]


def get_current_file_name(ticker):
    return f'{datetime.now().strftime(DATE_FORMAT)}_{ticker}.{CSV}'


def get_latest_file_list(file_list):
    sorted_file_list = sorted(file_list, key=lambda f: datetime.strptime(f.split('_')[0], DATE_FORMAT))
    return filter(lambda f: f.startswith(sorted_file_list[0].split('_')[0]), sorted_file_list)

