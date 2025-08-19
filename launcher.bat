@echo off
setlocal enabledelayedexpansion
echo ====================================================
echo    SOCIAL MEDIA SCRAPER - LAUNCHER v2.0
echo ====================================================
echo.

:: Verificar si se está ejecutando como administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] No se está ejecutando como administrador.
    echo [INFO] Esto puede causar problemas de permisos con pip.
    echo [INFO] Si hay errores, ejecuta como administrador.
    echo.
)

:: Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Por favor instala Python 3.8-3.11 desde https://python.org
    echo [WARNING] Python 3.13 tiene problemas de compatibilidad, usa 3.8-3.11
    pause
    exit /b 1
)

:: Mostrar versión de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python %PYTHON_VERSION% detectado

:: Crear estructura de carpetas si no existe
if not exist "src" mkdir src
if not exist "src\utils" mkdir src\utils
if not exist "src\javascript" mkdir src\javascript
if not exist "scrape" mkdir scrape
if not exist "scrape\tiktok" mkdir scrape\tiktok
if not exist "scrape\instagram" mkdir scrape\instagram
if not exist "scrape\facebook" mkdir scrape\facebook

echo [INFO] Verificando estructura de carpetas... OK
echo.

:: Limpiar cache de pip para evitar problemas de permisos
echo [INFO] Limpiando cache de pip...
python -m pip cache purge >nul 2>&1

:: Crear entorno virtual si no existe
if not exist "venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv venv --clear
    if %errorlevel% neq 0 (
        echo [ERROR] Error creando entorno virtual
        pause
        exit /b 1
    )
)

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] No se pudo encontrar el script de activación del entorno virtual
    pause
    exit /b 1
)

:: Actualizar pip en el entorno virtual
echo [INFO] Actualizando pip...
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

:: Configurar pip para preferir wheels precompilados y evitar compilación
echo [INFO] Configurando pip para usar wheels precompilados...
set PIP_PREFER_BINARY=1
set PIP_ONLY_BINARY=:all:

:: Instalar dependencias básicas primero
echo [INFO] Instalando dependencias básicas...
python -m pip install --no-cache-dir colorama==0.4.6
python -m pip install --no-cache-dir tqdm==4.66.1
python -m pip install --no-cache-dir python-dotenv==1.0.0
python -m pip install --no-cache-dir fake-useragent==1.4.0

:: Instalar dependencias de red
echo [INFO] Instalando dependencias de red...
python -m pip install --no-cache-dir requests==2.31.0
python -m pip install --no-cache-dir urllib3==2.0.7

:: Instalar scrapfly
echo [INFO] Instalando ScrapFly SDK...
python -m pip install --no-cache-dir scrapfly-sdk==0.8.23

:: Instalar dependencias de parsing
echo [INFO] Instalando dependencias de parsing...
python -m pip install --no-cache-dir beautifulsoup4==4.12.2

:: Instalar openpyxl para Excel
echo [INFO] Instalando OpenPyXL para Excel...
python -m pip install --no-cache-dir openpyxl==3.1.2

:: Intentar instalar lxml con mejores opciones
echo [INFO] Instalando lxml (opcional)...
:: Deshabilitar temporalmente la variable para permitir más flexibilidad con lxml
set PIP_ONLY_BINARY=
:: Primero intentar con wheels precompilados
python -m pip install --no-cache-dir --prefer-binary lxml 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Intentando con versión estable de lxml...
    python -m pip install --no-cache-dir --prefer-binary lxml==4.9.2 2>nul
    if %errorlevel% neq 0 (
        echo [INFO] Intentando versión más compatible de lxml...
        python -m pip install --no-cache-dir --prefer-binary lxml==4.8.0 2>nul
        if %errorlevel% neq 0 (
            echo [INFO] Última tentativa con versión muy estable...
            python -m pip install --no-cache-dir lxml==4.6.5 2>nul
            if %errorlevel% neq 0 (
                echo [WARNING] lxml no se pudo instalar, pero no es crítico.
                echo [INFO] BeautifulSoup funcionará con el parser html.parser integrado.
            ) else (
                echo [OK] lxml 4.6.5 instalado correctamente
            )
        ) else (
            echo [OK] lxml 4.8.0 instalado correctamente
        )
    ) else (
        echo [OK] lxml 4.9.2 instalado correctamente
    )
) else (
    echo [OK] lxml instalado correctamente
)
:: Restaurar la configuración
set PIP_ONLY_BINARY=:all:

:: Verificar que las dependencias críticas estén instaladas
echo [INFO] Verificando instalación...
python -c "import colorama, requests, openpyxl, bs4, scrapfly; print('[OK] Todas las dependencias críticas instaladas')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Algunas dependencias críticas faltan
    echo [INFO] Intentando reparar...
    
    :: Intentar instalar lo esencial sin versiones específicas
    python -m pip install colorama requests openpyxl beautifulsoup4 scrapfly-sdk tqdm python-dotenv fake-useragent --no-cache-dir --prefer-binary
    
    :: Verificar nuevamente
    python -c "import colorama, requests, openpyxl, bs4, scrapfly; print('[OK] Reparación exitosa')" 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudieron instalar todas las dependencias críticas
        echo [INFO] Intenta ejecutar el launcher como administrador
        echo [INFO] O instala Visual Studio Build Tools si el problema persiste
        pause
        exit /b 1
    )
)

:: Verificar parsers disponibles para BeautifulSoup
echo [INFO] Verificando parsers de BeautifulSoup...
python -c "from bs4 import BeautifulSoup; BeautifulSoup('<test></test>', 'html.parser'); print('[OK] Parser html.parser disponible')" 2>nul

:: Intentar verificar lxml parser (opcional)
python -c "from bs4 import BeautifulSoup; BeautifulSoup('<test></test>', 'lxml'); print('[OK] Parser lxml disponible')" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Parser lxml no disponible (usará html.parser como fallback)
)

echo.
echo [INFO] Iniciando Social Media Scraper...
echo.

:: Verificar que el archivo principal existe
if not exist "src\main_controller.py" (
    echo [ERROR] Archivo src\main_controller.py no encontrado
    echo [INFO] Asegúrate de que todos los archivos del proyecto estén presentes
    pause
    exit /b 1
)

:: Ejecutar el controlador principal
python src\main_controller.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Error ejecutando el scraper
    echo [INFO] Verifica los logs arriba para más detalles
    pause
) else (
    echo.
    echo [SUCCESS] Scraper ejecutado correctamente
)

echo.
echo [INFO] Proceso completado. Presiona cualquier tecla para salir.
pause >nul