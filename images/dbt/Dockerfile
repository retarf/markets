FROM    python:3.13
ENV     PYTHONBUFFERED 1
ENV     PYTHONDONTWRITEBYTECODE 1
WORKDIR /project
COPY    images/dbt/requirements.txt requirements.txt
RUN     pip install --upgrade pip
RUN     pip install -r requirements.txt

CMD     ["bash"]
