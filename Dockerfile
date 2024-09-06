FROM mono:latest
COPY ECGToolkit /opt/ecg_toolkit
COPY convert.sh /bin/convert
RUN chmod +x /bin/convert
RUN apt update && apt install -y python3 python3-pip && pip3 install flask gunicorn
COPY app.py /app/
WORKDIR /app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]