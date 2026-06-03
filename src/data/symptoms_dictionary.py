from src.data.symptoms.digestive import DIGESTIVE_SYMPTOMS
from src.data.symptoms.general import GENERAL_SYMPTOMS
from src.data.symptoms.pain import PAIN_SYMPTOMS
from src.data.symptoms.respiratory import RESPIRATORY_SYMPTOMS
from src.data.symptoms.skin import SKIN_SYMPTOMS

SYMPTOMS_DICTIONARY = {
  **RESPIRATORY_SYMPTOMS,
  **DIGESTIVE_SYMPTOMS,
  **SKIN_SYMPTOMS,
  **GENERAL_SYMPTOMS,
  **PAIN_SYMPTOMS,
}
