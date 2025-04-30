import pdfplumber
import pandas as pd
import sqlite3
import os

import re

def extract_diagnosis_table(pdf_path):
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}...")
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            for line in lines:
                # Regex: code at start, then description, then owner, discontinued, modified, icd10 (all optional)
                match = re.match(r"^(\S+)\s+(.+?)\s+[A-Z]\s+([0-9/\-]*)\s*([0-9/\-]*)\s*[A-Z0-9]*$", line)
                if match:
                    code, desc, discontinued, _ = match.groups()[:4]
                    status = 'Active' if not discontinued else 'Discontinued'
                    data.append({
                        'Diagnosis Code': code.strip(),
                        'Diagnosis Name': desc.strip(),
                        'Status': status
                    })
    return pd.DataFrame(data)


def save_to_sqlite(df, db_path):
    conn = sqlite3.connect(db_path)
    df.to_sql('diagnosis_codes', conn, if_exists='replace', index=False)
    conn.close()

def save_to_excel(df, excel_path):
    df.to_excel(excel_path, index=False)

def search_cli(df):
    print("\nDiagnosis Table Search CLI")
    while True:
        query = input("\nEnter code/description/status to search (or 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            break
        mask = (
            df['Diagnosis Code'].str.contains(query, case=False, na=False) |
            df['Diagnosis Name'].str.contains(query, case=False, na=False) |
            df['Status'].str.contains(query, case=False, na=False)
        )
        results = df[mask]
        if results.empty:
            print("No results found.")
        else:
            print(results.to_string(index=False))

def main():
    pdf_path = 'diagnosistable.pdf'
    db_path = 'diagnosis_codes.db'
    excel_path = 'diagnosis_codes.xlsx'

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return

    df = extract_diagnosis_table(pdf_path)
    if df.empty:
        print("No diagnosis codes extracted.")
        return

    save_to_sqlite(df, db_path)
    save_to_excel(df, excel_path)
    print(f"Extracted {len(df)} diagnosis codes.")
    print(f"Saved to {db_path} and {excel_path}.")
    search_cli(df)

if __name__ == '__main__':
    main()
