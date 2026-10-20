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

Las dependencias de Python y el procedimiento de arranque se instalarán o ejecutarán siguiendo las instrucciones del archivo `README.md` del proyecto.

## Cómo ejecutar el proyecto




