import sys
import logging

import click

from yield_data.load_data.warehouse import get_connection
from yield_data.load_data.operations import load_csv


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command
@click.option("--path", help="Path to a normalized YIELD_DATA CSV to load.")
@click.option("--db", default=None, help="DuckDB warehouse path (defaults to env / datalake).")
def run(path: str, db: str) -> None:
    logger.info(f"Starting yield load for {path}")
    con = get_connection(db)
    try:
        written = load_csv(con, path)
    finally:
        con.close()
    logger.info(f"Yield load complete: {written} rows written from {path}")


if __name__ == "__main__":
    run()
