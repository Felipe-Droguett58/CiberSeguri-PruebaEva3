pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
        ZAP_PORT = '8080'
        TARGET_URL = 'http://localhost:5000'  // Corregido: comilla faltante
        // Definir el ID de la credencial como variable para mejor mantenimiento
        GITHUB_CREDENTIALS_ID = 'github-token'  // Cambia esto por el ID que usaste en Jenkins
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Clonando repositorio con credenciales de GitHub...'
                // Opción 1: Usar checkout con credenciales explícitas
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/tu-usuario/tu-repositorio.git',  // Cambia por tu URL
                        credentialsId: env.GITHUB_CREDENTIALS_ID
                    ]]
                ])
                
                // Opción 2: Alternativa más simple (descomenta si prefieres)
                // git branch: 'main', 
                //     url: 'https://github.com/tu-usuario/tu-repositorio.git',
                //     credentialsId: env.GITHUB_CREDENTIALS_ID
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo 'Configurando entorno Python...'
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python create_db.py
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Construyendo aplicación...'
                sh 'python -m py_compile vulnerable_app.py'
            }
        }
        
        stage('Test') {
            steps {
                echo 'Ejecutando pruebas unitarias...'
                sh '''
                    pip install pytest
                    pytest tests/ -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    // Archivar resultados de pruebas para visualización en Jenkins
                    junit 'test-results.xml'
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                echo 'Ejecutando análisis de seguridad estático...'
                sh '''
                    pip install bandit safety
                    bandit -r . -f json -o bandit-report.json || true  # No falla el pipeline si hay hallazgos
                    safety check || true  # No falla el pipeline si hay hallazgos
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando aplicación en background...'
                // Mejor práctica: usar nohup para mantener el proceso
                sh '''
                    export FLASK_APP=vulnerable_app.py
                    export FLASK_ENV=development
                    nohup flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &
                    sleep 5  # Esperar a que la aplicación inicie
                    echo "Aplicación desplegada en $TARGET_URL"
                '''
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                echo 'Ejecutando OWASP ZAP scan...'
                sh '''
                    # Verificar si la aplicación está corriendo
                    curl -s --retry 5 --retry-delay 2 $TARGET_URL || exit 1
                    
                    # Instalar OWASP ZAP según el sistema operativo
                    if command -v apt-get &> /dev/null; then
                        apt-get update -qq && apt-get install -y -qq owasp-zap
                    elif command -v brew &> /dev/null; then
                        brew install owasp-zap
                    elif command -v docker &> /dev/null; then
                        # Usar Docker como alternativa
                        docker run --rm -v $(pwd):/zap/wrk:rw -t owasp/zap2docker-stable \
                            zap-full-scan.py -t $TARGET_URL -r zap-report.html
                    else
                        echo "No se pudo instalar OWASP ZAP"
                        exit 1
                    fi
                    
                    # Ejecutar ZAP si se instaló correctamente
                    if command -v zap-full-scan.py &> /dev/null; then
                        zap-full-scan.py -t $TARGET_URL -r zap-report.html || true
                    fi
                '''
            }
            post {
                always {
                    // Archivar reporte de ZAP si existe
                    archiveArtifacts artifacts: 'zap-report.html', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline completado. Generando reportes...'
            // Archivar todos los artefactos generados
            archiveArtifacts artifacts: 'bandit-report.json, test-results.xml', fingerprint: true
            
            // Limpiar procesos en background
            sh '''
                pkill -f "flask run" || true
                pkill -f "zap" || true
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
