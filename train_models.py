import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

def generate_and_train():
    print("1. Génération du dataset synthétique...")
    np.random.seed(42)
    n_samples = 2000
    
    # Simulation des données cliniques
    data = {
        'age': np.random.randint(30, 90, n_samples),
        'sexe': np.random.choice([1, 0], n_samples), # 1: Masculin, 0: Féminin
        'diabete': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'chest_pain': np.random.randint(0, 3, n_samples), # 0: Aucune, 1: Modérée, 2: Intense
        'breath_problems': np.random.randint(0, 3, n_samples),
        'cold_sweat': np.random.choice([0, 1], n_samples),
        'ecg': np.random.randint(0, 3, n_samples),
        'mri': np.random.choice([0, 1], n_samples),
        'pulse_rate': np.random.randint(50, 140, n_samples),
        'tcho': np.random.randint(120, 350, n_samples),
        'fbs': np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(data)

    # Logique cible (Vérité terrain)
    def get_target(row):
        score = 0
        if row['chest_pain'] == 2: score += 3
        if row['breath_problems'] == 2: score += 2
        if row['mri'] == 1: score += 2
        if row['tcho'] > 240: score += 1
        
        if score >= 5: return 2 # STEMI
        elif score >= 2: return 1 # NSTEMI
        else: return 0 # Normal

    df['target'] = df.apply(get_target, axis=1)
    
    X = df.drop('target', axis=1)
    y = df['target']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("2. Entraînement des modèles...")
    model_dl = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42)
    model_dl.fit(X_scaled, y)

    model_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    model_rf.fit(X_scaled, y)

    print("3. Sauvegarde...")
    joblib.dump(model_dl, 'model_dl.pkl')
    joblib.dump(model_rf, 'model_rf.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print("Terminé.")

if __name__ == "__main__":
    generate_and_train()
