from src.services.groq_service import groq_service


def main():
    response = groq_service.generate_response(
        user_message="""
        Tengo fiebre desde hace dos días,
        tos seca y dolor de cabeza.
        """,
        symptoms=[
            "fiebre",
            "tos",
            "dolor_cabeza"
        ],
        diagnosticos=[
            {
                "enfermedad": "gripe",
                "coincidencias": 3,
                "score": 0.75
            },
            {
                "enfermedad": "covid",
                "coincidencias": 2,
                "score": 0.50
            }
        ],
        most_probable={
            "enfermedad": "gripe",
            "coincidencias": 3,
            "score": 0.75
        }
    )

    print("\n=== RESPUESTA GENERADA ===\n")
    print(response)


if __name__ == "__main__":
    main()