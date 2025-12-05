from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    prenom = db.Column(db.String(50))
    email = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    role = db.Column(db.String(10))  # patient, doctor, admin

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    prenom = db.Column(db.String(50))
    age = db.Column(db.Integer)
    history_diabetes = db.Column(db.Boolean)
    status_attack = db.Column(db.String(30))  # ex: "ST", "NSTEMI"
    hospitalisation_status = db.Column(db.Boolean)
    final_decision = db.Column(db.String(10))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    position = db.Column(db.String(50))

class Symptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    chest_pain = db.Column(db.Integer)
    breath_pbs = db.Column(db.Integer)

class RadioImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    mri = db.Column(db.Integer)
    ecg = db.Column(db.Integer)
    tcho = db.Column(db.Integer)  # taux cholestérol
