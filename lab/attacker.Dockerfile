FROM python:3.10-slim

WORKDIR /lab

RUN pip install --no-cache-dir aiohttp

CMD ["tail", "-f", "/dev/null"]