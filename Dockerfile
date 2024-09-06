FROM mono:latest
COPY ECGToolkit/ /opt/ecg_toolkit/
WORKDIR /opt/ecg_toolkit
ENTRYPOINT [ "mono", "ECGTool.exe" ]