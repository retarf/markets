from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task

from stock_data import DATA_DIR, DATE_FORMAT
from stock_data.push_data.operations import push_stock_data_operation


BASE_DIR = Path(DATA_DIR)


@dag(
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=True
)
def ingest_to_snowflake_dag():

    @task
    def get_latest_directory(ds: str) -> str | None:
        ds_date = datetime.strptime(ds, DATE_FORMAT).date()

        candidates: list[tuple] = []

        for path in BASE_DIR.iterdir():
            if not path.is_dir():
                continue
            if not path.name.startswith("dt="):
                continue

            try:
                dir_date = datetime.strptime(path.name.removeprefix("dt="), DATE_FORMAT).date()
                print("dir_date", dir_date)
            except ValueError:
                continue
            
            if dir_date < ds_date:
                candidates.append((dir_date, path))
    
        print(candidates)
        if not candidates:
            return None
        
        return str(max(candidates, key=lambda x: x[0])[1])
    
    @task
    def list_data_files(directory: str | None) -> list[str]:
        if directory is None:
            return []
        
        files  = [
            str(path)
            for path in Path(directory).iterdir()
            if path.is_file() and path.suffix == ".csv"
        ]
        print(files)
        return files
    
    @task
    def process_file(file_path: str) -> None:
        push_stock_data_operation(file_path)

    latest_dir = get_latest_directory()
    files = list_data_files(latest_dir)
    process_file.expand(file_path=files)


dag = ingest_to_snowflake_dag()
        