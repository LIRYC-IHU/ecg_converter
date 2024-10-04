import xml.etree.ElementTree as ET
import sys
import re

def strip_namespace(element):
    for elem in element.iter():
        # Remove the namespace from the tag
        elem.tag = re.sub(r'\{.*\}', '', elem.tag)
    return element

def correct_xml(xml_filename: str):
    tree = ET.parse(xml_filename)
    root = tree.getroot()
    root = strip_namespace(root)

    # Replace "low" tags that make the converter bug with "center" tags
    for etime in root.findall("effectiveTime/low/.."):
        low_tag = etime.find('low')
        
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
    components = sequence_set.findall("component")
    first_component_found = None

    for component in components:
        code_tag = component.find("sequence/code")
        if code_tag is not None and code_tag.attrib.get('code') == "TIME_ABSOLUTE":
            if first_component_found is None:
                first_component_found = component
            else:
                # Remove this component if it's not the first one
                sequence_set.remove(component)
    
    # Save the modified XML file
    tree.write(xml_filename, encoding="utf-8", xml_declaration=True)

if __name__ == '__main__':
    correct_xml(sys.argv[1])