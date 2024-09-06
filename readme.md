# ECG converter
This package is an ECG conversion tool. It wraps the C# ECG-Toolkit in a docker container to provide cross-platform deployment.

ECG-Toolkit is an open source software. The webpage is [here](https://sourceforge.net/projects/ecgtoolkit-cs/).

## Deployment & use
First build the container using the following command:
```
docker build -t ecg_converter:latest .
```

You will need to mount a volume that contains the files you want to convert using the ECG conversion tools.
Here is an example:

```
docker run -v ./examples:/tmp ecg_converter:latest /tmp/Example.dcm PDF /tmp/output.pdf
```

This mounts the `./examples` folder to the `/tmp` directory on the container. The conversion then takes the `Example.dcm` file in this folder and converts it to PDF format, saving it to the `./examples` folder as `output.pdf`.

## Available options
Available options for `ECGTool.exe` can be obtained by running the container with the `--help` option:

```
docker run ecg_converter:latest --help
```


