# Shared image for the yields serving tier: the FastAPI query service, the API
# gateway, and the Temporal ingestion worker. All three share the same deps and
# the `src` (yield_data) + `services` code, so one image runs all of them; the
# compose `command` selects which process each container runs.
FROM    python:3.13-slim
ENV     PYTHONUNBUFFERED=1
ENV     PYTHONDONTWRITEBYTECODE=1
# `src` = yield_data package (config, events, activities); `services` = the apps.
ENV     PYTHONPATH=/project/src:/project
WORKDIR /project
COPY    images/services/requirements.txt requirements.txt
RUN     pip install --upgrade pip && pip install -r requirements.txt

CMD     ["bash"]
