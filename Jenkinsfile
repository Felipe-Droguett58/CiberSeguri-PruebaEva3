pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
        ZAP_PORT = '8080'
        APP_PORT = '5000'
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
                script {
                    // Antes de arrancar, liberar el puerto 5000 si algo quedó pegado
                    // de un build anterior (matando SOLO ese proceso, no todo java/python)
                    powershell '''
                        $existing = Get-NetTCPConnection -LocalPort $env:APP_PORT -ErrorAction SilentlyContinue |
                                    Select-Object -ExpandProperty OwningProcess -Unique
                        if ($existing) {
                            foreach ($procId in $existing) {
                                Write-Host "Liberando puerto $env:APP_PORT, matando PID $procId"
                                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                            }
                        } else {
                            Write-Host "Puerto $env:APP_PORT libre, nada que limpiar"
                        }
                    '''

                    // Iniciar Flask usando PowerShell, guardando el PID exacto
                    // en un archivo para poder limpiarlo de forma segura después
                    powershell '''
                        Write-Host "=== INICIANDO APLICACIÓN ==="
                        $env:FLASK_APP = "vulnerable_app.py"
                        $env:FLASK_ENV = "development"

                        if (Test-Path "vulnerable_app.py") {
                            Write-Host "Iniciando Flask..."

                            $proc = Start-Process python -ArgumentList "-m", "flask", "run", "--host=0.0.0.0", "--port=5000" -WindowStyle Minimized -PassThru
                            $proc.Id | Out-File -FilePath "flask_pid.txt" -Encoding ascii

                            Start-Sleep -Seconds 8

                            Write-Host "Verificando que la aplicación responda..."
                            try {
                                $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 5
                                Write-Host "HTTP Status: $($response.StatusCode)"
                            } catch {
                                Write-Host "⚠️ No se pudo conectar a la aplicación"
                            }
                            Write-Host ""
                            Write-Host "✅ Aplicación desplegada en http://localhost:5000 (PID $($proc.Id))"
                        } else {
                            Write-Host "❌ vulnerable_app.py no encontrado"
                            exit 1
                        }
                    '''
                }
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

                    set ZAP_FOUND=0
                    set ZAP_SCRIPT=

                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        set ZAP_FOUND=1
                        set ZAP_SCRIPT=C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py
                    )
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat" (
                        set ZAP_FOUND=1
                        set ZAP_SCRIPT=C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat
                    )
                    if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        set ZAP_FOUND=1
                        set ZAP_SCRIPT=C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py
                    )
                    if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat" (
                        set ZAP_FOUND=1
                        set ZAP_SCRIPT=C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat
                    )

                    if %ZAP_FOUND% equ 1 (
                        echo ✅ ZAP encontrado en: %ZAP_SCRIPT%
                        echo Ejecutando escaneo...

                        echo %ZAP_SCRIPT% | find ".py" >nul
                        if %errorlevel% equ 0 (
                            python %ZAP_SCRIPT% -t %TARGET_URL% -r zap-report.html || echo ⚠️ ZAP encontró problemas
                        ) else (
                            %ZAP_SCRIPT% -cmd -quickurl %TARGET_URL% -quickprogress -quickout zap-report.html || echo ⚠️ ZAP encontró problemas
                        )
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

            archiveArtifacts artifacts: 'bandit-report.json, test-results.xml', fingerprint: true, allowEmptyArchive: true

            // Limpieza SEGURA: solo mata el proceso Flask que este mismo build
            // lanzó (por PID guardado), nunca procesos java.exe/python.exe genéricos.
            // Matar java.exe a ciegas mata al propio Jenkins si corre sobre Windows.
            powershell '''
                Write-Host "=== LIMPIANDO PROCESOS ==="
                if (Test-Path "flask_pid.txt") {
                    $procId = Get-Content "flask_pid.txt"
                    try {
                        Stop-Process -Id $procId -Force -ErrorAction Stop
                        Write-Host "✅ Proceso Flask (PID $procId) detenido"
                    } catch {
                        Write-Host "⚠️ No se pudo detener el PID $procId (puede que ya no exista)"
                    }
                    Remove-Item "flask_pid.txt" -ErrorAction SilentlyContinue
                } else {
                    Write-Host "No hay flask_pid.txt, nada que limpiar"
                }
                Write-Host "✅ Limpieza completada"
            '''

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
