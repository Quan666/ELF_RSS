FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

RUN python3 -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

COPY . /app/

RUN python3 -m pip install -r requirements.txt

CMD nb run
