# Proyecto_DP-800

## Requisitos para ejecutar el proyecto

Para ejecutar esta aplicación de chat con IA local, es necesario instalar los siguientes programas en el equipo.

### Python

Necesario para ejecutar el backend y la lógica de la aplicación.

- **Versión recomendada:** Python 3.12.
- **Descarga:** ```winget install Python.Python.3.14```
- **Importante:** durante la instalación en Windows, marcar la opción `Add Python to PATH`.

### Ollama

Necesario para ejecutar los modelos de inteligencia artificial localmente, sin depender de una API externa de IA.

- **Versión recomendada:** ollama version 0.40.6
- **Descarga:** ```irm https://ollama.com/install.ps1 | iex```

### Modelos de inteligencia artificial

Después de instalar Ollama, descargar los siguientes modelos desde una terminal:

-  ```ollama pull embeddinggemma```
-  ```ollama pull qwen2.5:3b``` 

Los modelos se descargan una sola vez y quedan disponibles localmente.

### SQL Server y controlador ODBC

La aplicación necesita acceder a SQL Server para consultar los datos y realizar las búsquedas vectoriales.

- **SQL Server:** https://www.microsoft.com/sql-server/sql-server-downloads
- **Microsoft ODBC Driver for SQL Server:** https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

## Preparar el entorno virtual

Si es la primera vez que ejecutas el proyecto en tu equipo, abre una terminal en la carpeta raíz del repositorio y ejecuta los siguientes comandos.

**1. Crear el entorno virtual de Python**

```powershell
py -3 -m venv Backend\.venv
```

**2. Instalar las dependencias del proyecto**

```powershell
.\Backend\.venv\Scripts\python.exe -m pip install -r Backend\requirements.txt
```

Una vez completados estos pasos, el entorno virtual estará preparado para ejecutar la aplicación. No es necesario repetirlos en cada inicio, salvo que tengas que instalar nuevas dependencias o reconstruir el entorno.

## Ejecutar el proyecto

Antes de iniciar la aplicación, asegúrate de cumplir los siguientes requisitos:

- **Python y dependencias:** tener Python instalado y el entorno virtual creado en `Backend/.venv`, con las dependencias del archivo `Backend/requirements.txt` instaladas.
- **Base de datos:** ejecutar previamente todos los scripts SQL de la carpeta `Scripts` para crear las tablas y preparar los datos necesarios.
- **Configuración:** crear y configurar el archivo `Backend/.env` con la cadena de conexión a SQL Server.
- **Ollama:** tener Ollama instalado y en ejecución.
- **Modelos de IA:** descargar los modelos `embeddinggemma` y `qwen2.5:3b` mediante los siguientes comandos:

  ```powershell
  ollama pull embeddinggemma
  ollama pull qwen2.5:3b
  ```

### Iniciar la aplicación

Una vez completados los pasos anteriores, abre una terminal en la carpeta raíz del proyecto y ejecuta el siguiente comando:

```powershell
.\Backend\.venv\Scripts\python.exe -m uvicorn app:app --app-dir Backend --host 127.0.0.1 --port 8000
```

Cuando el servidor esté iniciado, abre la siguiente dirección en tu navegador:

http://127.0.0.1:8000

Para detener el servidor, pulsa `Ctrl + C` en la terminal.

