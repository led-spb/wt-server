FROM python:3.10-alpine

WORKDIR /app

RUN pip --no-cache-dir install gunicorn

COPY wt-server /app/wt-server
COPY gunicorn.conf.py requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["gunicorn", "wt-server.app:create_app()"]
