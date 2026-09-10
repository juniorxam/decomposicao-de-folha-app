@echo off
title Sistema de Tratamento de Dados - Ergon
echo ===================================================
echo   SISTEMA DE TRATAMENTO DE DADOS - ERGON
echo ===================================================
echo.

:: Verifica Python
echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo.
    echo Por favor, instale o Python 3.7 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Lembre-se de marcar "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% encontrado!
echo.

:: Verifica bibliotecas
echo [2/3] Verificando bibliotecas...

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Bibliotecas nao encontradas. Instalando...
    echo.
    echo Instalando bibliotecas necessarias...
    echo Aguarde, isso pode levar alguns minutos...
    echo.
    
    pip install --upgrade pip
    pip install streamlit pandas openpyxl xlsxwriter python-dateutil xlrd
    
    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao instalar as bibliotecas!
        echo Tente executar como Administrador.
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo Bibliotecas instaladas com sucesso!
) else (
    echo Bibliotecas OK!
)
echo.

:: Executa o app
echo [3/3] Iniciando aplicativo...
echo.
echo ===================================================
echo   APLICATIVO INICIANDO...
echo   Aguarde abrir no navegador
echo   URL: http://localhost:8501
echo ===================================================
echo.

streamlit run app.py --server.port 8501 --server.address localhost

pause