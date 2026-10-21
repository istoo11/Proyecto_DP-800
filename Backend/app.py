
import json
import os
import re
from pathlib import Path

import ollama
import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from buscar_ejercicios import buscar_ejercicios

load_dotenv()

app = FastAPI()

MODELO_SQL = "qwen2.5:3b"
CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")

# Objetos que Qwen puede consultar.
TABLAS_PERMITIDAS = {
    "dbo.leaderboard",
    "dbo.usuarios",
    "dbo.ejercicios",
    "dbo.clasificacion",
}

# Operaciones y construcciones que no aceptamos.
PATRON_PROHIBIDO = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|"
    r"EXEC|EXECUTE|GRANT|REVOKE|DENY|BACKUP|RESTORE|DBCC|"
    r"WAITFOR|INTO|OPENROWSET|OPENQUERY|OPENDATASOURCE|"
    r"INFORMATION_SCHEMA|UNION|USE|"
    r"XP_[A-Z0-9_]*|SP_[A-Z0-9_]*"
    r")\b",
    re.IGNORECASE,
)


class PeticionBusqueda(BaseModel):
    texto: str


# --------------------------------------------------
# EJERCICIOS: búsqueda semántica existente
# --------------------------------------------------

@app.post("/buscar")
def buscar(peticion: PeticionBusqueda):
    resultados = buscar_ejercicios(peticion.texto)

    ejercicios = []

    for fila in resultados:
        ejercicios.append({
            "id": fila[0],
            "tema": fila[1],
            "enunciado": fila[2],
            "solucion": fila[3],
            "texto_completo": fila[4],
            "distancia": fila[5],
        })

    return {"resultados": ejercicios}


# --------------------------------------------------
# LEADERBOARD: generación de SQL con Ollama
# --------------------------------------------------

def generar_sql(pregunta: str) -> dict:
    """
    Pide a Qwen una consulta SQL parametrizada.
    El modelo solo propone SQL; no lo ejecuta.
    """
    
    esquema = """
    Base de datos SQL Server. Genera consultas para responder preguntas
    sobre los tiempos de los ejercicios.

    TABLAS Y COLUMNAS:

    dbo.leaderboard:
    - id
    - id_usuario
    - id_ejercicio
    - fecha_comienzo
    - fecha_fin

    dbo.usuarios:
    - id
    - nombre

    dbo.ejercicios:
    - id
    - descripcion
    - ejercicio
    - solucion
    - descripcion_ejercicio

    VISTA dbo.clasificacion:
    - id_ejercicio
    - nombre
    - bloque
    - tiempo
    - embedding

    REGLAS OBLIGATORIAS:

    1. Si el usuario pregunta por tiempos, mejores tiempos, peores
    tiempos, quién tarda menos o cuánto tarda alguien, DEBES
    generar una consulta SQL. No rechaces estas peticiones.

    2. Para calcular tiempos usa:
    DATEDIFF(SECOND, l.fecha_comienzo, l.fecha_fin).

    3. Une leaderboard con usuarios mediante:
    l.id_usuario = u.id.
    Une leaderboard con ejercicios mediante:
    l.id_ejercicio = e.id.

    4. Excluye registros sin fecha de comienzo o fin y tiempos negativos.

    5. Para los mejores tiempos, ordena de menor a mayor.
    Para los peores tiempos, ordena de mayor a menor.

    6. Si el usuario menciona un ID de ejercicio, filtra por
    l.id_ejercicio = ?.

    7. Si pide un número de resultados, úsalo como límite.
    Si no indica número, utiliza 5.

    8. La consulta debe comenzar con SELECT TOP (?).
    El primer parámetro de params debe ser el límite entero
    entre 1 y 100. Los siguientes parámetros deben corresponder
    a los signos ? restantes, en orden.

    9. Solo genera SELECT de lectura. No generes INSERT, UPDATE,
    DELETE, DROP, ALTER, EXEC ni otras operaciones de escritura.

    10. No consultes correo, contraseña ni dirección de los usuarios.

    11. Si pregunta por puntuaciones o puntos, devuelve sql null
        y explica que no existe una columna de puntos en el esquema.

    EJEMPLO PARA:
    "Dame los 5 mejores tiempos del ejercicio 3"

    Devuelve este JSON:
    {
    "sql": "SELECT TOP (?) l.id_ejercicio, u.nombre, e.descripcion AS bloque, DATEDIFF(SECOND, l.fecha_comienzo, l.fecha_fin) AS tiempo FROM dbo.leaderboard AS l JOIN dbo.usuarios AS u ON u.id = l.id_usuario JOIN dbo.ejercicios AS e ON e.id = l.id_ejercicio WHERE l.id_ejercicio = ? AND l.fecha_comienzo IS NOT NULL AND l.fecha_fin IS NOT NULL AND l.fecha_fin >= l.fecha_comienzo ORDER BY tiempo ASC",
    "params": [5, 3],
    "mensaje": "Mejores tiempos del ejercicio 3"
    }

    Devuelve únicamente JSON válido con las claves sql, params y mensaje.
    """


    respuesta = ollama.chat(
        model=MODELO_SQL,
        format="json",
        options={"temperature": 0},
        messages=[
            {
                "role": "system",
                "content": (
                    "Genera SQL Server para preguntas sobre tiempos de ejercicios. "
                    "Sigue las instrucciones del esquema y el ejemplo literalmente "
                    "en cuanto a estructura y parámetros. "
                    "Para consultas de tiempos, genera SQL y no devuelvas sql null. "
                    "Devuelve únicamente JSON válido.\n\n"
                    + esquema
                ),
            },
            {
                "role": "user",
                "content": pregunta,
            },
        ],
    )

    contenido = respuesta["message"]["content"]

    try:
        resultado = json.loads(contenido)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Ollama no ha devuelto un JSON válido.",
        )

    if not isinstance(resultado, dict):
        raise HTTPException(
            status_code=502,
            detail="La respuesta de Ollama tiene un formato incorrecto.",
        )

    return resultado


