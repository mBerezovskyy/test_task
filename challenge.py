import re
import os
import csv
import json
import sys
import argparse

import xml.etree.ElementTree as ET


def parse_tsv_file(filename):
    def parse_organization(lines):
        organization_obj = {
                "organization": "",
                "street": "",
                "city": "",
                "state": "",
                "zip": ""
            }
        
        if lines['last']:
            organization_obj['organization'] = lines['last']
        if lines['organization'] != 'N/A':
            organization_obj['organization'] = lines['organization']

        organization_obj['street'] = lines['address']
        organization_obj['city'] = lines['city']
        organization_obj['state'] = lines['state']
        
        zipcode = ""

        if lines['zip']:
            zipcode += lines["zip"]
        if lines['zip4']:
            zipcode += "-" + lines["zip4"]

        organization_obj["zip"] = zipcode

        return organization_obj

    def parse_person(lines):
        person_obj = {
            "name": "",
            "street": "",
            "city": "",
            "county": "",
            "state": "",
            "zip": ""
        }


        first = lines['first'] + ' '
        middle = lines['middle'] + ' ' if lines['middle'] != 'N/M/N' else ''
        last = lines['last']

        full_name = f"{first}{middle}{last}".strip()

        person_obj['name'] = full_name
        person_obj['street'] = lines['address']
        person_obj['city'] = lines['city']
        person_obj['state'] = lines['state']
        person_obj['zip'] = lines['zip']
        
        return person_obj

    output_json = []

    with open(filename) as file:
        tsv_file = csv.DictReader(file, delimiter="\t")

        for lines in tsv_file:
            
            
            if not lines['first'] and not lines['middle']:
                organization_json = parse_organization(lines)
                output_json.append(organization_json)
            else:
                person_json = parse_person(lines)
                output_json.append(person_json)

    output_json = sorted(output_json, key=lambda x: x['zip'])

    return output_json

def parse_xml_file(filename):
    output_json = []

    tree = ET.parse(filename)
    root = tree.getroot()

    entities = root.find('ENTITY')

    for ent in entities.findall('ENT'):
        name = ent.find('NAME').text
        company = ent.find('COMPANY').text
        street = ent.find('STREET').text.strip() if ent.find('STREET').text else ''
        street2 = ent.find('STREET_2').text.strip() if ent.find('STREET_2').text else ''
        street3 = ent.find('STREET_3').text.strip() if ent.find('STREET_3').text else ''
        city = ent.find('CITY').text
        state = ent.find('STATE').text
        postal_code = ent.find('POSTAL_CODE').text

        streets = [s for s in [street, street2, street3] if s]
        

        if company != ' ':
            obj = {
                "organization": company,
                "street": ";". join(streets),
                "city": city,
                "state": state,
                "zip": postal_code
            }
        else:
            obj = {
                "name": name,
                "street": ";". join(streets),
                "city": city,
                "county": "",
                "state": state,
                "zip": postal_code
            }
        
        output_json.append(obj)

    output_json = sorted(output_json, key=lambda x: x['zip'])
    
    return output_json

def parse_txt_file(filename):

    output_json = []

    def process(info):
        
        person_obj = {
            "name": info[0],
            "street": info[1],
            "city": "",
            "county": "",
            "state": "",
            "zip": ""
        }

        if len(info) == 3:
            location = info[2].strip()
        else:
            location = info[3].strip()
            county = info[2].replace('COUNTY', '').strip()
            person_obj['county'] = county

        city = location.split(',')[0].strip()

        zipcode = re.findall(r'\b\d{5}(?:-\d{4})?\b', location)[0]

        state = location.replace(zipcode, '').split(',')[1].replace('-', '').strip()         

        person_obj['city'] = city
        person_obj['state'] = state
        person_obj['zip'] = zipcode

        return person_obj
    

    with open(filename) as f:
        lines = f.read()

        lines = lines.split('\n\n')

        for line in lines:
            info = line.split('\n')
            info = [i.strip() for i in info]
            if len(info) > 1:
                obj = process(info)
                output_json.append(obj)

    
    output_json = sorted(output_json, key=lambda x: x['zip'])

    return output_json

def validate_path(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Please specify valid paths, separated by spaces, e.g: --paths path1 path2 path3")
    return path

def main():
    parser = argparse.ArgumentParser(description="Process some paths.")
    parser.add_argument('--paths', type=validate_path, nargs='+', required=True, help="Enter paths separated by space. E.g. --paths input/file1 input/file2 input/file3")
    
    args = parser.parse_args()
    
    for full_path in args.paths:
        if full_path.endswith('.txt'):
            res = parse_txt_file(full_path)
            for i in res:
                print(json.dumps(i, indent=2))
        if full_path.endswith('.tsv'):
            res = parse_tsv_file(full_path)
            for i in res:
                print(json.dumps(i, indent=2))
        if full_path.endswith('.xml'):
            res = parse_xml_file(full_path)
            for i in res:
                print(json.dumps(i, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()













# for i in parse_tsv_file('input/input2.tsv'):
    # print(json.dumps(i, indent=2))

# for i in parse_xml_file('input/input1.xml'):
#     print(json.dumps(i, indent=2))

# for i in parse_txt_file('input/input3.txt'):
#     print(json.dumps(i, indent=2))
