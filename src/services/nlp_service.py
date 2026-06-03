from rapidfuzz import fuzz
from src.data.symptoms_dictionary import SYMPTOMS_DICTIONARY

class NlpService:
  def __init__(self):
    self.symptoms_dictionary = SYMPTOMS_DICTIONARY

  def extract_symptoms(self, message: str) -> list[str]:
    normalized_message = message.lower()

    detected_symptoms = []

    for symptom, keywords in self.symptoms_dictionary.items():
            for keyword in keywords:
                keyword = keyword.lower()

                if keyword in normalized_message:
                    detected_symptoms.append(symptom)
                    break

                if len(keyword) >= 6:
                    similarity = fuzz.partial_ratio(
                        keyword,
                        normalized_message,
                    )

                    if similarity >= 90:
                        detected_symptoms.append(symptom)
                        break

    return detected_symptoms
  
  def _extract_symptoms_with_confidence(self, message: str) -> list[tuple[str, float]]:
    normalized_message = message.lower()

    detected_symptoms = []

    for symptom, keywords in self.symptoms_dictionary.items():
      confidence = 0.0
      for keyword in keywords:
        similarity = fuzz.partial_ratio(keyword, normalized_message)
        if similarity >= 80:
          confidence += 1.0 / len(keywords)
      
      if confidence > 0:
        detected_symptoms.append((symptom, confidence))

    return detected_symptoms
  
nlp_service = NlpService()