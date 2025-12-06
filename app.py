from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import traceback
import os
import requests  # pour appeler les web services externes

app = Flask(__name__)

# Utilisation d'un chemin absolu pour la base SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cardiocare_v3.db')
app.secret_key = 'SECRET_KEY_CARDIO_APP'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

# =========================
# URLs DES WEB SERVICES (Render)
# =========================
RULES_SERVICE_URL = "https://rules-service.onrender.com/diagnose_rules"
ML_SERVICE_URL    = "https://ml-service-17mx.onrender.com/diagnose_ml"

# =========================
# MODÈLES BDD
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    age = db.Column(db.Integer)
    sexe = db.Column(db.String(10))
    diabete = db.Column(db.Boolean, default=False)
    problemes_pulmonaires = db.Column(db.Boolean, default=False)


class Symptom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    chest_pain = db.Column(db.Integer)
    breath_problems = db.Column(db.Integer)
    cold_sweat = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RadioImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    ecg = db.Column(db.Integer)
    mri = db.Column(db.Integer)
    pulse_rate = db.Column(db.Integer)
    tcho = db.Column(db.Float)
    fbs = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Diagnostic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date = db.Column(db.String(50))
    result = db.Column(db.String(50))
    decision = db.Column(db.String(200))
    details = db.Column(db.Text, nullable=True)


def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="admin@hospital.com").first():
            pw = generate_password_hash("admin123", method='pbkdf2:sha256')
            db.session.add(User(
                nom="Admin", prenom="Sys",
                email="admin@hospital.com",
                password=pw, role="admin"
            ))
        if not User.query.filter_by(email="medecin@hospital.com").first():
            pw = generate_password_hash("medecin123", method='pbkdf2:sha256')
            db.session.add(User(
                nom="House", prenom="Gregory",
                email="medecin@hospital.com",
                password=pw, role="medecin"
            ))
        db.session.commit()

# =========================
# ROUTES DE BASE
# =========================
@app.route('/')
def index():
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/current_user')
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'user': None})
    u = User.query.get(session['user_id'])
    if not u:
        return jsonify({'user': None})
    return jsonify({
        'user': {
            'id': u.id,
            'nom': u.nom,
            'prenom': u.prenom,
            'email': u.email,
            'role': u.role
        }
    })


@app.route('/login_api', methods=['POST'])
def login():
    data = request.json
    u = User.query.filter_by(email=data.get('email')).first()
    if u and check_password_hash(u.password, data.get('password')):
        session['user_id'] = u.id
        session['user_role'] = u.role
        return jsonify({'message': 'OK', 'role': u.role})
    return jsonify({'error': 'Identifiants invalides'}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =========================
# ADMIN
# =========================
@app.route('/api/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([
        {
            'id': u.id,
            'nom': u.nom,
            'prenom': u.prenom,
            'email': u.email,
            'role': u.role
        } for u in users
    ])


@app.route('/users', methods=['POST'])
def create_user():
    d = request.json
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email pris'}), 400
    if not d.get('nom') or not d.get('password'):
        return jsonify({'error': 'Champs manquants'}), 400

    u = User(
        nom=d['nom'],
        prenom=d['prenom'],
        email=d['email'],
        password=generate_password_hash(d['password'], method='pbkdf2:sha256'),
        role=d['role']
    )
    db.session.add(u)
    db.session.commit()
    return jsonify({'message': 'Créé'})


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    u = User.query.get(id)
    if not u:
        return jsonify({'error': 'Utilisateur introuvable'}), 404
    db.session.delete(u)
    db.session.commit()
    return jsonify({'message': 'Supprimé'})


@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    u = User.query.get(id)
    if not u:
        return jsonify({'error': 'Utilisateur introuvable'}), 404
    d = request.json
    u.nom = d['nom']
    u.prenom = d['prenom']
    u.email = d['email']
    u.role = d['role']
    if d.get('password'):
        u.password = generate_password_hash(d['password'], method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'message': 'Modifié'})

# =========================
# MEDECIN & PATIENTS
# =========================
@app.route('/api/patients_list')
def list_patients():
    res = []
    for p in Patient.query.all():
        u = User.query.get(p.user_id) if p.user_id else None
        has_sym = Symptom.query.filter_by(patient_id=p.id).first() is not None
        has_exam = RadioImage.query.filter_by(patient_id=p.id).first() is not None
        has_record = has_sym and has_exam
        res.append({
            'id': p.id,
            'nom': p.nom,
            'prenom': p.prenom,
            'age': p.age,
            'email': u.email if u else 'Non lié',
            'has_record': has_record
        })
    return jsonify(res)


@app.route('/api/users_without_record')
def users_without_record():
    patients_users = []
    for u in User.query.filter_by(role='patient').all():
        if not Patient.query.filter_by(user_id=u.id).first():
            patients_users.append({
                'id': u.id,
                'nom': u.nom,
                'prenom': u.prenom
            })
    return jsonify(patients_users)


@app.route('/api/patients', methods=['POST'])
def create_patient_api():
    d = request.json
    if not d.get('nom') or not d.get('prenom'):
        return jsonify({'error': 'Nom et Prénom requis'}), 400
    try:
        age = int(d.get('age'))
        if age < 0 or age > 120:
            return jsonify({'error': 'Âge invalide (0-120)'}), 400
    except Exception:
        return jsonify({'error': 'Âge invalide'}), 400

    p = Patient(
        user_id=d.get('user_id'),
        nom=d['nom'],
        prenom=d['prenom'],
        age=age,
        sexe=d['sexe'],
        diabete=d.get('diabete', False),
        problemes_pulmonaires=False
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'message': 'OK'})


