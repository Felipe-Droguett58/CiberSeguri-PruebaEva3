pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
        ZAP_PORT = '8080'
        TARGET_URL = 'http://localhost:5000'
        GITHUB_CREDENTIALS_ID = 'token_pruebaEv3'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Clonando repositorio con credenciales de GitHub...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/Felipe-Droguett58/CiberSeguri-PruebaEva3.git',
                        credentialsId: env.GITHUB_CREDENTIALS_ID
                    ]]
                ])
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo 'Configurando entorno Python...'
                bat '''
                    python -m pip install --upgrade pip
                    
                    if exist requirements.txt (
                        pip install -r requirements.txt
                    ) else (
                        echo requirements.txt no encontrado, instalando dependencias básicas...
                        pip install flask
                    )
                    
                    echo Configurando base de datos...
                    
                    if exist database.db (
                        echo Base de datos encontrada, verificando estructura...
                        python -c "import sqlite3; conn=sqlite3.connect('database.db'); c=conn.cursor(); c.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\' AND name=\\'users\\''); exit(0 if c.fetchone() else 1)" 2>nul
                        if %errorlevel% equ 0 (
                            echo ✅ Base de datos válida, continuando...
                            goto :db_ok
                        ) else (
                            echo ⚠️ Base de datos corrupta o incompleta, recreando...
                            del database.db
                        )
                    )
                    
                    echo Creando nueva base de datos...
                    python create_db.py
                    
                    if %errorlevel% neq 0 (
                        echo ❌ Error al crear la base de datos
                        exit 1
                    )
                    
                    :db_ok
                    echo ✅ Base de datos lista
                    
                    echo.
                    echo === USUARIOS EN LA BASE DE DATOS ===
                    python -c "import sqlite3; conn=sqlite3.connect('database.db'); c=conn.cursor(); c.execute('SELECT id, username, role FROM users'); print('ID | Usuario | Rol'); print('---|---------|-----'); [print(f'{row[0]:2} | {row[1]:7} | {row[2]}') for row in c.fetchall()]; conn.close()"
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Construyendo aplicación...'
                bat '''
                    if exist vulnerable_app.py (
                        python -m py_compile vulnerable_app.py
                        echo ✅ Compilación exitosa
                    ) else (
                        echo ❌ vulnerable_app.py no encontrado
                        exit 1
                    )
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias...'
                bat '''
                    pip install pytest
                    
                    if exist tests (
                        pytest tests/ -v --junitxml=test-results.xml
                    ) else (
                        echo ⚠️ No se encontró la carpeta tests, saltando pruebas...
                        python -c "import xml.etree.ElementTree as ET; root=ET.Element('testsuite', {'name':'pytest','tests':'0','errors':'0','failures':'0','skipped':'0'}); tree=ET.ElementTree(root); tree.write('test-results.xml', encoding='utf-8', xml_declaration=True)"
                    )
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                echo 'Ejecutando análisis de seguridad estático...'
                bat '''
                    pip install bandit safety
                    
                    echo === BANDIT SCAN ===
                    dir *.py /b >nul 2>nul
                    if %errorlevel% equ 0 (
                        bandit -r . -f json -o bandit-report.json || echo ⚠️ Bandit encontró problemas
                    ) else (
                        echo No se encontraron archivos Python para escanear
                        echo {} > bandit-report.json
                    )
                    
                    echo === SAFETY SCAN ===
                    safety check || echo ⚠️ Safety encontró problemas en dependencias
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando aplicación en background...'
                bat '''
                    echo === LIBERANDO PUERTO 5000 SI ESTABA OCUPADO ===
                    for /F "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Matando proceso previo en el puerto 5000, PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    
                    echo === INICIANDO APLICACIÓN ===
                    set FLASK_APP=vulnerable_app.py
                    set FLASK_ENV=development
                    
                    if exist vulnerable_app.py (
                        echo Iniciando Flask...
                        start /B python -m flask run --host=0.0.0.0 --port=5000
                        timeout /t 5 /nobreak
                        
                        echo Verificando que la aplicación responda...
                        curl -s -o nul -w "HTTP Status: %%{http_code}" %TARGET_URL% || echo ⚠️ No se pudo conectar a la aplicación
                        echo.
                        echo ✅ Aplicación desplegada en %TARGET_URL%
                    ) else (
                        echo ❌ vulnerable_app.py no encontrado
                        exit 1
                    )
                '''
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                echo 'Ejecutando OWASP ZAP scan...'
                bat '''
                    echo === VERIFICANDO APLICACIÓN ===
                    
                    where curl >nul 2>nul
                    if %errorlevel% equ 0 (
                        echo Verificando conexión a %TARGET_URL%...
                        curl -s --retry 5 --retry-delay 2 %TARGET_URL%
                        if %errorlevel% neq 0 (
                            echo ❌ La aplicación no está respondiendo
                            exit 1
                        )
                    ) else (
                        echo ⚠️ curl no disponible, verificando con ping...
                        ping localhost -n 5 >nul
                    )
                    
                    echo === ESCANEO OWASP ZAP ===
                    
                    REM Buscar ZAP en múltiples ubicaciones (CORREGIDO PARA RUTAS CON ESPACIOS)
                    set "ZAP_SCRIPT="
                    
                    REM ZAP 2.16+ (nueva ubicación)
                    if exist "C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.exe" set "ZAP_SCRIPT=C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.exe"
                    if exist "C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.exe" set "ZAP_SCRIPT=C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.exe"
                    
                    REM Ubicación antigua (OWASP)
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" set "ZAP_SCRIPT=C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py"
                    if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" set "ZAP_SCRIPT=C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py"
                    
                    if defined ZAP_SCRIPT (
                        echo ✅ ZAP encontrado en: %ZAP_SCRIPT%
                        echo Ejecutando escaneo...
                        
                        REM Ejecutar ZAP con comillas para manejar espacios en la ruta
                        "%ZAP_SCRIPT%" -cmd -quickurl %TARGET_URL% -quickprogress -quickout zap-report.html || echo ⚠️ ZAP encontró problemas
                        echo ✅ Escaneo ZAP completado
                    ) else (
                        echo ⚠️ ZAP no encontrado. Generando reporte de advertencia...
                        echo ^<html^> > zap-report.html
                        echo ^<head^>^<title^>ZAP Report^</title^>^</head^> >> zap-report.html
                        echo ^<body^> >> zap-report.html
                        echo ^<h1 style="color: orange;"^>⚠️ OWASP ZAP no instalado^</h1^> >> zap-report.html
                        echo ^<p^>ZAP no se encontró en el sistema.^</p^> >> zap-report.html
                        echo ^<p^>Instala desde: ^<a href="https://www.zaproxy.org/download/"^>https://www.zaproxy.org/download/^</a^>^</p^> >> zap-report.html
                        echo ^</body^> >> zap-report.html
                        echo ^</html^> >> zap-report.html
                        echo ✅ Reporte de advertencia generado
                    )
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'zap-report.html', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            echo '=== PIPELINE COMPLETADO ==='
            echo 'Generando reportes...'
            
            archiveArtifacts artifacts: 'bandit-report.json, test-results.xml', fingerprint: true
            
            catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                bat '''
                    echo === LIMPIANDO PROCESOS ===
                    
                    REM Liberar puerto 5000 si está ocupado
                    for /F "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Deteniendo proceso en el puerto 5000, PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    
                    echo ✅ Limpieza completada
                '''
            }
            
            bat '''
                echo.
                echo === ARTEFACTOS GENERADOS ===
                dir *.json *.xml *.html 2>nul
            '''
        }
        success {
            echo '✅ ✅ ✅ PIPELINE EXITOSO ✅ ✅ ✅'
            echo 'Todos los stages se completaron correctamente'
        }
        failure {
            echo '❌ ❌ ❌ PIPELINE FALLÓ ❌ ❌ ❌'
            echo 'Revisa los logs para identificar el error'
            
            bat '''
                echo.
                echo === POSIBLES CAUSAS DE ERROR ===
                echo 1. ¿Falta algún archivo requerido? (vulnerable_app.py, requirements.txt)
                echo 2. ¿Hay problemas de red al instalar dependencias?
                echo 3. ¿La base de datos tiene errores?
                echo 4. ¿La aplicación no pudo iniciar correctamente?
                echo 5. ¿ZAP no está instalado correctamente?
            '''
        }
        unstable {
            echo '⚠️ ⚠️ ⚠️ PIPELINE INESTABLE ⚠️ ⚠️ ⚠️'
            echo 'Algunas pruebas o escaneos encontraron problemas'
            echo 'Revisa los artefactos para más detalles'
        }
    }
}
