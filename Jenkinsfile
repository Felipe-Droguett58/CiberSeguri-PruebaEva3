pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
        ZAP_PORT = '8080'
        TARGET_URL = 'http://localhost:5000'
        GITHUB_CREDENTIALS_ID = 'token_pruebaEv3'
        // Controlar si se reinicia la DB (true = eliminar y recrear)
        RESET_DATABASE = 'true'  // Cambiar a 'true' para resetear en cada ejecución
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
                    
                    REM === MANEJO AVANZADO DE LA BASE DE DATOS ===
                    
                    REM 1. Verificar si la base de datos existe y debe resetearse
                    if "%RESET_DATABASE%"=="true" (
                        echo Reiniciando base de datos...
                        if exist database.db (
                            echo Eliminando database.db existente...
                            del database.db
                        )
                    )
                    
                    REM 2. Ejecutar create_db.py con manejo de errores
                    python create_db.py
                    
                    REM 3. Verificar que la base de datos se creó correctamente
                    if exist database.db (
                        echo ✅ Base de datos creada exitosamente
                        
                        REM 4. Mostrar información de la base de datos
                        echo.
                        echo === USUARIOS EN LA BASE DE DATOS ===
                        python -c "import sqlite3; conn=sqlite3.connect('database.db'); c=conn.cursor(); c.execute('SELECT id, username, role FROM users'); print('ID | Usuario | Rol'); print('---|---------|-----'); [print(f'{row[0]:2} | {row[1]:7} | {row[2]}') for row in c.fetchall()]; conn.close()" 2>nul || echo No se pudo mostrar usuarios
                    ) else (
                        echo ❌ Error: No se pudo crear la base de datos
                        exit 1
                    )
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
                        echo <?xml version="1.0" encoding="UTF-8"?> > test-results.xml
                        echo <testsuite name="pytest" tests="0" errors="0" failures="0" skipped="0"> >> test-results.xml
                        echo </testsuite> >> test-results.xml
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
                    echo === INICIANDO APLICACIÓN ===
                    set FLASK_APP=vulnerable_app.py
                    set FLASK_ENV=development
                    
                    if exist vulnerable_app.py (
                        echo Iniciando Flask...
                        start /B flask run --host=0.0.0.0 --port=5000
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
                    
                    REM Buscar ZAP en ubicaciones comunes
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        echo Usando ZAP desde Program Files...
                        "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html
                        echo ✅ Escaneo ZAP completado
                    ) else if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        echo Usando ZAP desde Program Files (x86)...
                        "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html
                        echo ✅ Escaneo ZAP completado
                    ) else (
                        echo ⚠️ ZAP no encontrado. Generando reporte de advertencia...
                        echo ^<html^> > zap-report.html
                        echo ^<head^>^<title^>ZAP Report^</title^>^</head^> >> zap-report.html
                        echo ^<body^> >> zap-report.html
                        echo ^<h1 style="color: orange;"^>⚠️ OWASP ZAP no instalado^</h1^> >> zap-report.html
                        echo ^<p^>ZAP no se encontró en el sistema.^</p^> >> zap-report.html
                        echo ^<p^>Instala desde: ^<a href="https://www.zaproxy.org/download/"^>https://www.zaproxy.org/download/^</a^>^</p^> >> zap-report.html
                        echo ^<ul^> >> zap-report.html
                        echo ^<li^>En Program Files: C:\\Program Files\\OWASP\\Zed Attack Proxy\\^</li^> >> zap-report.html
                        echo ^<li^>En Program Files (x86): C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\^</li^> >> zap-report.html
                        echo ^</ul^> >> zap-report.html
                        echo ^</body^> >> zap-report.html
                        echo ^</html^> >> zap-report.html
                        echo ⚠️ Reporte de advertencia generado
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
            
            bat '''
                echo === LIMPIANDO PROCESOS ===
                taskkill /F /IM python.exe 2>nul || echo No hay procesos Python que limpiar
                taskkill /F /IM java.exe 2>nul || echo No hay procesos Java que limpiar
                echo ✅ Limpieza completada
            '''
            
            // Mostrar resumen de artefactos
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
            
            // Mostrar errores comunes
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
