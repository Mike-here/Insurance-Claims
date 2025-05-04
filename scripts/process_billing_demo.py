import os
import pandas as pd
try:
    from scripts import db_utils
except ImportError:
    import db_utils

def main():
    # Load data from the database
    patients = db_utils.get_patients()
    doctors = db_utils.get_doctors()
    insurance_rates = db_utils.get_insurance_rates()

    # Build lookup dictionaries for quick access
    doctor_lookup = {d['id']: d for d in doctors}
    insurance_lookup = {}
    for rate in insurance_rates:
        key = (rate['provider'], rate['icd_code'])
        insurance_lookup[key] = rate['rate']

    summary_rows = []
    for p in patients:
        patient_id = p['id']
        doctor_id = p['assigned_doctor_id']
        icd_code = p['icd_code']
        disease = p['disease']
        insurance_provider = p['insurance_provider']
        patient_name = p['name']
        doctor_name = doctor_lookup[doctor_id]['name'] if doctor_id in doctor_lookup else 'Unknown'

        # Check for custom rate
        custom_rate = db_utils.get_custom_rate(patient_id, doctor_id, icd_code)
        if custom_rate is not None:
            doctor_charge = custom_rate
        else:
            # Find default rate for this doctor and ICD code
            doctor_rates = doctor_lookup[doctor_id]['rates'] if doctor_id in doctor_lookup else []
            default_rate = next((r['default_rate'] for r in doctor_rates if r['icd_code'] == icd_code), None)
            doctor_charge = default_rate if default_rate is not None else 0.0

        # Find insurance rate
        insurance_rate = insurance_lookup.get((insurance_provider, icd_code), 0.0)
        patient_owes = doctor_charge - insurance_rate
        summary_rows.append({
            'Patient Name': patient_name,
            'Patient ID': patient_id,
            'Disease': disease,
            'ICD Code': icd_code,
            'Assigned Doctor': doctor_name,
            'Doctor Charge': doctor_charge,
            f'{insurance_provider} Rate': insurance_rate,
            'Patient Owes': patient_owes
        })

    summary = pd.DataFrame(summary_rows)
    print("\nBilling Summary:")
    print(summary.to_string(index=False))

    # Save to CSV
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    summary.to_csv(os.path.join(data_dir, 'billing_summary.csv'), index=False)
    print("\nSaved summary to data/billing_summary.csv")

if __name__ == '__main__':
    main()
