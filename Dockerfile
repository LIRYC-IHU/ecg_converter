FROM mono:latest
COPY ECGToolkit /opt/ecg_toolkit
COPY convert.sh /bin/convert
COPY requirements.txt /opt/requirements.txt
RUN chmod +x /bin/convert && apt update && apt install -y python3 python3-pip libpq-dev && pip3 install --no-cache-dir --upgrade -r /opt/requirements.txt
COPY ./app /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]