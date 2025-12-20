FROM    apache/airflow:3.1.2rc1-python3.13 AS stage1
ENV     PYTHONBUFFERED 1
ENV     PYTHONDONTWRITEBYTECODE 1

USER    0:0
RUN     apt update && apt install -y pgcli vim
RUN     apt install -y openjdk-17-jdk

FROM stage1
USER    50000:0
WORKDIR /project
COPY    dockerfile/airflow/requirements.txt build/airflow/requirements.txt
RUN     pip install --upgrade pip
RUN     pip install -r build/airflow/requirements.txt

CMD     ["bash"]
