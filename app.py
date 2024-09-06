from flask import Flask, request, send_file
import os
import tempfile
import subprocess
import io

app = Flask(__name__)

EXTENSIONS = {
    'aECG': '.xml',
    'CSV': '.csv',
    'DICOM': '.dcm',
    'DICOM-PDF': '.dcm',
    'ISHNE': '.ecg',
    'MUSE-XML': '.xml',
    'OmronECG': '.ecg',
    'PDF': '.pdf',
    'RAW': '.bin',
    'SCP-ECG': '.scp'
}

@app.route('/', methods=['POST'])
def convert_file():
    """ Convert ECG file """
    # Get & check requested output format
    format = request.values.get('format', default = 'aECG', type = str)
    if format not in EXTENSIONS:
        return 'Bad request: invalid conversion format.\nShould be one of [aECG, CSV, DICOM, DICOM-PDF, ISHNE, MUSE-XML, OmronECG, PDF, RAW, SCP-ECG]\n', 400

    # Get file & convert
    try:
        file = request.files['file']
    except KeyError:
        return f'Please provide file to convert\n', 400

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save the file to a temp directory
        input_filename = os.path.join(tmpdir, file.filename)
        file.save(input_filename)

        # Convert file
        app.logger.debug(f'Converting file to {format}...')
        output_filename = os.path.splitext(input_filename)[0] + '_converted' + EXTENSIONS[format]
        download_filename = os.path.splitext(file.filename)[0] + EXTENSIONS[format]
        
        try:
            subprocess.run(['convert', input_filename, format, output_filename])
        except Exception as e:
            return f'Error converting file - {e}\n', 500
        
        # Read file to binary buffer (it will be deleted with the temp directory)
        with open(output_filename, 'rb') as f:
            contents = f.read()
    
    return send_file(
        io.BytesIO(contents),
        as_attachment=True,
        download_name=download_filename
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)