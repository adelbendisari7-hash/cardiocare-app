import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('cardiocare.db')
cursor = conn.cursor()

try:
    # Tentative d'ajout de la colonne 'details'
    cursor.execute("ALTER TABLE diagnostic ADD COLUMN details TEXT")
    conn.commit()
    print("✅ Succès : La colonne 'details' a été ajoutée.")
except sqlite3.OperationalError as e:
    # Si l'erreur dit que la colonne existe déjà, tout va bien
    if "duplicate column name" in str(e):
        print("ℹ️ Info : La colonne 'details' existe déjà.")
    else:
        print(f"❌ Erreur SQL : {e}")

conn.close()
