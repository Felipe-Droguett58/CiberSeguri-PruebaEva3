pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        DB_PATH = 'database.db'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Clonando repositorio...'
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo 'Configurando entorno Python...'
                sh '''
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
                    pytest tests/ -v
                '''
            }
        }
        
        stage('Security Scan') {
            steps {
                echo 'Ejecutando análisis de seguridad estático...'
                sh '''
                    pip install bandit safety
                    bandit -r . -f json -o bandit-report.json
                    safety check
                '''
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Desplegando aplicación...'
                sh '''
                    export FLASK_APP=vulnerable_app.py
                    flask run --host=0.0.0.0 --port=5000 &
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline completado. Generando reportes...'
            archiveArtifacts artifacts: 'bandit-report.json'
        }
    }
}
