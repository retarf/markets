WITH raw_stock_data AS (SELECT * FROM MARKETS.RAW.RAW_STOCK_DATA)
    SELECT
        TICKER,
        DATE,
        OPEN,
        HIGH,
        LOW,
        CLOSE,
        VOLUME,
        SOURCE_FILE,
        LOAD_TS
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY TICKER, DATE ORDER BY LOAD_TS DESC) AS LATEST_FLAG FROM raw_stock_data
    ) AS all_stock_data
    WHERE LATEST_FLAG = 1

