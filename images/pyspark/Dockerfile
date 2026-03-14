FROM    python:3.13 as stage1
ENV     PYTHONBUFFERED 1
ENV     PYTHONDONTWRITEBYTECODE 1
RUN     apt update && apt install -y vim less
RUN     apt install -y openjdk-21-jdk
WORKDIR /project
COPY    images/pyspark/requirements.txt requirements.txt
RUN     pip install --upgrade pip
RUN     pip install -r requirements.txt

CMD     ["bash"]
