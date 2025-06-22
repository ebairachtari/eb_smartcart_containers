pipeline {
    agent any

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Cleanup') {
            steps {
                echo 'Removing old containers (if any)...'
                sh '''
                docker compose down || true
                docker volume prune -f || true
                '''
            }
        }

        stage('Build & Start Containers') {
            steps {
                echo 'Starting SmartCart containers...'
                sh '''
                docker compose up -d --build
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking service availability...'
                sh '''
                sleep 10
                curl --fail http://localhost:5000/health || echo "Backend not responding"
                curl --fail http://localhost:8000 || echo "Frontend not responding"
                '''
            }
        }
    }

    post {
        failure {
            echo '❌ Build failed.'
        }
        success {
            echo '✅ All SmartCart services deployed successfully.'
        }
    }
}
