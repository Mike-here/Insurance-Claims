import os
import pandas as pd
from docx import Document

# Helper to read a table from a docx file into a DataFrame
def docx_table_to_df(docx_path):
    doc = Document(docx_path)
    table = doc.tables[0]
    data = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def main():
    # Load all data
    doctor_df = docx_table_to_df(os.path.join('..', 'data', 'Doctor_Charges.docx'))
    insurance_df = docx_table_to_df(os.path.join('..', 'data', 'Medicaid_Insurance_Rates.docx'))
    patient_df = docx_table_to_df(os.path.join('..', 'data', 'Patient_Disease_Assignments.docx'))

    # Assign doctors to patients (alternating: A, B, A, B, A)
    doctors = ['A', 'B'] * 3
    patient_df['Assigned Doctor'] = [doctors[i] for i in range(len(patient_df))]

    # Merge patient with disease info
    merged = pd.merge(patient_df, doctor_df, left_on=['Disease', 'ICD Code'], right_on=['Disease Name', 'ICD Code'])
    merged = pd.merge(merged, insurance_df, on=['Disease Name', 'ICD Code'])

    # Calculate charges and patient responsibility
    def get_doctor_charge(row):
        return float(row['Doctor A Rate ($)']) if row['Assigned Doctor'] == 'A' else float(row['Doctor B Rate ($)'])
    merged['Doctor Charge'] = merged.apply(get_doctor_charge, axis=1)
    merged['Medicaid Rate'] = merged['Medicaid Rate ($)'].astype(float)
    merged['Patient Owes'] = merged['Doctor Charge'] - merged['Medicaid Rate']

    # Output summary
    summary_cols = [
        'Patient Name', 'Patient ID', 'Disease', 'ICD Code', 'Assigned Doctor',
        'Doctor Charge', 'Medicaid Rate', 'Patient Owes'
    ]
    summary = merged[summary_cols]
    print("\nBilling Summary:")
    print(summary.to_string(index=False))

    # Save to CSV
    summary.to_csv(os.path.join('..', 'data', 'billing_summary.csv'), index=False)
    print("\nSaved summary to data/billing_summary.csv")

if __name__ == '__main__':
    main()
