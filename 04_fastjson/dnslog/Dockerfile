FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN python -m pip install --no-cache-dir dnslib flask

COPY dnslog.py /app/dnslog.py

EXPOSE 53/udp 80/tcp

CMD ["python", "dnslog.py"]
