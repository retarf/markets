import os

from datetime import datetime

from constants import DATE_FORMAT, CSV


def get_ticker_from_file_name(file_name):
    return file_name.split(".")[0].split("_")[-1].upper()


def get_file_list(directory, extension):
    return [file for file in os.listdir(directory) if file.split(".")[-1] == extension]


def get_current_file_name(ticker):
    return f'{datetime.now().strftime(DATE_FORMAT)}_{ticker}.{CSV}'