def validar_sql(sql: str, parametros: list):
    """
    Comprobaciones defensivas básicas.
    No sustituyen los permisos de solo lectura de SQL Server.
    """

    if not isinstance(sql, str) or not isinstance(parametros, list):
        raise HTTPException(
            status_code=400,
            detail="La consulta generada no tiene un formato válido.",
        )

    sql = sql.strip()

    # Aceptamos una sola sentencia SELECT.
    if not re.match(r"^SELECT\b", sql, re.IGNORECASE):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten consultas SELECT.",
        )

    # Evita sentencias adicionales, comentarios y algunas
    # construcciones que no necesitamos en este proyecto.
    if any(marca in sql for marca in (";", "--", "/*", "*/")):
        raise HTTPException(
            status_code=400,
            detail="La consulta contiene sintaxis no permitida.",
        )

    if PATRON_PROHIBIDO.search(sql):
        raise HTTPException(
            status_code=400,
            detail="La consulta contiene una operación no permitida.",
        )

    # Impedimos referencias a columnas sensibles.
    if re.search(
        r"\b(contraseña|password|correo|direccion)\b",
        sql,
        re.IGNORECASE,
    ):
        raise HTTPException(
            status_code=400,
            detail="La consulta intenta acceder a datos privados.",
        )

    # Bloqueamos otras construcciones que no necesitamos.
    if re.search(
        r"\b(WITH|APPLY|PIVOT|UNPIVOT|"
        r"FOR\s+XML|FOR\s+JSON|OPTION)\b",
        sql,
        re.IGNORECASE,
    ):
        raise HTTPException(
            status_code=400,
            detail="La consulta utiliza una construcción no permitida.",
        )

    # Comprobamos las tablas utilizadas en FROM y JOIN.
    referencias = re.findall(
        r"\b(?:FROM|JOIN)\s+"
        r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)",
        sql,
        re.IGNORECASE,
    )

    if not referencias:
        raise HTTPException(
            status_code=400,
            detail="No se han encontrado tablas en la consulta.",
        )

    for tabla in referencias:
        nombre = tabla.lower()

        # Solo aceptamos los objetos definidos en la lista permitida.
        if nombre not in TABLAS_PERMITIDAS:
            raise HTTPException(
                status_code=400,
                detail=f"El objeto SQL '{tabla}' no está permitido.",
            )

    # Obligamos a limitar el número de filas.
    coincidencia_top = re.search(
        r"\bTOP\s*(?:\(\s*(\?)\s*\)|\(\s*(\d+)\s*\)|(\d+))",
        sql,
        re.IGNORECASE,
    )

    if not coincidencia_top:
        raise HTTPException(
            status_code=400,
            detail=(
                "La consulta debe limitar los resultados con TOP "
                "y utilizar un parámetro o un límite entero."
            ),
        )

    if coincidencia_top.group(1) == "?":
        pass
    elif coincidencia_top.group(2) is not None:
        limite_sql = int(coincidencia_top.group(2))

        if not 1 <= limite_sql <= 100:
            raise HTTPException(
                status_code=400,
                detail="El límite TOP debe estar entre 1 y 100.",
            )
    else:
        limite_sql = int(coincidencia_top.group(3))

        if not 1 <= limite_sql <= 100:
            raise HTTPException(
                status_code=400,
                detail="El límite TOP debe estar entre 1 y 100.",
            )

    if not parametros:
        raise HTTPException(
            status_code=400,
            detail="Falta el parámetro del límite de resultados.",
        )

    limite = parametros[0]

    if (
        isinstance(limite, bool)
        or not isinstance(limite, int)
        or not 1 <= limite <= 100
    ):
        raise HTTPException(
            status_code=400,
            detail="El límite debe ser un entero entre 1 y 100.",
        )

    # En este formato no esperamos signos ? dentro de textos SQL.
    if sql.count("?") != len(parametros):
        raise HTTPException(
            status_code=400,
            detail="El número de parámetros no coincide con el SQL.",
        )

    return sql


