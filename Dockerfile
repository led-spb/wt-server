FROM python:3.10-alpine

WORKDIR /app

RUN pip --no-cache-dir install gunicorn

COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY gunicorn.conf.py wt-server /app/

CMD ["gunicorn", "wt-server.app:create_app()"]
