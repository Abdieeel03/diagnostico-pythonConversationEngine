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
      "puntos_negros": [
        "puntos negros",
        "espinillas",
        "comedones abiertos",
        "puntos en la nariz",
      ],
      "puntos_blancos": [
        "puntos blancos",
        "milium",
        "comedones cerrados",
        "granitos blancos",
      ],
      "papulas": [
        "pápulas",
        "bultos rojos",
        "granitos sin pus",
        "protuberancias rojas",
      ],
      "pustulas": [
        "pústulas",
        "granitos con pus",
        "espinillas con pus",
        "granos infectados",
      ],
      "nodulos": [
        "nódulos",
        "bultos profundos",
        "bultos dolorosos",
        "nódulos en la piel",
      ],
      "quistes": [
        "quistes",
        "quistes sebáceos",
        "bultos grandes",
        "quiste bajo la piel",
      ],
      "inflamacion": [
        "inflamación",
        "hinchazón",
        "zona inflamada",
        "hinchado",
        "edema",
      ],
      "enrojecimiento": [
        "enrojecimiento",
        "piel roja",
        "rojez",
        "eritema",
        "colorado",
      ],
      "prurito": [
        "prurito",
        "picazón",
        "picor",
        "me pica",
        "rascarse",
      ],
      "piel_seca": [
        "piel seca",
        "sequedad",
        "piel deshidratada",
        "piel áspera",
        "xerosis",
      ],
      "manchas_rojas": [
        "manchas rojas",
        "parches rojos",
        "máculas rojas",
        "manchas coloradas",
      ],
      "exudado": [
        "exudado",
        "líquido",
        "supuración",
        "sale líquido",
        "mojado",
      ],
      "costras": [
        "costras",
        "escamas secas",
        "cascaritas",
        "costra",
      ],
      "piel_engrosada": [
        "piel engrosada",
        "piel dura",
        "liquenificación",
        "piel gruesa",
      ],
      "erupcion_localizada": [
        "erupción localizada",
        "sarpullido en una zona",
        "brote localizado",
        "erupción en un lugar",
      ],
      "picazon": [
        "picazón",
        "comezón",
        "picor",
        "rasquera",
        "me pica mucho",
      ],
      "quemazon": [
        "quemazón",
        "ardor",
        "me quema",
        "sensación de calor",
        "escozor",
      ],
      "ampollas": [
        "ampollas",
        "vesículas",
        "flictenas",
        "bolitas de agua",
      ],
      "hinchazon": [
        "hinchazón",
        "edema",
        "inflamado",
        "hinchado",
        "aumento de volumen",
      ],
      "piel_agrietada": [
        "piel agrietada",
        "grietas en la piel",
        "fisuras",
        "piel rota",
      ],
      "habones": [
        "habones",
        "ronchas",
        "urticaria",
        "bultos elevados",
      ],
      "ronchas": [
        "ronchas",
        "habones",
        "marcas rojas",
        "alergia en la piel",
      ],
      "picazon_severa": [
        "picazón severa",
        "picor intenso",
        "no aguanto la picazón",
        "picazón insoportable",
      ],
      "angioedema": [
        "angioedema",
        "hinchazón de labios",
        "hinchazón de ojos",
        "inflamación profunda",
      ],
      "placas_rojas": [
        "placas rojas",
        "manchas grandes rojas",
        "parches colorados",
        "placas en la piel",
      ],
      "escamas_plateadas": [
        "escamas plateadas",
        "escamas blancas",
        "piel que se descama",
        "placas escamosas",
      ],
      "picor": [
        "picor",
        "picazón",
        "comezón",
        "me pica",
      ],
      "dolor_articular": [
        "dolor articular",
        "dolor en las articulaciones",
        "dolor de coyunturas",
        "me duelen los huesos",
        "artralgia",
      ],
      "perdida_apetito": [
        "pérdida de apetito",
        "no tengo hambre",
        "falta de ganas de comer",
        "anorexia",
        "desganado",
      ],
      "hormigueo": [
        "hormigueo",
        "parestesia",
        "cosquilleo",
        "entumecimiento",
        "me hormiguea",
      ],
      "ampollas_labios": [
        "ampollas en los labios",
        "fuego en la boca",
        "herpes labial",
        "pupas en el labio",
      ],
      "dolor_quemante": [
        "dolor quemante",
        "ardor fuerte",
        "dolor que quema",
        "quemazón intensa",
      ],
      "sarpullido_rojo": [
        "sarpullido rojo",
        "erupción roja",
        "brote rojo",
        "piel con puntitos rojos",
      ],
      "erupcion_anillo": [
        "erupción en forma de anillo",
        "mancha circular",
        "anillo rojo",
        "erupción redonda",
      ],
      "bordes_elevados": [
        "bordes elevados",
        "bordes resaltados",
        "orilla hinchada",
        "borde con relieve",
      ],
      "descamacion": [
        "descamación",
        "se me cae la piel",
        "pellejitos",
        "despellejamiento",
      ],
      "perdida_cabello": [
        "pérdida de cabello",
        "se me cae el pelo",
        "alopecia",
        "calvicie",
        "caída de cabello",
      ],
      "llagas_rojas": [
        "llagas rojas",
        "heridas abiertas",
        "úlceras en la piel",
        "llagas que no curan",
      ],
      "costras_miel": [
        "costras melicéricas",
        "costras de color miel",
        "costras amarillentas",
        "heridas con costra miel",
      ],
      "fiebre_alta": [
        "fiebre alta",
        "mucha fiebre",
        "temperatura muy alta",
        "fiebre fuerte",
      ],
      "dolor_muscular": [
        "dolor muscular",
        "mialgia",
        "me duelen los músculos",
        "dolor de cuerpo",
      ],
      "dolor_retroocular": [
        "dolor retroocular",
        "dolor detrás de los ojos",
        "me duelen los ojos por dentro",
        "presión tras los ojos",
      ],
      "nauseas": [
        "náuseas",
        "ganas de vomitar",
        "asco",
        "mareos con náuseas",
      ],
      "vomitos": [
        "vómitos",
        "devolver",
        "vomitar",
        "lanzar",
      ],
      "fiebre_leve": [
        "fiebre leve",
        "febrícula",
        "un poco de fiebre",
        "temperatura algo alta",
      ],
      "conjuntivitis": [
        "conjuntivitis",
        "ojos llorosos",
        "ojos inflamados",
        "lagañas",
        "irritación ocular",
      ],
      "erupcion_pruriginosa": [
        "erupción pruriginosa",
        "sarpullido que pica",
        "brote con picazón",
        "erupción con picor",
      ],
      "edema": [
        "edema",
        "hinchazón por líquido",
        "retención de líquidos",
        "inflamación blanda",
      ],
      "fiebre_muy_alta": [
        "fiebre muy alta",
        "fiebre extrema",
        "hipertermia",
        "fiebre de 40 grados",
      ],
      "dolor_articular_intenso": [
        "dolor articular intenso",
        "dolor fuerte en articulaciones",
        "no puedo mover las articulaciones",
        "artralgia severa",
      ],
      "inflamacion_articulaciones": [
        "inflamación de articulaciones",
        "coyunturas hinchadas",
        "artritis",
        "articulaciones inflamadas",
      ],
      "fatiga_extrema": [
        "fatiga extrema",
        "agotamiento total",
        "no tengo fuerzas",
        "cansancio extremo",
      ],
      "ganglios_inflamados": [
        "ganglios inflamados",
        "bolitas en el cuello",
        "adenopatía",
        "ganglios hinchados",
      ],
      "esplenomegalia": [
        "esplenomegalia",
        "bazo inflamado",
        "dolor en el lado izquierdo",
        "bazo agrandado",
      ],
      "tos_persistente": [
        "tos persistente",
        "tos que no se quita",
        "tos crónica",
        "tengo tos hace mucho",
      ],
      "tos_sangre": [
        "tos con sangre",
        "hemoptisis",
        "escupir sangre al toser",
        "sangre en la flema",
      ],
      "dolor_pecho": [
        "dolor de pecho",
        "dolor torácico",
        "presión en el pecho",
        "me duele al respirar",
      ],
      "perdida_peso": [
        "pérdida de peso",
        "adelgazar sin motivo",
        "he bajado de peso",
        "estoy más flaco",
      ],
      "sudoraciones_nocturnas": [
        "sudoraciones nocturnas",
        "sudar mucho de noche",
        "me despierto empapado",
        "diaforesis nocturna",
      ],
      "ictericia": [
        "ictericia",
        "piel amarilla",
        "ojos amarillos",
        "color amarillento",
      ],
      "orina_oscura": [
        "orina oscura",
        "coluria",
        "orina color café",
        "orina muy cargada",
      ],
      "heces_claras": [
        "heces claras",
        "acolia",
        "popo blanco",
        "heces pálidas",
      ],
      "dolor_abdominal": [
        "dolor abdominal",
        "dolor de panza",
        "dolor de estómago",
        "retortijones",
      ],
      "fiebre_baja": [
        "fiebre baja",
        "febrícula",
        "calentura leve",
        "poca fiebre",
      ],
      "debilidad": [
        "debilidad",
        "flojera",
        "falta de fuerza",
        "me siento débil",
      ],
      "coriza": [
        "coriza",
        "mucha secreción nasal",
        "goteo nasal constante",
        "rinitis",
      ],
      "tos_seca": [
        "tos seca",
        "tos sin flema",
        "tos irritativa",
        "tengo tos seca",
      ],
      "manchas_koplik": [
        "manchas de koplik",
        "puntos blancos en la boca",
        "manchas rojas con centro blanco en la boca",
      ],
      "exantema": [
        "exantema",
        "erupción en la piel",
        "brote cutáneo",
        "manchas en el cuerpo",
      ],
      "inflamacion_ganglios": [
        "inflamación de ganglios",
        "ganglios linfáticos hinchados",
        "adenopatías",
      ],
      "sarpullido_rosado": [
        "sarpullido rosado",
        "manchas rosadas",
        "erupción tenue",
        "piel rosada",
      ],
      "ojos_rojos": [
        "ojos rojos",
        "ojos inyectados en sangre",
        "hiperemia conjuntival",
        "enrojecimiento ocular",
      ],
      "inflamacion_parotidas": [
        "inflamación de parótidas",
        "paperas",
        "hinchazón debajo de las orejas",
        "glándulas salivales inflamadas",
      ],
      "dolor_masticar": [
        "dolor al masticar",
        "me duele al comer",
        "mandíbula dolorida",
        "dolor al abrir la boca",
      ],
      "dolores_musculares": [
        "dolores musculares",
        "mialgias",
        "dolor en los músculos",
        "cuerpo cortado",
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