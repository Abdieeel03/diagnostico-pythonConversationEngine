from rapidfuzz import fuzz

class NlpService:
  def __init__(self):
    self.symptoms_dictionary = {
      "fiebre": [
        "fiebre",
        "temperatura alta",
        "alta temperatura",
        "temperatura",
        "calentura",
        "me siento caliente",
      ],
      "tos": [
        "tos",
        "toser",
        "tose",
        "tos seca",
        "estoy tosiendo",
      ],
      "dolor_cabeza": [
        "dolor de cabeza",
        "dolor cabeza",
        "me duele la cabeza",
        "me duele cabeza",
        "cabeza me duele",
        "cefalea",
        "migraña",
      ],
      "congestion_nasal": [
        "congestión nasal",
        "nariz tapada",
        "nariz congestionada",
        "me cuesta respirar por la nariz",
        "no puedo respirar por la nariz",
        "mocos",
        "secreción nasal",
        "secrecion nasal",
      ],
      "dolor_garganta": [
        "dolor de garganta",
        "garganta me duele",
        "me duele la garganta",
        "dolor garganta",
        "garganta dolorida",
        "garganta irritada",
        "ardor de garganta",
      ],
      "cansancio": [
        "cansancio",
        "fatiga",
        "me siento cansado",
        "me siento fatigado",
        "estoy cansado",
        "estoy fatigado",
        "me siento debil",
        "debilidad",
        "agotamiento",
        "cansado",
      ],
      "perdida_olfato": [
        "pérdida de olfato",
        "perdida de olfato",
        "no puedo oler",
        "olfato perdido",
        "olfato no funciona",
        "no siento olores",
        "no huelo",
      ],
      "perdida_gusto": [
        "pérdida de gusto",
        "perdida de gusto",
        "no puedo saborear",
        "gusto perdido",
        "gusto no funciona",
        "no siento sabores",
        "no saboreo",
        "no tengo gusto",
      ],
    }

  def extract_symptoms(self, message: str) -> list[str]:
    normalized_message = message.lower()

    detected_symptoms = []

    for symptom, keywords in self.symptoms_dictionary.items():
      for keyword in keywords:
        similarity = fuzz.partial_ratio(
          keyword,
          normalized_message,
        )

        if similarity >= 80:
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