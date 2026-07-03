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
                    pip install -r requirements.txt
                    python create_db.py
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Construyendo aplicación...'
                bat 'python -m py_compile vulnerable_app.py'
            }
        }
        
        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias...'
                bat '''
                    pip install pytest
                    pytest tests/ -v --junitxml=test-results.xml
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
                    bandit -r . -f json -o bandit-report.json || exit 0
                    safety check || exit 0
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando aplicación en background...'
                bat '''
                    set FLASK_APP=vulnerable_app.py
                    set FLASK_ENV=development
                    start /B flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1
                    timeout /t 5 /nobreak
                    echo Aplicación desplegada en %TARGET_URL%
                '''
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                echo 'Ejecutando OWASP ZAP scan...'
                bat '''
                    echo Verificando si la aplicación está corriendo...
                    curl -s --retry 5 --retry-delay 2 %TARGET_URL% || exit 1
                    
                    echo Intentando instalar OWASP ZAP...
                    where choco >nul 2>nul
                    if %errorlevel% equ 0 (
                        choco install owasp-zap -y
                    ) else (
                        where winget >nul 2>nul
                        if %errorlevel% equ 0 (
                            winget install OWASP.ZAP -h
                        ) else (
                            echo OWASP ZAP no está instalado y no hay gestor de paquetes disponible
                            echo Descarga e instala manualmente desde: https://www.zaproxy.org/download/
                            echo O usa Docker Desktop con: docker run --rm -v %cd%:/zap/wrk:rw -t owasp/zap2docker-stable zap-full-scan.py -t %TARGET_URL% -r zap-report.html
                            exit 1
                        )
                    )
                    
                    echo Ejecutando ZAP scan...
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html || exit 0
                    ) else if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html || exit 0
                    ) else (
                        echo No se encontró zap-full-scan.py. Buscando en PATH...
                        where zap-full-scan.py >nul 2>nul
                        if %errorlevel% equ 0 (
                            zap-full-scan.py -t %TARGET_URL% -r zap-report.html || exit 0
                        ) else (
                            echo No se pudo ejecutar ZAP. Instálalo manualmente.
                            exit 1
                        )
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
            echo 'Pipeline completado. Generando reportes...'
            archiveArtifacts artifacts: 'bandit-report.json, test-results.xml', fingerprint: true
            
            bat '''
                echo Limpiando procesos en background...
                taskkill /F /IM python.exe /FI "WINDOWTITLE eq flask*" 2>nul || exit 0
                taskkill /F /IM java.exe /FI "WINDOWTITLE eq ZAP*" 2>nul || exit 0
            '''
        }
        success {
            echo '✅ Pipeline ejecutado exitosamente'
        }
        failure {
            echo '❌ Pipeline falló. Revisa los logs para más detalles.'
        }
        unstable {
            echo '⚠️ Pipeline inestable. Algunas pruebas o escaneos encontraron problemas.'
        }
    }
}
