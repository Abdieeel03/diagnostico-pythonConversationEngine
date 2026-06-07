import re
import unicodedata

from rapidfuzz import fuzz
from src.data.symptoms_dictionary import SYMPTOMS_DICTIONARY

class NlpService:
  def __init__(self):
    self.symptoms_dictionary = SYMPTOMS_DICTIONARY

  def _normalize_text(self, text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")

  def _keyword_matches(self, keyword: str, message: str) -> bool:
    if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", message):
      return True

    if len(keyword) < 6:
      return False

    keyword_words = keyword.split()
    message_words = message.split()
    window_size = len(keyword_words)

    if window_size > len(message_words):
      return False

    for index in range(len(message_words) - window_size + 1):
      candidate = " ".join(message_words[index:index + window_size])
      if fuzz.ratio(keyword, candidate) >= 90:
        return True

    return False

  def extract_symptoms(self, message: str) -> list[str]:
    normalized_message = self._normalize_text(message)

    detected_symptoms = []

    for symptom, keywords in self.symptoms_dictionary.items():
            for keyword in keywords:
                keyword = self._normalize_text(keyword)

                if self._keyword_matches(keyword, normalized_message):
                  detected_symptoms.append(symptom)
                  break

    return detected_symptoms
  
  def _extract_symptoms_with_confidence(self, message: str) -> list[tuple[str, float]]:
    normalized_message = self._normalize_text(message)

    detected_symptoms = []

    for symptom, keywords in self.symptoms_dictionary.items():
      confidence = 0.0
      for keyword in keywords:
        keyword = self._normalize_text(keyword)
        if self._keyword_matches(keyword, normalized_message):
          confidence += 1.0 / len(keywords)
      
      if confidence > 0:
        detected_symptoms.append((symptom, confidence))

    return detected_symptoms
  
nlp_service = NlpService()
