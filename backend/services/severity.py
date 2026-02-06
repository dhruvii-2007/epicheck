def calculate_severity(symptoms: list, ai_confidence: float):
    score = len(symptoms) * 0.2 + ai_confidence

    if score >= 1.2:
        return score, "high", "Consult a dermatologist immediately"
    elif score >= 0.7:
        return score, "medium", "Monitor and seek medical advice"
    else:
        return score, "low", "Self care recommended"
