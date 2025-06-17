from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
from io import BytesIO
from .utils import anonymize_pdf, anonymize_xml
from .ecg_conversion import EXTENSIONS, convert_file
import psycopg2
import os
import smbclient
import tempfile
from os import getenv

ROOT_PATH = os.getenv('ROOT_PATH', '')

app = FastAPI(title='ECG API', description='An API to get ECGs from the ACCELIS Workflow Manager server.', root_path=ROOT_PATH)

DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')
FILE_SERVER_URL = os.getenv('FILE_SERVER_URL')
FILE_SERVER_USER = os.getenv('FILE_SERVER_USER')
FILE_SERVER_PASSWORD = os.getenv('FILE_SERVER_PASSWORD')
smbclient.ClientConfig(username=FILE_SERVER_USER, password=FILE_SERVER_PASSWORD)

# Route 1: get the ECGs corresponding to a given patient ID
@app.get('/patient/{patient_id}', description='Get the list of ECGs matching a patient ID.')
async def get_patient_data(patient_id: str, limit: Optional[int]=None):
    conn = psycopg2.connect(DB_CONNECTION_STRING)
    try:
        cursor = conn.cursor()

        # Fetch the rows
        query = ("SELECT cpatientlastname, cpatientfirstname, cpatientsex, dpatientbirthdate, idxdossierid, dwtscreation, caccessionnumber "
                "FROM acworkflowmanager.titems "
                "WHERE cexamtype = 'ECG Standard' AND cdicomstudyuids != '' AND cpatientid = %s")
        if limit is None:
            query += ';'
            cursor.execute(query, (patient_id,))
        else:
            query += ' LIMIT %s;'
            cursor.execute(query, (patient_id, int(limit)))
        rows = cursor.fetchall()

    finally:
        conn.close()

    # Extract patient metadata and ecgs
    if not rows:
        raise HTTPException(404, 'Could not find any ECGs matching this patient ID')
    
    # Format the patient info
    patient_info = {
        'patient_id': str(patient_id),
        'last_name': rows[0][0],
        'first_name': rows[0][1],
        'sex': rows[0][2],
        'date_of_birth': rows[0][3]
        }
    
    # Format the ecg info
    ecg_files = {
        r[4]: {
            'timestamp': r[5],
            'venue_id': r[6]

        } for r in rows
    }
    patient_info['ecgs'] = ecg_files

    return(patient_info)


# Route 2 to get the ECGs
@app.get('/ecg/{ecg_id}', description='Get an ECG file matching a given id.')
async def get_ecg_file(ecg_id: str, format: str = 'xml', anonymize: bool = False):
    # Verify inputs
    filetypes = {
        'pdf': 'application/pdf',
        'xml': 'application/xml'
    }
    if format not in filetypes:
        raise HTTPException(400, f'Supported returned file formats are {[f for f in filetypes]}.')
    
    # Connect to the file server and find the matching file
    try:
        file_path = '\\'.join([FILE_SERVER_URL, ecg_id, 'AttachedFiles'])
        file_list = [f for f in smbclient.listdir(file_path) if f.endswith(format)]
    except FileNotFoundError:
        raise HTTPException(404, 'Could not find ECG file.')

    if not file_list:
        raise HTTPException(404, 'Could not find ECG file.')
    
    if len(file_list) > 1:
        raise HTTPException(409, 'Multiple files matching the request - aborting.')

    filename = '\\'.join([file_path, file_list[0]])
    out_filename = f'anonymized_{ecg_id}.{format}' if anonymize else f'{ecg_id}.{format}'
    response_headers = {'Content-disposition': f'attachment; filename="{out_filename}"'}

    stream = BytesIO()
    with smbclient.open_file(filename, 'rb') as f:
        stream.write(f.read())
    stream.seek(0)

    if anonymize:
        try:
            if format == 'xml':
                stream = anonymize_xml(stream)
            elif format == 'pdf':
                stream = anonymize_pdf(stream)
            else:
                raise TypeError
        except Exception as err:
            raise HTTPException(500, f'Error during anonymization process: {err}')

    return StreamingResponse(stream, media_type=filetypes[format], headers=response_headers)


def named_temp_file():
    with tempfile.NamedTemporaryFile() as tmpfile:
        yield tmpfile


# Route 3 to perform conversion of files if necessary
@app.post('/convert', description='Convert an ECG into a given format')
async def convert_ecg(file: UploadFile = File(...), format: str = 'aECG', target_file = Depends(named_temp_file)) -> FileResponse:
    """ Convert an input ECG into another format """
    base_filename = os.path.splitext(os.path.basename(file.filename))[0]
    download_filename = f'{base_filename}{EXTENSIONS[format]}'
    with tempfile.NamedTemporaryFile() as saved_file:
        while True:
            content = await file.read(1024)  # async read chunk
            if not content: 
                break
            saved_file.write(content)  # write chunk
        saved_file.seek(0)

        # Launch conversion
        try:
            convert_file(saved_file.name, target_file.name, format=format)
        except TypeError as e:
            raise HTTPException(400, str(e))
        except RuntimeError as e:
            raise HTTPException(500, str(e))

        # Stream the file as a response
        return FileResponse(target_file.name, filename=download_filename)
    

