pipeline {
    agent any

    stages {
        stage('Start containers') {
            steps {
                dir('eb_smartcart-containers') {
                    sh 'docker-compose up -d --build'
                }
            }
        }

        stage('Wait for services') {
            steps {
                echo '⌛ Waiting for containers to get ready...'
                sh 'sleep 15'
            }
        }

        stage('Health check: Backend') {
            steps {
                sh 'curl --fail http://localhost:5000/health || exit 1'
            }
        }

        stage('Health check: ML Service') {
            steps {
                sh 'curl --fail http://localhost:5001/health || exit 1'
            }
        }

        stage('Health check: Frontend') {
            steps {
                sh 'curl --fail http://localhost:8501 || exit 1'
            }
        }
    }

    post {
        success {
            echo '✅ All containers started and passed health checks.'
        }
        failure {
            echo '❌ Something failed!'
        }
    }
}

