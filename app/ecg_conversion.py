import xml.etree.ElementTree as ET
import sys
import re
import subprocess
from typing import Optional

import logging

logger = logging.getLogger('uvicorn.error')

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


def strip_namespace(element):
    for elem in element.iter():
        # Remove the namespace from the tag
        elem.tag = re.sub(r'\{.*\}', '', elem.tag)
    return element


def correct_xml(input_filename: str, output_filename: str = None):
    """ Correct XML files before sending them to the converter """
    if not output_filename:
        output_filename = input_filename + '.corrected'
    
    tree = ET.parse(input_filename)
    root = tree.getroot()
    root = strip_namespace(root)

    # Replace "low" tags that make the converter bug with "center" tags
    for etime in root.findall("effectiveTime/low/.."):
        low_tag = etime.find('low')
        high_tag = etime.find('high')

        if low_tag is not None and high_tag is None:
            center_tag = ET.Element('center')
            # Copy attributes and text from 'low' if necessary
            center_tag.attrib = low_tag.attrib
            center_tag.text = low_tag.text
            # Replace 'low' with 'center'
            etime.remove(low_tag)
            etime.append(center_tag)

    # 2. Find components with path AnnotatedECG>component>series>component>sequenceSet>component 
    # and sequence>code with code attribute TIME_ABSOLUTE
    sequence_set = root.find("component/series/component/sequenceSet")
    if sequence_set is None:
        tree.write(output_filename, encoding="utf-8", xml_declaration=True)
        return
    
    components = sequence_set.findall("component")

    code_tags = []
    for component in components:
        code_tag = component.find("sequence/code")
        if code_tag is not None:
            l_code_tag = code_tag.attrib.get('code')
            if l_code_tag.startswith('TIME_') and ('TIME_ABSOLUTE' in code_tags or 'TIME_RELATIVE' in code_tags):
                logger.debug(f'Removing {l_code_tag} section.')
                sequence_set.remove(component)
                continue

            if l_code_tag not in code_tags:
                code_tags.append(l_code_tag)
            else:
                logger.debug(f'Removing {l_code_tag} section.')
                sequence_set.remove(component)

    # Save the modified XML file
    tree.write(output_filename, encoding="utf-8", xml_declaration=True)


def convert_file(filename: str, output_filename: Optional[str] = None, format: str = 'aECG'):
    """ Convert ECG file """
    if output_filename is None:
        output_filename = filename
        
    # Get & check requested output format
    if format not in EXTENSIONS:
        raise TypeError(f'Invalid conversion format - accepted values: {list(EXTENSIONS)}')

    # Check if xml file needs correction and apply
    try:
        correct_xml(filename, filename)
        logger.debug('Corrected XML file prior to conversion.')
    except ET.ParseError:
        pass

    # Convert the file, saving it to the out directory
    logger.debug(f'Converting file to {format}...')

    proc = subprocess.run(['mono', '/opt/ecg_toolkit/ECGTool.exe', filename, format, output_filename], stderr=subprocess.PIPE, text=True)

    if proc.stderr:
        if proc.stderr.startswith('Error: Not any of the supported ECG file types'):
            raise TypeError('ECG file is not supported/invalid')
        else:
            raise RuntimeError(proc.stderr)

if __name__ == '__main__':
    correct_xml(*sys.argv[1:])