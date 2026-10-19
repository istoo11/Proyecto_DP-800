
@echo off
title Buscador semantico - Proyecto DP-800

cd /d "%~dp0"

echo ========================================
echo    PROYECTO DP-800 - BUSCADOR IA
echo ========================================
echo.

echo [1/3] Iniciando Ollama...
start "Ollama" /min ollama serve

echo Esperando a que Ollama este disponible...
:esperar_ollama
timeout /t 2 /nobreak >nul
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto esperar_ollama

echo Ollama esta funcionando.
echo.

echo [2/3] Comprobando modelos...
ollama list
echo.

echo [3/3] Iniciando buscador Python...
python buscar_ejercicios.py

echo.
echo El buscador ha terminado.
pause
