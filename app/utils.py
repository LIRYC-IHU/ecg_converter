from io import BytesIO
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter


def anonymize_xml(stream: BytesIO) -> BytesIO:
    bs4 = BeautifulSoup(stream, features='xml')
        
    patient_info = bs4.find('subjectAssignment')
    patient_info.decompose()

    output = BytesIO()
    output.write(bs4.prettify().encode('utf-8'))
    output.seek(0)

    return output

def anonymize_pdf(stream: BytesIO) -> BytesIO:
    pdf = PdfReader(stream)
    page = pdf.pages[0]
    del page['/Resources']['/XObject']
    
    writer = PdfWriter()
    writer.add_page(page)

    output = BytesIO()
    
    writer.write(output)
    output.seek(0)

    return output
