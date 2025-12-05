def rule_mi_diagnosis(patient, symptoms, radio_image):
    # RÈGLE 1 : Cas Critique (STEMI)
    if symptoms.chest_pain == 2 and (radio_image.ecg == 2 or radio_image.mri == 1):
        return {
            'attack_status': 'STEMI (CRITIQUE)',
            'hospitalisation': True,
            'decision': 'URGENCE CHIRURGICALE'
        }

    # RÈGLE 2 : Cas Modéré (NSTEMI)
    elif (symptoms.chest_pain >= 1 or symptoms.breath_problems >= 1) and (radio_image.tcho > 240 or patient.diabete):
        return {
            'attack_status': 'NSTEMI (Risque Élevé)',
            'hospitalisation': True,
            'decision': 'OBSERVATION INTENSIVE'
        }

    # RÈGLE 3 : Cas Normal
    else:
        return {
            'attack_status': 'Normal / Stable',
            'hospitalisation': False,
            'decision': 'RETOUR DOMICILE'
        }