def ejecutar_sql(sql: str, parametros: list) -> list:
    """
    Ejecuta la consulta y convierte las filas en diccionarios.
    """

    if not CONNECTION_STRING:
        raise HTTPException(
            status_code=500,
            detail="No se ha configurado SQL_CONNECTION_STRING.",
        )

    try:
        with pyodbc.connect(CONNECTION_STRING) as conexion:
            cursor = conexion.cursor()
            cursor.execute(sql, parametros)

            columnas = [columna[0] for columna in cursor.description]
            filas = cursor.fetchall()

            return [
                {
                    columna: valor
                    for columna, valor in zip(columnas, fila)
                }
                for fila in filas
            ]

    except pyodbc.Error:
        # No exponemos al navegador los detalles internos de SQL Server.
        raise HTTPException(
            status_code=500,
            detail="No se ha podido ejecutar la consulta en SQL Server.",
        )


@app.post("/leaderboard/buscar")
def buscar_leaderboard(peticion: PeticionBusqueda):
    pregunta = peticion.texto.strip()

    if not pregunta:
        raise HTTPException(
            status_code=400,
            detail="Escribe una pregunta para consultar el Leaderboard.",
        )

    # 1. Qwen genera una propuesta de consulta.
    propuesta = generar_sql(pregunta)
    print("SQL generado por Qwen:", propuesta.get("sql"))
    print("Parámetros:", propuesta.get("params"))

    sql = propuesta.get("sql")
    parametros = propuesta.get("params", [])
    mensaje = propuesta.get("mensaje", "")

    # El modelo puede indicar que la petición no se puede responder.
    if sql is None:
        return {
            "mensaje": mensaje or "No puedo responder a esa consulta.",
            "sql": None,
            "resultados": [],
        }

    # 2. Python valida la propuesta.
    sql_validado = validar_sql(sql, parametros)

    # 3. Python ejecuta el SQL parametrizado.
    resultados = ejecutar_sql(sql_validado, parametros)

    # 4. Devolvemos los datos al frontend.
    return {
        "mensaje": mensaje or "Consulta realizada correctamente.",
        "sql": sql_validado,
        "resultados": resultados,
    }


# --------------------------------------------------
# FRONTEND: mantener el montaje al final
# --------------------------------------------------

RUTA_FRONTEND = Path(__file__).resolve().parent.parent / "Frontend"

app.mount(
    "/",
    StaticFiles(directory=str(RUTA_FRONTEND), html=True),
    name="frontend",
)
