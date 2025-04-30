import streamlit as st
import pandas as pd
import os
from data_loader import load_default_data, prepare_billing_summary
import plotly.express as px
import tempfile

# --- Doctor Codes Mapping ---
DOCTOR_CODES = {
    "Doctor Kelvin": "kelvin2024",
    "Doctor Alan": "alan2024"
}

def main():
    st.set_page_config(page_title="Hospital Billing Dashboard", layout="wide")
    st.title("🏥 Hospital Billing & Insurance Demo Dashboard")
    st.markdown("""
    This dashboard displays the billing summary for all patients, doctors, and insurance companies.\nYou can upload new data, add new patients, and visualize billing results (Doctor access only).
    """)

    # --- Sidebar: Data Uploaders ---
    st.sidebar.header("Upload Data Files (.docx or .csv)")
    docx_types = [".docx", ".csv"]
    doctor_file = st.sidebar.file_uploader("Doctor Charges", type=["docx", "csv"])
    insurance_file = st.sidebar.file_uploader("Insurance Rates", type=["docx", "csv"])
    patient_file = st.sidebar.file_uploader("Patient Assignments", type=["docx", "csv"])

    # --- Load Data ---
    from data_loader import docx_table_to_df, csv_to_df
    def load_df(uploaded_file, default_path):
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                return csv_to_df(uploaded_file)
            else:
                return docx_table_to_df(uploaded_file)
        else:
            return docx_table_to_df(default_path) if default_path.endswith(".docx") else csv_to_df(default_path)
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    doctor_df = load_df(doctor_file, os.path.join(data_dir, 'Doctor_Charges.docx'))
    insurance_df = load_df(insurance_file, os.path.join(data_dir, 'Medicaid_Insurance_Rates.docx'))
    patient_df = load_df(patient_file, os.path.join(data_dir, 'Patient_Disease_Assignments.docx'))

    # --- Sidebar: Add New Patient Form ---
    st.sidebar.header("Simulate New Patient")
    with st.sidebar.form("add_patient_form"):
        new_patient_name = st.text_input("Patient Name")
        new_patient_id = st.text_input("Patient ID")
        disease_options = doctor_df['Disease Name'].unique().tolist()
        new_disease = st.selectbox("Disease", disease_options)
        icd_code = doctor_df[doctor_df['Disease Name'] == new_disease]['ICD Code'].iloc[0]
        doctor_options = ['Doctor Kelvin Nkansa', 'Doctor Lord Gyasi']
        assigned_doctor = st.selectbox("Assigned Doctor", doctor_options)
        # Insurance companies from insurance_df
        insurance_options = insurance_df['Insurance Company'].unique().tolist() if 'Insurance Company' in insurance_df.columns else ['Medicaid']
        insurance_company = st.selectbox("Insurance Company", insurance_options)
        add_patient = st.form_submit_button("Add Patient")

    # Add new patient if form submitted
    if add_patient and new_patient_name and new_patient_id:
        new_row = {
            'Patient Name': new_patient_name,
            'Patient ID': new_patient_id,
            'Disease': new_disease,
            'ICD Code': icd_code,
            'Assigned Doctor': assigned_doctor,
            'Insurance Company': insurance_company
        }
        patient_df = pd.concat([patient_df, pd.DataFrame([new_row])], ignore_index=True)
        st.sidebar.success(f"Added patient: {new_patient_name}")

    # --- Prepare Billing Summary ---
    summary = prepare_billing_summary(doctor_df, insurance_df, patient_df)

    # --- Sidebar: Filters (Everyone) ---
    st.sidebar.header("Filters")
    billing_summary["Doctor"] = billing_summary["Doctor"].fillna("").astype(str)
    billing_summary["Patient Name"] = billing_summary["Patient Name"].fillna("").astype(str)
    billing_summary["Insurance Company"] = billing_summary["Insurance Company"].fillna("").astype(str)
    doctor_filter = st.sidebar.selectbox("Filter by Doctor", options=["All"] + sorted(billing_summary["Doctor"].unique()))
    patient_filter = st.sidebar.selectbox("Filter by Patient", options=["All"] + sorted(billing_summary["Patient Name"].unique()))
    insurance_filter = st.sidebar.selectbox("Filter by Insurance Company", options=["All"] + sorted(billing_summary["Insurance Company"].unique()))

    filtered_summary = billing_summary.copy()
    if doctor_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Doctor"] == doctor_filter]
    if patient_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Patient Name"] == patient_filter]
    if insurance_filter != "All":
        filtered_summary = filtered_summary[filtered_summary["Insurance Company"] == insurance_filter]

    # --- Main Tables ---
    st.subheader("Billing Summary Table")
    
    # Get all patients (both default and session state)
    all_patients = patient_df.copy()
    if 'patient_data' in st.session_state:
        all_patients = pd.concat([all_patients, st.session_state['patient_data']], ignore_index=True)
    
    # Prepare billing summary with all patients
    billing_summary = prepare_billing_summary(doctor_df, insurance_rates, all_patients)
    
    # Remove the Insurance Coverage column before displaying
    columns_to_show = [col for col in billing_summary.columns if col != 'Insurance Coverage']
    st.dataframe(billing_summary[columns_to_show], use_container_width=True)

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

    if is_doctor:
        # Create a dropdown to select which insurance company's rates to view
        selected_insurance = st.selectbox(
            "Select Insurance Company to View Rates",
            list(insurance_rates.keys())
        )
        
        if selected_insurance:
            # Create a DataFrame from the rates dictionary
            rates_df = pd.DataFrame({
                'Disease Name': list(insurance_rates[selected_insurance].keys()),
                f'{selected_insurance} Rate': list(insurance_rates[selected_insurance].values())
            })
            
            # Display the selected insurance company's rates
            st.subheader(f"{selected_insurance} Insurance Rates")
            st.dataframe(rates_df)
            
        # Add a section to show patient-specific information
        st.header("Patient Information")
        patient_id = st.text_input("Enter Patient ID to View Details")
        if patient_id:
            patient_info = billing_summary[billing_summary['Patient ID'] == patient_id]
            if not patient_info.empty:
                st.subheader(f"Patient Details for ID: {patient_id}")
                st.dataframe(patient_info)
            else:
                st.warning("Patient ID not found.")
    else:
        # Patient view - show only their own information
        st.header("Your Medical Bill")
        
        # Filter to show only this patient's information
        patient_info = billing_summary[billing_summary['Patient ID'] == login_user]
        
        if not patient_info.empty:
            st.dataframe(patient_info)
            
            # Convert currency strings back to numbers before summing
            def convert_currency(s):
                return float(s.replace('$', '').replace(',', '')) if isinstance(s, str) else s
            
            # Show total amounts
            total_doctor_charge = patient_info['Doctor Charge'].apply(convert_currency).sum()
            total_insurance_pays = patient_info['Insurance Pays'].apply(convert_currency).sum()
            total_patient_pays = patient_info['Patient Pays'].apply(convert_currency).sum()
            
            st.markdown("---")
            st.subheader("Summary")
            st.write(f"Total Doctor Charge: ${total_doctor_charge:,.2f}")
            st.write(f"Total Insurance Coverage: ${total_insurance_pays:,.2f}")
            st.write(f"Total Amount You Owe: ${total_patient_pays:,.2f}")
        else:
            st.info("No billing information found for your ID.")

if __name__ == "__main__":
    main()
