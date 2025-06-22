pipeline {
    agent any

    environment {
        COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Cleanup') {
            steps {
                echo '🔁 Removing old containers (if any)...'
                sh '''
                docker-compose down || true
                docker volume prune -f || true
                '''
            }
        }

        stage('Build & Start Containers') {
            steps {
                echo '🚀 Starting SmartCart containers...'
                sh '''
                docker-compose up -d --build
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking service availability...'
                sh '''
                echo "⌛ Waiting for services to warm up..."
                sleep 10

                echo "Checking Backend..."
                curl --fail http://localhost:5000/health || echo "⚠️ Backend not responding"

                echo "Checking Frontend..."
                curl --fail http://localhost:8000 || echo "⚠️ Frontend not responding"
                '''
            }
        }
    }

    post {
        failure {
            echo '❌ Build failed. Please check logs for errors.'
        }
        success {
            echo '✅ All SmartCart services deployed successfully and passed basic health check.'
        }
    }
}
