import os

from airflow.sdk import task


def get_ticker_from_file_name(file_name):
    return file_name.split(".")[0]


def get_file_list(directory, extension):
    return [file for file in os.listdir(directory) if file.split(".")[-1] == extension]
