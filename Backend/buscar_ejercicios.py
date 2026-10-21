import json
import os

import ollama
import pyodbc
from dotenv import load_dotenv

load_dotenv()

MODELO_EMBEDDING = "embeddinggemma"
DIMENSIONES = 768
RESULTADOS = 5

CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")


def generar_embedding(texto):
    respuesta = ollama.embed(
        model=MODELO_EMBEDDING,
        input=texto
    )

    vector = respuesta.embeddings[0]

    if len(vector) != DIMENSIONES:
        raise ValueError(
            f"Se esperaban {DIMENSIONES} dimensiones, "
            f"pero se recibieron {len(vector)}."
        )

    return vector


def buscar_ejercicios(pregunta):
    vector = generar_embedding(pregunta)
    vector_json = json.dumps(vector)

    with pyodbc.connect(CONNECTION_STRING) as conexion:
        cursor = conexion.cursor()

        consulta = """
            DECLARE @vector VECTOR(768);

            SET @vector = CAST(
                CAST(? AS NVARCHAR(MAX))
                AS VECTOR(768)
            );

            SELECT TOP (?)
                id,
                descripcion,
                ejercicio,
                solucion,
                descripcion_ejercicio,
                VECTOR_DISTANCE(
                    'cosine',
                    @vector,
                    CAST(embedding AS VECTOR(768))
                ) AS distancia
            FROM dbo.ejercicios
            WHERE embedding IS NOT NULL
            ORDER BY distancia ASC;
        """

        cursor.execute(consulta, (vector_json, RESULTADOS))

        return cursor.fetchall()


