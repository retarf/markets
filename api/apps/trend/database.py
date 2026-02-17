import os
from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


with open('/api/.credentials/rsa_key.p8', "rb") as key:
    p_key= serialization.load_pem_private_key(
        key.read(),
        password=os.environ['SNOWFLAKE_PRIVATE_KEY_FILE_PWD'].encode(),
        backend=default_backend()
    )

pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption())


engine = create_engine(URL(
    account= os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    ),
    connect_args={
        'private_key': pkb,
        },
    )
# try:
#     connection = engine.connect()
#     results = connection.execute(text('select * from markets.dev.mart_trend_data limit 10')).fetchall()
#     for row in results:
#         print(row)
# finally:
#     connection.close()
#     engine.dispose()


# def get_session():
#     with Session(engine) as session:
#         yield session


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()