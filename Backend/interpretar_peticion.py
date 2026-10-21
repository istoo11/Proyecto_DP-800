
import json
import requests

MODELO = "qwen2.5:3b"

ESQUEMA = {
    "type": "object",
    "properties": {
        "accion": {
            "type": "string",
            "enum": [
                "buscar_ejercicios",
                "puntuaciones_ejercicio",
                "mejores_tiempos",
                "peticion_no_reconocida"
            ]
        },
        "id_ejercicio": {
            "type": ["integer", "null"]
        },
        "limite": {
            "type": "integer"
        }
    },
    "required": ["accion", "id_ejercicio", "limite"]
}


def interpretar_peticion(texto):
    respuesta = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": MODELO,
            "stream": False,
            "format": ESQUEMA,
            "options": {"temperature": 0},
            "messages": [
                {
                    "role": "system",
                    "content": """
                    Eres un clasificador de peticiones para una aplicación
                    de ejercicios y estadísticas.

                    Reglas:
                    - Buscar ejercicios por tema o descripción:
                      buscar_ejercicios.
                    - Consultar puntuaciones de un ejercicio concreto:
                      puntuaciones_ejercicio.
                    - Pedir mejores tiempos, sin importar el ejercicio:
                      mejores_tiempos.
                    - Si la petición no corresponde a esas operaciones:
                      peticion_no_reconocida.

                    Extrae el ID del ejercicio si se menciona.
                    Si se pide un número de resultados, extrae ese número.
                    Si no se indica límite, utiliza 5.
                    No inventes IDs de ejercicios.
                    """
                },
                {
                    "role": "user",
                    "content": texto
                }
            ]
        },
        timeout=120
    )

    respuesta.raise_for_status()

    datos = json.loads(
        respuesta.json()["message"]["content"]
    )

    # Validaciones adicionales: el modelo no decide los límites permitidos.
    if datos["accion"] not in {
        "buscar_ejercicios",
        "puntuaciones_ejercicio",
        "mejores_tiempos",
        "peticion_no_reconocida"
    }:
        raise ValueError("Acción no permitida")

    datos["limite"] = max(1, min(datos["limite"], 50))

    if datos["id_ejercicio"] is not None:
        if datos["id_ejercicio"] < 1:
            raise ValueError("ID de ejercicio no válido")

    return datos
