from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # Could be expanded with specialty, contact info, etc.
    rates = relationship('DoctorRate', back_populates='doctor')

class DoctorRate(Base):
    __tablename__ = 'doctor_rates'
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    icd_code = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    default_rate = Column(Float, nullable=False)
    doctor = relationship('Doctor', back_populates='rates')
    __table_args__ = (UniqueConstraint('doctor_id', 'icd_code', name='_doctor_icd_uc'),)

class InsuranceRate(Base):
    __tablename__ = 'insurance_rates'
    id = Column(Integer, primary_key=True)
    insurance_provider = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    icd_code = Column(String, nullable=False)
    rate = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint('insurance_provider', 'icd_code', name='_ins_icd_uc'),)

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(String, primary_key=True)  # hashed id
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    icd_code = Column(String, nullable=False)
    assigned_doctor_id = Column(Integer, ForeignKey('doctors.id'))
    insurance_provider = Column(String, nullable=False)
    assigned_doctor = relationship('Doctor')
    custom_rates = relationship('PatientDoctorRate', back_populates='patient')

class PatientDoctorRate(Base):
    __tablename__ = 'patient_doctor_rates'
    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.id'))
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    icd_code = Column(String, nullable=False)
    custom_rate = Column(Float, nullable=False)
    patient = relationship('Patient', back_populates='custom_rates')
    doctor = relationship('Doctor')
    __table_args__ = (UniqueConstraint('patient_id', 'doctor_id', 'icd_code', name='_pat_doc_icd_uc'),)

# Utility function to create the database

import os

def init_db(db_path=None):
    # Always create DB inside the project data/ directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    db_file = os.path.join(data_dir, 'billing.db')
    engine = create_engine(f'sqlite:///{db_file}')
    Base.metadata.create_all(engine)
    return engine

Session = sessionmaker()
