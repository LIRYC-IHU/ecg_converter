# ECG converter
This package is an ECG conversion tool. It wraps the C# ECG-Toolkit in a docker container to provide cross-platform deployment.
ECG-Toolkit is an open source software. The webpage is [here](https://sourceforge.net/projects/ecgtoolkit-cs/).
The container can be used as a standalone app or deployed as a web server (default)

# Container build
Build container using the following command:
```
docker build -t ecg_converter:latest .
```

## Webserver deployment
The container can be used as a web-based conversion server. To deploy it, use the following:
```
docker run -p 80:80 ecg_converter:latest
```

The app has a single POST endpoint at it's root. The endpoint accepts two arguments: the `file` argument, which should be the file you want to convert, and the `format` argument, which is the destination format, one of [aECG, CSV, DICOM, DICOM-PDF, ISHNE, MUSE-XML, OmronECG, PDF, RAW, SCP-ECG]. The `format` argument is optional, and will default to aECG.

The app will convert the input file on the fly, and return as a file attachment the converted ECG.

Example call of the API:
```
curl -F "file=@./Example.dcm" http://localhost/
```
This converts the example dicom file to an FDA aECG xml format. Results are displayed in the console.

Example call of the API (2):
```
curl -F "file=@./Example.xml" -F format=PDF --output output.pdf http://localhost/
```
This converts the example aECG xml file to a PDF report, and saves the report to output.pdf

## Standalone App
You can override the default container command and access the conversion tool directly by calling the `convert` script (which is just a shortcut to `ECGTool.exe`).
You will need to mount a volume that contains the files you want to convert.
Here is an example:

```
docker run -v ./examples:/tmp ecg_converter:latest convert /tmp/Example.dcm PDF /tmp/output.pdf
```

This mounts the `./examples` folder to the `/tmp` directory on the container. The conversion then takes the `Example.dcm` file in this folder and converts it to PDF format, saving it to the `./examples` folder as `output.pdf`.

Available options can be obtained by running the container with the `--help` option:

```
docker run ecg_converter:latest convert --help
```


