from src.data.symptoms.digestive import DIGESTIVE_SYMPTOMS
from src.data.symptoms.general import GENERAL_SYMPTOMS
from src.data.symptoms.pain import PAIN_SYMPTOMS
from src.data.symptoms.respiratory import RESPIRATORY_SYMPTOMS
from src.data.symptoms.skin import SKIN_SYMPTOMS
from src.data.symptoms.urinary import URINARY_SYMPTOMS
from src.data.symptoms.metabolic import METABOLIC_SYMPTOMS
from src.data.symptoms.neurological import NEUROLOGICAL_SYMPTOMS
from src.data.symptoms.ocular_ear import OCULAR_EAR_SYMPTOMS


SYMPTOMS_DICTIONARY = {
  **RESPIRATORY_SYMPTOMS,
  **DIGESTIVE_SYMPTOMS,
  **SKIN_SYMPTOMS,
  **URINARY_SYMPTOMS,
  **GENERAL_SYMPTOMS,
  **PAIN_SYMPTOMS,
  **METABOLIC_SYMPTOMS,
  **NEUROLOGICAL_SYMPTOMS,
  **OCULAR_EAR_SYMPTOMS,
}