@app.route('/api/symptoms', methods=['POST'])
def add_symptom():
    d = request.json
    s = Symptom(
        patient_id=d['patient_id'],
        chest_pain=int(d['chest_pain']),
        breath_problems=int(d['breath_problems']),
        cold_sweat=bool(d['cold_sweat'])
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'message': 'OK'})


@app.route('/api/exams', methods=['POST'])
def add_exam():
    d = request.json
    try:
        tcho = float(d['tcho'])
        pulse = int(d['pulse_rate'])
        if tcho < 50 or tcho > 600:
            return jsonify({'error': 'Cholestérol hors limites (50-600)'}), 400
        if pulse < 30 or pulse > 250:
            return jsonify({'error': 'Pouls hors limites (30-250)'}), 400
    except Exception:
        return jsonify({'error': 'Valeurs numériques invalides'}), 400

    exam = RadioImage(
        patient_id=d['patient_id'],
        ecg=int(d['ecg']),
        mri=int(d['mri']),
        pulse_rate=pulse,
        tcho=tcho,
        fbs=False
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify({'message': 'OK'})

# NOUVELLE ROUTE : récupérer le dernier dossier pour pré-remplir / consulter
@app.route('/api/patient_record/<int:pid>')
def get_patient_record(pid):
    p = Patient.query.get(pid)
    if not p:
        return jsonify({'error': 'Patient introuvable'}), 404

    s = Symptom.query.filter_by(patient_id=pid).order_by(Symptom.id.desc()).first()
    r = RadioImage.query.filter_by(patient_id=pid).order_by(RadioImage.id.desc()).first()

    return jsonify({
        'patient': {
            'id': p.id,
            'nom': p.nom,
            'prenom': p.prenom,
            'age': p.age,
            'sexe': p.sexe,
            'diabete': bool(p.diabete)
        },
        'symptoms': None if not s else {
            'chest_pain': s.chest_pain,
            'breath_problems': s.breath_problems,
            'cold_sweat': bool(s.cold_sweat)
        },
        'exams': None if not r else {
            'ecg': r.ecg,
            'mri': r.mri,
            'pulse_rate': r.pulse_rate,
            'tcho': r.tcho
        }
    })

# =========================
# DIAGNOSTIC VIA WEB SERVICES (RÈGLES ou IA)
# =========================
@app.route('/api/diagnose/<int:pid>', methods=['POST'])
def diagnose(pid):
    try:
        method = request.json.get('method', 'rules')  # 'rules' | 'deep_learning' | 'random_forest'

        p = Patient.query.get(pid)
        s = Symptom.query.filter_by(patient_id=pid).order_by(Symptom.id.desc()).first()
        r = RadioImage.query.filter_by(patient_id=pid).order_by(RadioImage.id.desc()).first()

        if not p or not s or not r:
            return jsonify({'error': 'Données manquantes'}), 400

        payload = {
            "patient": {
                "age": p.age,
                "sexe": p.sexe,
                "diabete": bool(p.diabete)
            },
            "symptoms": {
                "chest_pain": s.chest_pain,
                "breath_problems": s.breath_problems,
                "cold_sweat": bool(s.cold_sweat)
            },
            "exams": {
                "ecg": r.ecg,
                "mri": r.mri,
                "pulse_rate": r.pulse_rate,
                "tcho": r.tcho,
                "fbs": 0
            }
        }

        if method == 'rules':
            resp = requests.post(RULES_SERVICE_URL, json=payload, timeout=8)
        else:
            payload["model_type"] = 'deep_learning' if method == 'deep_learning' else 'random_forest'
            resp = requests.post(ML_SERVICE_URL, json=payload, timeout=15)

        if not resp.ok:
            return jsonify({'error': f'Service externe indisponible ({resp.status_code})'}), 502

        result = resp.json()

        if 'explanation' in result:
            details_text = ", ".join(result.get('explanation', []))
        else:
            details_text = 'Règles expertes'

        diag = Diagnostic(
            patient_id=pid,
            doctor_id=session.get('user_id'),
            date=datetime.now().strftime("%d/%m/%Y %H:%M"),
            result=result['attack_status'],
            decision=result['decision'],
            details=details_text
        )
        db.session.add(diag)
        db.session.commit()

        return jsonify({'message': 'Diagnostic OK', 'result': result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# =========================
# PATIENT : MON ESPACE
# =========================
@app.route('/api/my_info')
def my_info():
    if 'user_id' not in session:
        return jsonify({'error': 'Non connecté'}), 403
    p = Patient.query.filter_by(user_id=session['user_id']).first()
    if not p:
        return jsonify({'found': False})
    diags = Diagnostic.query.filter_by(patient_id=p.id).order_by(Diagnostic.id.desc()).all()
    return jsonify({
        'found': True,
        'nom': p.nom,
        'prenom': p.prenom,
        'age': p.age,
        'sexe': p.sexe,
        'diabete': p.diabete,
        'historique': [
            {
                'date': d.date,
                'result': d.result,
                'decision': d.decision,
                'details': d.details
            } for d in diags
        ]
    })


if __name__ == '__main__':
    if not os.path.exists(os.path.join(basedir, 'cardiocare_v3.db')):
        print("Initialisation DB...")
        init_db()
    app.run(debug=True)
