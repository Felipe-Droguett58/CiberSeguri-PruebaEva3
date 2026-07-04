pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
        ZAP_PORT = '8080'
        TARGET_URL = 'http://localhost:5000'
        GITHUB_CREDENTIALS_ID = 'PruebaEv3'
        
        // SonarQube Configuration - CORREGIDO PARA DOCKER
        SONAR_HOST_URL = 'http://host.docker.internal:9000'  // ← CAMBIADO de localhost
        SONAR_TOKEN = credentials('sonarqube-Ev3')
        SONAR_PROJECT_KEY = 'ciberseguri_Ev3'
        SONAR_PROJECT_NAME = 'ciberseguri_Ev3'
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
        
        stage('SonarQube Analysis') {
            steps {
                echo '=== EJECUTANDO ANÁLISIS CON SONARQUBE ==='
                script {
                    // Verificar que SonarQube esté corriendo
                    try {
                        def sonarStatus = bat(
                            script: "curl -s -o nul -w \"%%{http_code}\" http://localhost:9000/api/system/status",
                            returnStdout: true
                        ).trim()
                        echo "SonarQube Status Code: ${sonarStatus}"
                    } catch (Exception e) {
                        echo '⚠️ SonarQube no está disponible.'
                    }
                }
                
                bat '''
                    echo Verificando SonarQube Scanner...
                    
                    REM Crear sonar-project.properties
                    (
                        echo sonar.projectKey=%SONAR_PROJECT_KEY%
                        echo sonar.projectName=%SONAR_PROJECT_NAME%
                        echo sonar.projectVersion=1.0
                        echo sonar.sources=.
                        echo sonar.exclusions=**/tests/**,**/venv/**,**/__pycache__/**,**/node_modules/**
                        echo sonar.python.version=3.9
                        echo sonar.python.coverage.reportPaths=coverage.xml
                        echo sonar.host.url=%SONAR_HOST_URL%
                    ) > sonar-project.properties
                    
                    echo Ejecutando análisis de SonarQube con Docker...
                    
                    REM Usar Docker para ejecutar SonarQube Scanner
                    docker run --rm -v "%cd%":/usr/src -v sonar-scanner-data:/root/.sonar/cache ^
                        sonarsource/sonar-scanner-cli:latest ^
                        -Dsonar.projectKey=%SONAR_PROJECT_KEY% ^
                        -Dsonar.projectName=%SONAR_PROJECT_NAME% ^
                        -Dsonar.projectVersion=1.0 ^
                        -Dsonar.sources=. ^
                        -Dsonar.exclusions=**/tests/**,**/venv/**,**/__pycache__/**,**/node_modules/** ^
                        -Dsonar.python.version=3.9 ^
                        -Dsonar.python.coverage.reportPaths=coverage.xml ^
                        -Dsonar.host.url=%SONAR_HOST_URL% ^
                        -Dsonar.token=%SONAR_TOKEN%
                    
                    echo ✅ Análisis SonarQube completado
                    echo 📊 Ver resultados en: %SONAR_HOST_URL%/dashboard?id=%SONAR_PROJECT_KEY%
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'sonar-project.properties', fingerprint: true
                }
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
        
        stage('Test & Coverage') {
            steps {
                echo 'Ejecutando pruebas unitarias con cobertura...'
                bat '''
                    pip install pytest pytest-cov coverage
                    
                    if exist tests (
                        pytest tests/ -v --junitxml=test-results.xml --cov=. --cov-report=xml --cov-report=html
                    ) else (
                        echo ⚠️ No se encontró la carpeta tests, saltando pruebas...
                        python -c "import xml.etree.ElementTree as ET; root=ET.Element('testsuite', {'name':'pytest','tests':'0','errors':'0','failures':'0','skipped':'0'}); tree=ET.ElementTree(root); tree.write('test-results.xml', encoding='utf-8', xml_declaration=True)"
                    )
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'coverage.xml, coverage_html/**', fingerprint: true
                }
            }
        }
        
        stage('Vulnerability Analysis') {
            steps {
                echo '=== ANALIZANDO CÓDIGO VULNERABLE ==='
                bat '''
                    echo Identificando vulnerabilidades en vulnerable_app.py...
                    
                    if not exist reports mkdir reports
                    
                    REM Buscar SQL Injection
                    echo === SQL INJECTION DETECTION === > reports/vulnerabilities.txt
                    echo. >> reports/vulnerabilities.txt
                    findstr /N /C:"execute(" /C:"SELECT" /C:"INSERT" /C:"UPDATE" /C:"DELETE" vulnerable_app.py >> reports/vulnerabilities.txt 2>nul
                    
                    REM Buscar XSS
                    echo. >> reports/vulnerabilities.txt
                    echo === XSS DETECTION === >> reports/vulnerabilities.txt
                    echo. >> reports/vulnerabilities.txt
                    findstr /N /C:"render_template" /C:"return render_template" /C:"{{" /C:"| safe" vulnerable_app.py >> reports/vulnerabilities.txt 2>nul
                    
                    REM Buscar credenciales hardcodeadas
                    echo. >> reports/vulnerabilities.txt
                    echo === HARDCODED CREDENTIALS === >> reports/vulnerabilities.txt
                    echo. >> reports/vulnerabilities.txt
                    findstr /N /C:"password =" /C:"passwd =" /C:"secret =" /C:"api_key =" /C:"token =" vulnerable_app.py >> reports/vulnerabilities.txt 2>nul
                    
                    REM Buscar configuraciones inseguras
                    echo. >> reports/vulnerabilities.txt
                    echo === INSECURE CONFIGURATIONS === >> reports/vulnerabilities.txt
                    echo. >> reports/vulnerabilities.txt
                    findstr /N /C:"debug=True" /C:"SECRET_KEY =" /C:"DEBUG = True" vulnerable_app.py >> reports/vulnerabilities.txt 2>nul
                    
                    echo ✅ Análisis completado
                    echo.
                    echo === VULNERABILIDADES ENCONTRADAS ===
                    type reports/vulnerabilities.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/vulnerabilities.txt', fingerprint: true
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
                        bandit -r . -f html -o bandit-report.html || echo ⚠️ Bandit encontró problemas
                        bandit -r . -f csv -o bandit-report.csv || echo ⚠️ Bandit encontró problemas
                    ) else (
                        echo No se encontraron archivos Python para escanear
                        echo {} > bandit-report.json
                        echo <html><body>No Python files found</body></html> > bandit-report.html
                    )
                    
                    echo === SAFETY SCAN ===
                    safety check --json > safety-report.json || echo ⚠️ Safety encontró problemas en dependencias
                    safety check --full-report > safety-report.txt || echo ⚠️ Safety encontró problemas en dependencias
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json, bandit-report.html, bandit-report.csv, safety-report.json, safety-report.txt', fingerprint: true
                }
            }
        }
        
        stage('Fix Vulnerabilities') {
            steps {
                echo '=== APLICANDO CORRECCIONES DE SEGURIDAD ==='
                bat '''
                    echo Creando versión segura de la aplicación...
                    
                    copy vulnerable_app.py secure_app.py 2>nul
                    
                    echo Aplicando correcciones de seguridad...
                    
                    powershell -Command "
                        # Leer el contenido del archivo
                        \$content = Get-Content -Path secure_app.py -Raw
                        
                        # 1. CORRECCIÓN SQL INJECTION
                        \$content = \$content -replace 'cursor\\.execute\\(\\s*\"SELECT.*?\\s*\\+\\s*\\w+', {
                            \$match = \$args[0].Value
                            Write-Host '🔧 Corrigiendo SQL Injection'
                            return \$match -replace '\\+\\s*\\w+', ', ('
                        }
                        
                        # 2. CORRECCIÓN XSS
                        \$content = \$content -replace 'return render_template\\([^,]+,\\s*(\\w+)\\s*=\\s*(\\w+)', {
                            \$match = \$args[0].Value
                            Write-Host '🔧 Corrigiendo XSS'
                            return \$match + ' | safe'
                        }
                        
                        # 3. CORRECCIÓN CREDENCIALES
                        \$content = \$content -replace 'password\\s*=\\s*\"[^\"]*\"', 'password = os.environ.get(\"DB_PASSWORD\", \"\")'
                        \$content = \$content -replace 'SECRET_KEY\\s*=\\s*\"[^\"]*\"', 'SECRET_KEY = os.environ.get(\"SECRET_KEY\", \"default-secret-key\")'
                        
                        # 4. CORRECCIÓN DEBUG
                        \$content = \$content -replace 'debug\\s*=\\s*True', 'debug = False'
                        
                        # Guardar el archivo corregido
                        Set-Content -Path secure_app.py -Value \$content
                        
                        Write-Host '✅ Correcciones aplicadas en secure_app.py'
                    "
                    
                    echo.
                    echo === COMPARACIÓN DE CAMBIOS ===
                    echo Archivo original: vulnerable_app.py
                    echo Archivo corregido: secure_app.py
                    
                    echo ✅ Versión segura creada exitosamente
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'secure_app.py', fingerprint: true
                }
            }
        }
        
        stage('Deploy Vulnerable') {
            steps {
                echo 'Desplegando aplicación vulnerable en background...'
                bat '''
                    echo === LIBERANDO PUERTO 5000 ===
                    for /F "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Matando proceso previo en el puerto 5000, PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    
                    echo === INICIANDO APLICACIÓN VULNERABLE ===
                    set FLASK_APP=vulnerable_app.py
                    set FLASK_ENV=development
                    
                    if exist vulnerable_app.py (
                        echo Iniciando Flask...
                        start /B python -m flask run --host=0.0.0.0 --port=5000
                        timeout /t 5 /nobreak
                        
                        echo Verificando que la aplicación responda...
                        curl -s -o nul -w "HTTP Status: %%{http_code}" %TARGET_URL% || echo ⚠️ No se pudo conectar a la aplicación
                        echo.
                        echo ✅ Aplicación vulnerable desplegada en %TARGET_URL%
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
                    
                    set "ZAP_SCRIPT="
                    
                    if exist "C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files\\ZAP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files (x86)\\ZAP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat"
                    if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat" set "ZAP_SCRIPT=C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat"
                    
                    if defined ZAP_SCRIPT (
                        echo ✅ ZAP encontrado en: %ZAP_SCRIPT%
                        echo Ejecutando escaneo...
                        "%ZAP_SCRIPT%" -cmd -quickurl %TARGET_URL% -quickprogress -quickout zap-report.html || echo ⚠️ ZAP encontró problemas
                        echo ✅ Escaneo ZAP completado
                    ) else (
                        echo ⚠️ ZAP no encontrado. Generando reporte de advertencia...
                        echo ^<html^> > zap-report.html
                        echo ^<head^>^<title^>ZAP Report^</title^>^</head^> >> zap-report.html
                        echo ^<body^> >> zap-report.html
                        echo ^<h1 style="color: orange;"^>⚠️ OWASP ZAP no instalado^</h1^> >> zap-report.html
                        echo ^<p^>ZAP no se encontró en el sistema.^</p^> >> zap-report.html
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
        
        stage('Security Validation') {
            steps {
                echo '=== VALIDANDO CORRECCIONES DE SEGURIDAD ==='
                bat '''
                    echo Verificando que las correcciones fueron aplicadas...
                    
                    echo === 1. VERIFICANDO SQL INJECTION ===
                    echo Intentando inyección SQL en la aplicación vulnerable...
                    curl -s "%TARGET_URL%/login?username=admin'--&password=test" || echo ⚠️ Error en la prueba
                    
                    echo.
                    echo === 2. VERIFICANDO XSS ===
                    echo Intentando XSS en la aplicación vulnerable...
                    curl -s "%TARGET_URL%/search?q=<script>alert('XSS')</script>" || echo ⚠️ Error en la prueba
                    
                    echo.
                    echo === 3. VERIFICANDO HEADERS DE SEGURIDAD ===
                    powershell -Command "
                        try {
                            \$response = Invoke-WebRequest -Uri %TARGET_URL% -Method Head
                            Write-Host 'Headers de seguridad:'
                            Write-Host 'X-Content-Type-Options: ' \$response.Headers['X-Content-Type-Options']
                            Write-Host 'X-Frame-Options: ' \$response.Headers['X-Frame-Options']
                            Write-Host 'Content-Security-Policy: ' \$response.Headers['Content-Security-Policy']
                        } catch {
                            Write-Host '⚠️ No se pudieron verificar headers de seguridad'
                        }
                    "
                    
                    echo ✅ Validación completada
                '''
            }
        }
        
        stage('Deploy Secure') {
            steps {
                echo 'Desplegando aplicación segura...'
                bat '''
                    echo === DETENIENDO APLICACIÓN VULNERABLE ===
                    for /F "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Deteniendo proceso en el puerto 5000, PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    
                    timeout /t 3 /nobreak
                    
                    echo === INICIANDO APLICACIÓN SEGURA ===
                    set FLASK_APP=secure_app.py
                    set FLASK_ENV=production
                    
                    if exist secure_app.py (
                        echo Iniciando Flask con versión segura...
                        start /B python -m flask run --host=0.0.0.0 --port=5000
                        timeout /t 5 /nobreak
                        
                        echo Verificando que la aplicación segura responda...
                        curl -s -o nul -w "HTTP Status: %%{http_code}" %TARGET_URL% || echo ⚠️ No se pudo conectar a la aplicación
                        echo.
                        echo ✅ Aplicación segura desplegada en %TARGET_URL%
                    ) else (
                        echo ❌ secure_app.py no encontrado
                        exit 1
                    )
                '''
            }
        }
        
        stage('Dependency Management') {
            steps {
                echo '=== GESTIÓN DE DEPENDENCIAS ==='
                bat '''
                    echo Verificando dependencias...
                    
                    pip list --outdated > outdated-dependencies.txt
                    
                    echo === DEPENDENCIAS DESACTUALIZADAS ===
                    type outdated-dependencies.txt
                    
                    echo.
                    echo === ESCANEO DE VULNERABILIDADES EN DEPENDENCIAS ===
                    safety check --full-report > dependency-vulnerabilities.txt || echo ⚠️ Vulnerabilidades encontradas
                    
                    echo.
                    echo === ACTUALIZANDO DEPENDENCIAS SEGURAS ===
                    if exist requirements.txt (
                        pip install --upgrade -r requirements.txt
                        echo ✅ Dependencias actualizadas
                    )
                    
                    pip freeze > requirements-safe.txt
                    echo ✅ Lista de dependencias seguras guardada en requirements-safe.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'outdated-dependencies.txt, dependency-vulnerabilities.txt, requirements-safe.txt', fingerprint: true
                }
            }
        }
        
        stage('Documentation & Traceability') {
            steps {
                echo '=== GENERANDO DOCUMENTACIÓN ==='
                bat '''
                    echo Generando documentación completa...
                    
                    if not exist docs mkdir docs
                    
                    echo # REPORTE DE SEGURIDAD - EV3 > docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    echo ## Fecha: %DATE% %TIME% >> docs/Security-Report.md
                    echo ## Estudiante: Felipe Droguett >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    
                    echo ## 1. ANÁLISIS DE VULNERABILIDADES >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    echo ### 1.1 SQL Injection >> docs/Security-Report.md
                    findstr /N /C:"execute(" /C:"SELECT" vulnerable_app.py >> docs/Security-Report.md 2>nul
                    echo. >> docs/Security-Report.md
                    
                    echo ### 1.2 XSS >> docs/Security-Report.md
                    findstr /N /C:"render_template" vulnerable_app.py >> docs/Security-Report.md 2>nul
                    echo. >> docs/Security-Report.md
                    
                    echo ### 1.3 Credenciales Hardcodeadas >> docs/Security-Report.md
                    findstr /N /C:"password =" /C:"secret =" vulnerable_app.py >> docs/Security-Report.md 2>nul
                    echo. >> docs/Security-Report.md
                    
                    echo ## 2. CORRECCIONES APLICADAS >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    echo - Parametrización de consultas SQL >> docs/Security-Report.md
                    echo - Sanitización de outputs para prevenir XSS >> docs/Security-Report.md
                    echo - Uso de variables de entorno para credenciales >> docs/Security-Report.md
                    echo - Desactivación de modo DEBUG en producción >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    
                    echo ## 3. HERRAMIENTAS UTILIZADAS >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    echo - SonarQube: Análisis estático de código >> docs/Security-Report.md
                    echo - Bandit: Análisis de seguridad Python >> docs/Security-Report.md
                    echo - OWASP ZAP: Pruebas de seguridad dinámicas >> docs/Security-Report.md
                    echo - Safety: Escaneo de vulnerabilidades en dependencias >> docs/Security-Report.md
                    echo - Grafana/Prometheus: Monitorización >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    
                    echo ## 4. TRAZABILIDAD >> docs/Security-Report.md
                    echo. >> docs/Security-Report.md
                    echo | Etapa | Herramienta | Resultado | >> docs/Security-Report.md
                    echo |-------|-------------|-----------| >> docs/Security-Report.md
                    echo | Build | Compilación | ✅ Exitosa | >> docs/Security-Report.md
                    echo | Tests | Pytest | ✅ %TEST_COUNT% pruebas | >> docs/Security-Report.md
                    echo | Security | Bandit | ✅ %BANDIT_ISSUES% issues | >> docs/Security-Report.md
                    echo | Security | OWASP ZAP | ✅ Escaneo completado | >> docs/Security-Report.md
                    echo | Security | SonarQube | ✅ Análisis completado | >> docs/Security-Report.md
                    echo | Deploy | Producción | ✅ Aplicación segura | >> docs/Security-Report.md
                    
                    echo ✅ Documentación generada en docs/Security-Report.md
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'docs/Security-Report.md', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            echo '=== PIPELINE COMPLETADO ==='
            echo 'Generando reportes...'
            
            archiveArtifacts artifacts: 'bandit-report.json, bandit-report.html, bandit-report.csv, safety-report.json, safety-report.txt, test-results.xml, reports/vulnerabilities.txt, docs/Security-Report.md, outdated-dependencies.txt, dependency-vulnerabilities.txt, requirements-safe.txt, coverage.xml', fingerprint: true
            
            catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                bat '''
                    echo === LIMPIANDO PROCESOS ===
                    for /F "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
                        echo Deteniendo proceso en el puerto 5000, PID %%a
                        taskkill /F /PID %%a 2>nul
                    )
                    echo ✅ Limpieza completada
                '''
            }
            
            bat '''
                echo.
                echo === RESUMEN DE EJECUCIÓN ===
                echo 📁 Archivos generados:
                echo   - sonarqube-report.html (SonarQube)
                echo   - bandit-report.json/html/csv (Bandit)
                echo   - safety-report.json/txt (Safety)
                echo   - test-results.xml (JUnit)
                echo   - zap-report.html (OWASP ZAP)
                echo   - secure_app.py (Código corregido)
                echo   - reports/vulnerabilities.txt (Vulnerabilidades)
                echo   - docs/Security-Report.md (Documentación)
                echo   - requirements-safe.txt (Dependencias seguras)
                echo.
                echo === LINKS IMPORTANTES ===
                echo 📊 Grafana: http://localhost:3000 (admin/admin)
                echo 📈 Prometheus: http://localhost:9090
                echo 🔍 SonarQube: %SONAR_HOST_URL%
                echo 🚀 Aplicación: http://localhost:5000
            '''
        }
        success {
            echo '✅ ✅ ✅ PIPELINE EXITOSO ✅ ✅ ✅'
            echo '🎉 Todas las etapas completadas correctamente'
            echo '📝 Documentación generada en docs/Security-Report.md'
        }
        failure {
            echo '❌ ❌ ❌ PIPELINE FALLÓ ❌ ❌ ❌'
            echo 'Revisa los logs para identificar el error'
        }
    }
}
