import hashlib
from sqlalchemy.orm import sessionmaker
try:
    from scripts.db_models import (
        init_db, Doctor, DoctorRate, InsuranceRate, Patient, PatientDoctorRate, Base
    )
except ImportError:
    from db_models import (
        init_db, Doctor, DoctorRate, InsuranceRate, Patient, PatientDoctorRate, Base
    )

def get_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

def generate_patient_id(name, email, phone):
    raw = f"{name.lower()}-{email.lower()}-{phone}"
    return hashlib.sha256(raw.encode()).hexdigest()[:10]

# --- Doctor functions ---
def add_doctor(name, rates):
    '''rates: list of dicts [{icd_code, disease, default_rate}]'''
    session = get_session()
    doctor = Doctor(name=name)
    session.add(doctor)
    session.flush()  # To get doctor.id
    for r in rates:
        dr_rate = DoctorRate(doctor_id=doctor.id, icd_code=r['icd_code'], disease=r['disease'], default_rate=r['default_rate'])
        session.add(dr_rate)
    session.commit()
    session.close()

def get_doctors():
    session = get_session()
    doctors = session.query(Doctor).all()
    result = []
    for d in doctors:
        rates = [ {'icd_code': r.icd_code, 'disease': r.disease, 'default_rate': r.default_rate} for r in d.rates ]
        result.append({'id': d.id, 'name': d.name, 'rates': rates})
    session.close()
    return result

# --- Insurance functions ---
def add_insurance_rate(provider, disease, icd_code, rate):
    session = get_session()
    ins = InsuranceRate(insurance_provider=provider, disease=disease, icd_code=icd_code, rate=rate)
    session.add(ins)
    session.commit()
    session.close()

def get_insurance_rates():
    session = get_session()
    rates = session.query(InsuranceRate).all()
    result = [ {'provider': r.insurance_provider, 'disease': r.disease, 'icd_code': r.icd_code, 'rate': r.rate} for r in rates ]
    session.close()
    return result

# --- Patient functions ---
def add_patient(name, email, phone, disease, icd_code, doctor_id, insurance_provider):
    session = get_session()
    patient_id = generate_patient_id(name, email, phone)
    # Ensure uniqueness
    existing = session.query(Patient).filter_by(id=patient_id).first()
    if existing:
        session.close()
        raise ValueError('Patient already exists!')
    patient = Patient(
        id=patient_id, name=name, email=email, phone=phone,
        disease=disease, icd_code=icd_code,
        assigned_doctor_id=doctor_id, insurance_provider=insurance_provider
    )
    session.add(patient)
    session.commit()
    session.close()
    return patient_id

def get_patients():
    session = get_session()
    patients = session.query(Patient).all()
    result = []
    for p in patients:
        result.append({
            'id': p.id, 'name': p.name, 'email': p.email, 'phone': p.phone,
            'disease': p.disease, 'icd_code': p.icd_code,
            'assigned_doctor_id': p.assigned_doctor_id,
            'insurance_provider': p.insurance_provider
        })
    session.close()
    return result

# --- Custom patient-doctor rates ---
def set_custom_rate(patient_id, doctor_id, icd_code, custom_rate):
    session = get_session()
    existing = session.query(PatientDoctorRate).filter_by(patient_id=patient_id, doctor_id=doctor_id, icd_code=icd_code).first()
    if existing:
        existing.custom_rate = custom_rate
    else:
        new_rate = PatientDoctorRate(patient_id=patient_id, doctor_id=doctor_id, icd_code=icd_code, custom_rate=custom_rate)
        session.add(new_rate)
    session.commit()
    session.close()

def get_custom_rate(patient_id, doctor_id, icd_code):
    session = get_session()
    rate = session.query(PatientDoctorRate).filter_by(patient_id=patient_id, doctor_id=doctor_id, icd_code=icd_code).first()
    session.close()
    if rate:
        return rate.custom_rate
    return None
