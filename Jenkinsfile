pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = "smartcart"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Cleanup old containers') {
            steps {
                echo "🔁 Removing old containers (if any)..."
                sh '''
                    docker rm -f ${COMPOSE_PROJECT_NAME}_mongo || true
                    docker rm -f ${COMPOSE_PROJECT_NAME}_ml_service || true
                    docker rm -f ${COMPOSE_PROJECT_NAME}_jenkins || true
                    docker rm -f ${COMPOSE_PROJECT_NAME}_backend || true
                    docker rm -f ${COMPOSE_PROJECT_NAME}_frontend || true
                    docker volume prune -f || true
                '''
            }
        }

        stage('Start containers') {
            steps {
                dir('eb_smartcart-containers') {
                    sh 'docker-compose down || true'
                    sh 'docker-compose up -d --build'
                }
            }
        }

        stage('Wait for services') {
            steps {
                echo '⏳ Giving services some time to boot...'
                sleep 10
            }
        }

        stage('Health check: Backend') {
            steps {
                sh 'curl -f http://localhost:5000/health || exit 1'
            }
        }

        stage('Health check: ML Service') {
            steps {
                sh 'curl -f http://localhost:5001/health || exit 1'
            }
        }

        stage('Health check: Frontend') {
            steps {
                sh 'curl -f http://localhost:8501 || exit 1'
            }
        }
    }

    post {
        failure {
            echo '❌ Something failed!'
        }
        success {
            echo '✅ Build and deployment successful!'
        }
    }
}
