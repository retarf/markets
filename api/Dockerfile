FROM    python:3.13 as stage1
ENV     PYTHONBUFFERED 1
ENV     PYTHONDONTWRITEBYTECODE 1

USER    0:0
RUN     apt update && apt install -y vim less

FROM stage1
#USER    50000:0
WORKDIR /api
COPY    api/requirements.txt api/requirements.txt
#RUN     pip install --upgrade pip
RUN     pip install -r api/requirements.txt

CMD     ["bash"]
