pipeline {
    agent any

    stages {
        stage('Clean Repo') {
            steps {
                echo '🧹 Removing previous clone if exists...'
                sh 'rm -rf eb_smartcart_containers'
            }
        }

        stage('Clone Repo') {
            steps {
                echo '🔽 Cloning repo...'
                sh 'git clone https://github.com/ebairachtari/eb_smartcart_containers.git'
            }
        }

        stage('Build & Deploy Containers') {
            steps {
                echo '🚀 Deploying containers from docker-compose.yml...'
                dir('eb_smartcart_containers') {
                    sh '''
                        echo "🧹 Stopping & removing containers..."
                        docker-compose down || true

                        echo "🧹 Deleting leftover containers (if exist)..."
                        docker rm -f smartcart_mongo smartcart_ml_service smartcart_backend smartcart_frontend smartcart_nodered || true

                        echo "🧹 Pruning volumes..."
                        docker volume prune -f || true

                        echo "🚀 Starting fresh containers..."
                        docker-compose up -d --build
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ SUCCESS: SmartCart containers are up and healthy!'
        }
        failure {
            echo '❌ FAILURE: Something went wrong during the pipeline.'
        }
    }
}
