import streamlit as st
import pandas as pd
import os
# import plotly.express as px

def main():
    try:
        from scripts import db_utils
    except ImportError:
        import db_utils
    st.set_page_config(page_title="Hospital Billing Dashboard", layout="wide")
    st.title("\U0001F3E5 Hospital Billing & Insurance Demo Dashboard")
    st.markdown("""
    This dashboard displays the billing summary for all patients, doctors, and insurance companies.\nYou can add new patients and visualize billing results (Doctor access only).
    """)

    # --- Load all data from the database ---
    doctors = db_utils.get_doctors() 
    patients = db_utils.get_patients()
    insurance_rates = db_utils.get_insurance_rates()

    # Convert to DataFrames for compatibility
    doctor_df = pd.DataFrame([
        {**{'id': d['id'], 'name': d['name']}, **{f"{r['icd_code']}|{r['disease']}": r['default_rate'] for r in d['rates']}}
        for d in doctors
    ]) if doctors else pd.DataFrame()
    patient_df = pd.DataFrame(patients) if patients else pd.DataFrame()
    insurance_df = pd.DataFrame(insurance_rates) if insurance_rates else pd.DataFrame()

    # --- Sidebar: Add New Patient Form ---
    st.sidebar.header("Simulate New Patient")
    with st.sidebar.form("add_patient_form"):
        new_patient_name = st.text_input("Patient Name")
        new_patient_email = st.text_input("Patient Email")
        new_patient_phone = st.text_input("Patient Phone")
        disease_options = doctor_df.columns[2:].tolist() if not doctor_df.empty else []
        disease_icd_pairs = [col.split('|') for col in disease_options]
        disease_list = [pair[1] for pair in disease_icd_pairs] if disease_icd_pairs else []
        new_disease = st.selectbox("Disease", disease_list) if disease_list else ''
        icd_code = disease_icd_pairs[disease_list.index(new_disease)][0] if new_disease and disease_list else ''
        doctor_options = doctor_df['name'].tolist() if not doctor_df.empty else []
        assigned_doctor = st.selectbox("Assigned Doctor", doctor_options) if doctor_options else ''
        insurance_options = insurance_df['provider'].unique().tolist() if not insurance_df.empty else []
        insurance_company = st.selectbox("Insurance Company", insurance_options) if insurance_options else ''
        custom_doctor_charge = st.number_input("Custom Doctor Charge (optional)", min_value=0.0, step=1.0, value=0.0)
        add_patient = st.form_submit_button("Add Patient")

    # Add new patient if form submitted
    if add_patient and new_patient_name and new_patient_email and new_patient_phone and new_disease and icd_code and assigned_doctor and insurance_company:
        # Find doctor_id
        doctor_id = doctor_df[doctor_df['name'] == assigned_doctor]['id'].iloc[0] if assigned_doctor in doctor_df['name'].values else None
        try:
            patient_id = db_utils.add_patient(new_patient_name, new_patient_email, new_patient_phone, new_disease, icd_code, doctor_id, insurance_company)
            # Set custom doctor charge if provided and > 0
            if custom_doctor_charge and custom_doctor_charge > 0:
                db_utils.set_custom_rate(patient_id, doctor_id, icd_code, custom_doctor_charge)
            st.sidebar.success(f"Added patient: {new_patient_name}")
        except Exception as e:
            st.sidebar.error(f"Error adding patient: {e}")
        # Reload patients
        patients = db_utils.get_patients()
        patient_df = pd.DataFrame(patients) if patients else pd.DataFrame()

    # --- Prepare Billing Summary ---
    # Build lookup dictionaries
    doctor_lookup = {d['id']: d for d in doctors}
    insurance_lookup = {(r['provider'], r['icd_code']): r['rate'] for r in insurance_rates}
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
            doctor_rates = doctor_lookup[doctor_id]['rates'] if doctor_id in doctor_lookup else []
            default_rate = next((r['default_rate'] for r in doctor_rates if r['icd_code'] == icd_code), None)
            doctor_charge = default_rate if default_rate is not None else 0.0
        insurance_rate = insurance_lookup.get((insurance_provider, icd_code), 0.0)
        patient_owes = doctor_charge - insurance_rate
        summary_rows.append({
            'Patient Name': patient_name,
            'Patient ID': patient_id,
            'Disease': disease,
            'ICD Code': icd_code,
            'Assigned Doctor': doctor_name,
            'Doctor Charge': doctor_charge,
            'Insurance Provider': insurance_provider,
            'Insurance Pays': insurance_rate,
            'Patient Pays': patient_owes
        })

    # --- Prepare Billing Summary ---
    billing_summary = pd.DataFrame(summary_rows)
    if not billing_summary.empty:
        billing_summary["Assigned Doctor"] = billing_summary["Assigned Doctor"].fillna("").astype(str)
        billing_summary["Patient Name"] = billing_summary["Patient Name"].fillna("").astype(str)
        billing_summary["Insurance Provider"] = billing_summary["Insurance Provider"].fillna("").astype(str)
    doctor_filter = st.sidebar.selectbox("Filter by Doctor", options=["All"] + sorted(billing_summary["Assigned Doctor"].unique()))
    patient_filter = st.sidebar.selectbox("Filter by Patient", options=["All"] + sorted(billing_summary["Patient Name"].unique()))
    insurance_filter = st.sidebar.selectbox("Filter by Insurance Provider", options=["All"] + sorted(billing_summary["Insurance Provider"].unique()))

    filtered_summary = billing_summary.copy()
    if doctor_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Assigned Doctor"] == doctor_filter]
    if patient_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Patient Name"] == patient_filter]
    if insurance_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Insurance Provider"] == insurance_filter]

    # --- Main Tables ---
    # Only show the personalized billing summary for the logged-in patient or by entered patient ID
    patient_id = st.session_state.get('patient_id', None)
    if not patient_id:
        patient_id = st.text_input("Enter your Patient ID to view your billing summary")
    if patient_id:
        patient_info = billing_summary[billing_summary['Patient ID'] == patient_id]
        st.subheader("Your Billing Summary Table")
        if not patient_info.empty:
            st.dataframe(patient_info, use_container_width=True)
        else:
            st.info("No billing information found for your ID.")

    st.subheader("Doctor Charges Table")
    st.dataframe(doctor_df, use_container_width=True)

    # --- Summary statistics (Everyone) ---
    st.markdown("---")
    st.subheader("Summary Statistics")
    
    if not filtered_summary.empty:
        # Convert currency strings back to numbers before summing
        def convert_currency(s):
            return float(s.replace('$', '').replace(',', '')) if isinstance(s, str) else s
        
        total_charges = filtered_summary["Doctor Charge"].apply(convert_currency).sum()
        total_covered = filtered_summary["Insurance Pays"].apply(convert_currency).sum()
        total_out_of_pocket = filtered_summary["Patient Pays"].apply(convert_currency).sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Charges", f"${total_charges:,.2f}")
        with col2:
            st.metric("Total Covered by Insurance", f"${total_covered:,.2f}")
        with col3:
            st.metric("Total Out-of-Pocket", f"${total_out_of_pocket:,.2f}")
    else:
        st.info("No data to display for the selected filters")

    # --- Pie chart: Distribution of Doctor Charges (Everyone) ---
    st.subheader("Doctor Charges Distribution (Pie Chart)")
    fig2 = px.pie(filtered_summary, names="Patient Name", values="Doctor Charge", title="Doctor Charges per Patient")
    st.plotly_chart(fig2, use_container_width=True)

    # --- Download CSV (Everyone) ---
    st.markdown("---")
    st.subheader("Download Billing Summary")
    csv = filtered_summary.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", csv, "billing_summary.csv", "text/csv")

    # Show insurance rates and patient lookup to all users (no authentication implemented)
    st.header("Insurance Company Rates")
    insurance_providers = insurance_df['provider'].unique().tolist() if not insurance_df.empty else []
    if insurance_providers:
        selected_insurance = st.selectbox(
            "Select Insurance Company to View Rates",
            insurance_providers
        )
        if selected_insurance:
            rates_df = insurance_df[insurance_df['provider'] == selected_insurance][['disease', 'icd_code', 'rate']]
            rates_df = rates_df.rename(columns={
                'disease': 'Disease Name',
                'icd_code': 'ICD Code',
                'rate': f'{selected_insurance} Rate'
            })
            st.subheader(f"{selected_insurance} Insurance Rates")
            st.dataframe(rates_df)

    st.header("All Patients in Database")
    if not patient_df.empty:
        # Add assigned doctor name to the DataFrame for display
        doctor_id_to_name = {d['id']: d['name'] for d in doctors}
        patient_df['Assigned Doctor'] = patient_df['assigned_doctor_id'].map(doctor_id_to_name)
        display_cols = [
            col for col in ["id", "name", "disease", "icd_code", "Assigned Doctor", "insurance_provider", "email", "phone"]
            if col in patient_df.columns
        ]
        col_rename = {
            "id": "Patient ID",
            "name": "Patient Name",
            "disease": "Disease",
            "icd_code": "ICD Code",
            "Assigned Doctor": "Assigned Doctor",
            "insurance_provider": "Insurance Provider",
            "email": "Email",
            "phone": "Phone"
        }
        st.dataframe(patient_df[display_cols].rename(columns=col_rename), use_container_width=True)
    else:
        st.info("No patients found in the database.")

    # --- Doctor Custom Charge Input ---
    st.header("Doctor: Set Custom Charge for Patient's Disease")
    if not patient_df.empty and not doctor_df.empty:
        with st.form("set_custom_charge_form"):
            patient_choices = patient_df[["id", "name", "disease", "icd_code", "assigned_doctor_id"]].copy()
            patient_choices["desc"] = patient_choices.apply(lambda row: f"{row['name']} (ID: {row['id']}, Disease: {row['disease']}, ICD: {row['icd_code']})", axis=1)
            selected_patient = st.selectbox("Select Patient", patient_choices["desc"].tolist())
            # Extract patient info
            selected_row = patient_choices[patient_choices["desc"] == selected_patient].iloc[0]
            patient_id = selected_row["id"]
            doctor_id = selected_row["assigned_doctor_id"]
            icd_code = selected_row["icd_code"]
            disease = selected_row["disease"]
            custom_amount = st.number_input(f"Enter Custom Charge for {disease} (ICD: {icd_code})", min_value=0.0, step=1.0)
            submit_custom = st.form_submit_button("Set Custom Charge")
        if submit_custom:
            try:
                db_utils.set_custom_rate(patient_id, doctor_id, icd_code, custom_amount)
                st.success(f"Custom charge of ${custom_amount:,.2f} set for patient {selected_row['name']} (Disease: {disease})")
                # Reload patients and billing summary to reflect the change
                patients = db_utils.get_patients()
                patient_df = pd.DataFrame(patients) if patients else pd.DataFrame()
                # Also reload summary rows
                doctors = db_utils.get_doctors()
                insurance_rates = db_utils.get_insurance_rates()
                doctor_lookup = {d['id']: d for d in doctors}
                insurance_lookup = {(r['provider'], r['icd_code']): r['rate'] for r in insurance_rates}
                summary_rows = []
                for p in patients:
                    pid = p['id']
                    did = p['assigned_doctor_id']
                    icd = p['icd_code']
                    dis = p['disease']
                    ins = p['insurance_provider']
                    pname = p['name']
                    dname = doctor_lookup[did]['name'] if did in doctor_lookup else 'Unknown'
                    custom_rate = db_utils.get_custom_rate(pid, did, icd)
                    if custom_rate is not None:
                        doctor_charge = custom_rate
                    else:
                        doctor_rates = doctor_lookup[did]['rates'] if did in doctor_lookup else []
                        default_rate = next((r['default_rate'] for r in doctor_rates if r['icd_code'] == icd), None)
                        doctor_charge = default_rate if default_rate is not None else 0.0
                    insurance_rate = insurance_lookup.get((ins, icd), 0.0)
                    patient_owes = doctor_charge - insurance_rate
                    summary_rows.append({
                        'Patient Name': pname,
                        'Patient ID': pid,
                        'Disease': dis,
                        'ICD Code': icd,
                        'Assigned Doctor': dname,
                        'Doctor Charge': doctor_charge,
                        'Insurance Provider': ins,
                        'Insurance Pays': insurance_rate,
                        'Patient Pays': patient_owes
                    })
                billing_summary = pd.DataFrame(summary_rows)
            except Exception as e:
                st.error(f"Error setting custom charge: {e}")

if __name__ == "__main__":
    main()
