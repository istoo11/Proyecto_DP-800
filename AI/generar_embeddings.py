
import json
import os
import sys

import ollama
import pyodbc
from dotenv import load_dotenv

load_dotenv()

MODEL = "embeddinggemma"
DIMENSIONES = 768

CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")

if not CONNECTION_STRING:
    sys.exit("Error: configura SQL_CONNECTION_STRING en el archivo .env")


def generar_embedding(texto):
    respuesta = ollama.embed(
        model=MODEL,
        input=texto
    )

    vector = respuesta.embeddings[0]

    if len(vector) != DIMENSIONES:
        raise ValueError(
            f"El modelo ha generado {len(vector)} dimensiones; "
            f"la columna espera {DIMENSIONES}."
        )

    return vector


def main():
    conexion = None

    try:
        conexion = pyodbc.connect(CONNECTION_STRING)
        cursor = conexion.cursor()

        # Obtener únicamente los registros pendientes.
        cursor.execute("""
            SELECT
                id,
                descripcion,
                ejercicio,
                descripcion_ejercicio
            FROM dbo.ejercicios
            WHERE embedding IS NULL
            ORDER BY id;
        """)

        ejercicios = cursor.fetchall()

        if not ejercicios:
            print(
                "No hay ejercicios pendientes. "
                "Comprueba que la tabla contiene datos "
                "y que sus embeddings son NULL."
            )
            return

        print(f"Ejercicios pendientes: {len(ejercicios)}")

        procesados = 0

        for fila in ejercicios:
            ejercicio_id = fila.id

            # Combinamos los textos que describen el ejercicio.
            texto = (
                f"Descripción: {fila.descripcion}\n"
                f"Ejercicio: {fila.ejercicio}\n"
                f"Descripción del ejercicio: "
                f"{fila.descripcion_ejercicio}"
            )

            vector = generar_embedding(texto)

            # SQL Server convierte el JSON al tipo VECTOR.
            vector_json = json.dumps(
                vector,
                separators=(",", ":")
            )

            cursor.execute("""
                UPDATE dbo.ejercicios
                SET embedding = CAST(
                    CAST(? AS NVARCHAR(MAX))
                    AS VECTOR(768)
                )
                WHERE id = ?
                AND embedding IS NULL;
            """, (vector_json, ejercicio_id))

            conexion.commit()
            procesados += cursor.rowcount if cursor.rowcount > 0 else 0

            print(
                f"Procesado ID {ejercicio_id} "
                f"({procesados}/{len(ejercicios)})"
            )

        print(f"\nFinalizado. Registros actualizados: {procesados}")

    except Exception as error:
        if conexion is not None:
            conexion.rollback()

        print(f"Error al generar embeddings: {error}")
        raise

    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    main()
