
CSV = "csv"
PARQUET = "parquet"
TICKER = "TICKER"
SOURCE_FILE = "SOURCE_FILE"

DATE_FORMAT = "%Y%m%d"
DATA_DIR = "/project/datalake"
UPLOADED_DATA_DIR = "/project/datalake/uploaded"


class RAW_COLUMN:
    DATE = "Data"
    OPEN = "Otwarcie"
    HIGH = "Najwyzszy"
    LOW = "Najnizszy"
    CLOSE = "Zamkniecie"
    VOLUME = "Wolumen"


class COLUMN:
    DATE = "TRADING_DATE"
    OPEN = "OPEN"
    HIGH = "HIGH"
    LOW = "LOW"
    CLOSE = "CLOSE"
    VOLUME = "VOLUME"


TICKER_LIST = ["xtb", "ORL"]