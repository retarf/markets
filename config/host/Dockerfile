FROM python:3.14

WORKDIR /project
COPY config/host/requirements.txt build/host/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r build/host/requirements.txt
RUN apt update && apt install -y pgcli vim

CMD ["bash"]
