from src.services.nlp_service import nlp_service

def main():
  test_cases = [
    "Tengo fiebre y dolor de cabeza",
    "Me duele la garganta y tengo tos",
    "Estoy cansado y tengo dolor muscular",
    "Tengo dificultad para respirar y dolor en el pecho",
    "Tengo náuseas y vómitos",
    "Me duele el estómago y tengo diarrea",
    "Tengo pérdida de olfato y gusto",
    "Estoy congestionado y tengo secreción nasal",
    "Tengo dolor de garganta y fiebre",
    "Me duele la cabeza y tengo fatiga",
  ]

  for message in test_cases:
    symptoms = nlp_service.extract_symptoms(message)
    print(f"Mensaje: '{message}' -> Síntomas detectados: {symptoms}")

if __name__ == "__main__":
  main()