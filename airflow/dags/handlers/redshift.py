import logging
from handlers.aws import get_aws_session


SERVICE_NAME = 'redshift-data'
WORKGROUP_NAME = 'markets'
DATABASE_NAME = 'dev'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def execute(sql):
    session = get_aws_session()

    client = session.client(SERVICE_NAME)

    response = client.execute_statement(
        WorkgroupName=WORKGROUP_NAME,
        Database=DATABASE_NAME,
        Sql=sql
    )

    logger.info(response)

    # if response['HTTPStatusCode'] != 200:
    #     logger.error(f"Failed to execute query: {sql}")

    logger.info(f"Query has been executed: {sql}")
    stmt_id = response['Id']

    try:
        result = client.get_statement_result(Id=stmt_id)
    except client.exceptions.ResourceNotFoundException as e:
        result = e.response["Error"]["Message"]

    return result
