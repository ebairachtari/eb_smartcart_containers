pipeline {
    agent any

    stages {
        stage('Clone') {
            steps {
                echo '🧹 Cleaning old clone (if exists)...'
                sh 'rm -rf eb_smartcart_containers'
                echo '🔽 Cloning repo...'
                sh 'git clone https://github.com/ebairachtari/eb_smartcart_containers.git'
            }
        }

        stage('Cleanup') {
            steps {
                echo '🔁 Removing old containers (if any)...'
                dir('eb_smartcart_containers') {
                    sh '''
                    docker-compose -f docker-compose.jenkins.yml down || true
                    docker volume prune -f || true
                    '''
                }
            }
        }

        stage('Build & Start Containers') {
            steps {
                echo '🚀 Starting SmartCart containers from docker-compose.jenkins.yml...'
                dir('eb_smartcart_containers') {
                    sh '''
                    docker-compose -f docker-compose.jenkins.yml up -d --build
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking service availability...'
                dir('eb_smartcart_containers') {
                    sh '''
                    sleep 10
                    echo "Checking Backend..."
                    curl --fail http://localhost:5000/health || echo "⚠️ Backend not responding"
                    echo "Checking Frontend..."
                    curl --fail http://localhost:8000 || echo "⚠️ Frontend not responding"
                    '''
                }
            }
        }
    }

    post {
        failure {
            echo '❌ Build failed.'
        }
        success {
            echo '✅ SmartCart deployed with docker-compose.jenkins.yml!'
        }
    }
}
