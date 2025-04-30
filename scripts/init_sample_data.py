import sys
import os
import importlib.util

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)
sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location("db_utils", os.path.join(script_dir, "db_utils.py"))
db_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_utils)
add_doctor = db_utils.add_doctor
add_insurance_rate = db_utils.add_insurance_rate

doctors = [
    {
        'name': 'Doctor Kelvin Nkansa',
        'rates': [
            {'icd_code': 'H10.9', 'disease': 'CONJUNCTIVITIS', 'default_rate': 150},
            {'icd_code': 'H53.143', 'disease': 'C.L.A.R.E', 'default_rate': 170},
            {'icd_code': 'H04.123', 'disease': 'DRY EYE', 'default_rate': 200},
            {'icd_code': 'H00.14', 'disease': 'CHALAZION', 'default_rate': 210},
            {'icd_code': 'H01.009', 'disease': 'BLEPHARITIS', 'default_rate': 160}
        ]
    },
    {
        'name': 'Doctor Lord Gyasi',
        'rates': [
            {'icd_code': 'H10.9', 'disease': 'CONJUNCTIVITIS', 'default_rate': 155},
            {'icd_code': 'H53.143', 'disease': 'C.L.A.R.E', 'default_rate': 175},
            {'icd_code': 'H04.123', 'disease': 'DRY EYE', 'default_rate': 205},
            {'icd_code': 'H00.14', 'disease': 'CHALAZION', 'default_rate': 215},
            {'icd_code': 'H01.009', 'disease': 'BLEPHARITIS', 'default_rate': 165}
        ]
    }
]

insurances = [
    'Medicaid',
    'Medicare',
    'UHC',
    'Blue Cross Blue Shield'
]

rates = [
    {'icd_code': 'H10.9', 'disease': 'CONJUNCTIVITIS'},
    {'icd_code': 'H53.143', 'disease': 'C.L.A.R.E'},
    {'icd_code': 'H04.123', 'disease': 'DRY EYE'},
    {'icd_code': 'H00.14', 'disease': 'CHALAZION'},
    {'icd_code': 'H01.009', 'disease': 'BLEPHARITIS'}
]

# Add doctors and their rates
for doc in doctors:
    add_doctor(doc['name'], doc['rates'])

# Generate insurance rates for each insurance, disease
for ins in insurances:
    for r in rates:
        # Example: Medicaid covers 80% of Doctor Kelvin Nkansa's default rate for each disease
        # Medicare covers 75%, UHC 70%, Blue Cross Blue Shield 65%
        base = next((d for d in doctors if d['name'] == 'Doctor Kelvin Nkansa'), None)
        default = next((dr for dr in base['rates'] if dr['icd_code'] == r['icd_code']), None)
        rate_val = 0
        if ins == 'Medicaid':
            rate_val = default['default_rate'] * 0.8
        elif ins == 'Medicare':
            rate_val = default['default_rate'] * 0.75
        elif ins == 'UHC':
            rate_val = default['default_rate'] * 0.7
        elif ins == 'Blue Cross Blue Shield':
            rate_val = default['default_rate'] * 0.65
        add_insurance_rate(ins, r['disease'], r['icd_code'], round(rate_val, 2))
