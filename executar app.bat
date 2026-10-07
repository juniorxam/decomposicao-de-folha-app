@echo off
title Sistema de Tratamento de Dados - Ergon
echo ===================================================
echo   SISTEMA DE TRATAMENTO DE DADOS - ERGON
echo ===================================================
echo.

:: Verifica Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python 3.10 ou superior.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% encontrado!
echo.

:: Atualiza pip
echo [2/4] Atualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo AVISO: Nao foi possivel atualizar o pip.
    echo Continuando com a versao instalada...
)
echo.

:: Instala/atualiza todas as dependencias do projeto
echo [3/4] Instalando dependencias do requirements.txt...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao instalar as dependencias!
    echo Verifique sua conexao com a internet e tente novamente.
    echo.
    pause
    exit /b 1
)
echo Dependencias instaladas com sucesso!
echo.

:: Executa o app
echo [4/4] Iniciando aplicativo...
echo.
echo ===================================================
echo   APLICATIVO INICIANDO...
echo   Aguarde abrir no navegador
echo   URL: http://localhost:8501
echo ===================================================
echo.

python -m streamlit run app.py --server.port 8501 --server.address localhost

pause
