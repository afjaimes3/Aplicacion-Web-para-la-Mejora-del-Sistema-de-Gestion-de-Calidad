@echo off
TITLE Generador de Documentos App
CLS

echo ========================================================
echo   INICIANDO GENERADOR DE DOCUMENTOS
echo ========================================================
echo.

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no fue encontrado en este sistema.
    echo Por favor instala Python desde https://www.python.org/downloads/
    echo Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b
)

:: 2. Verificar/Crear entorno virtual
IF NOT EXIST ".venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Fallo al crear el entorno virtual.
        pause
        exit /b
    )
    echo [INFO] Entorno virtual creado exitosamente.
)

:: 3. Activar entorno e instalar dependencias
echo [INFO] Activando entorno y verificando dependencias...
call .venv\Scripts\activate
pip install -r requirements.txt >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar las dependencias.
    pause
    exit /b
)

:: 4. Iniciar la aplicacion
echo.
echo ========================================================
echo   APLICACION LISTA
echo   NO CIERRES ESTA VENTANA MIENTRAS USAS LA APP
echo ========================================================
echo.
echo Iniciando servidor... 
echo Accede a la app en tu navegador web.
echo.

python main.py

pause
