import pdfplumber
import pandas as pd
import re
import os
import json

def extract_eob_data(pdf_path):
    data = []
    patient_name = None
    patient_id = None
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for i, line in enumerate(lines):
                # Search Patient by name
                if not patient_name:
                    m = re.search(r'Patient:\s*([\w\-, ]+)', line)
                    if m:
                        patient_name = m.group(1).strip()
                # Search Patient by ID
                if not patient_id:
                    m = re.search(r'Insured ID #:\s*(\w+)', line)
                    if m:
                        patient_id = m.group(1).strip()
                # CPT code line
                m = re.match(r'([A-Z0-9,]+)\s+(\d+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+([A-Z0-9]+)', line)
                if m:
                    cpt = m.group(1)
                    units = m.group(2)
                    billed = m.group(3)
                    allowed = m.group(4)
                    paid = m.group(6)
                    patient_resp = m.group(5)
                    denial_code = m.group(10)
                    # Next line is service date (optional)
                    service_date = ''
                    if i+1 < len(lines):
                        date_match = re.match(r'(\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})', lines[i+1])
                        if date_match:
                            service_date = date_match.group(0)
                    data.append({
                        'Patient Name': patient_name,
                        'Patient ID': patient_id,
                        'CPT Code': cpt,
                        'Units': units,
                        'Service Date': service_date,
                        'Amount Billed': billed,
                        'Amount Paid': paid,
                        'Patient Responsibility': patient_resp,
                        'Denial Code': denial_code
                    })
    return pd.DataFrame(data)

def save_to_csv_and_json(df, base_filename):
    csv_path = base_filename + '.csv'
    json_path = base_filename + '.json'
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient='records', indent=2)
    print(f"Saved CSV to {csv_path}")
    print(f"Saved JSON to {json_path}")

def main():
    pdf_path = 'uhc eob.pdf'
    base_filename = 'uhc_eob_data'
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    df = extract_eob_data(pdf_path)
    if df.empty:
        print("No EOB data extracted.")
        return
    print(f"Extracted {len(df)} EOB line items.")
    save_to_csv_and_json(df, base_filename)

if __name__ == '__main__':
    main()
