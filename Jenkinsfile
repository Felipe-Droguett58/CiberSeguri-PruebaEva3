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
                    bandit -r . -f json -o bandit-report.json
                    safety check
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando aplicación en background...'
                bat '''
                    set FLASK_APP=vulnerable_app.py
                    set FLASK_ENV=development
                    start /B flask run --host=0.0.0.0 --port=5000
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
                    curl -s --retry 5 --retry-delay 2 %TARGET_URL%
                    
                    echo Intentando ejecutar OWASP ZAP...
                    
                    REM Buscar ZAP en ubicaciones comunes de Windows
                    if exist "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        echo Usando ZAP desde Program Files...
                        "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html
                    ) else if exist "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" (
                        echo Usando ZAP desde Program Files (x86)...
                        "C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html
                    ) else (
                        echo ZAP no encontrado. Instalando con Chocolatey...
                        where choco
                        if %errorlevel% equ 0 (
                            choco install owasp-zap -y
                            "C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap-full-scan.py" -t %TARGET_URL% -r zap-report.html
                        ) else (
                            echo ZAP no está instalado. Descarga manual desde: https://www.zaproxy.org/download/
                            echo O instala Chocolatey y luego ejecuta: choco install owasp-zap -y
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
                taskkill /F /IM python.exe 2>nul
                taskkill /F /IM java.exe 2>nul
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
