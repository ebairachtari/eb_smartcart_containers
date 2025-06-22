pipeline {
    agent any
    stages {
        stage('Start') {
            steps {
                echo '✅ Jenkins pipeline started'
            }
        }
        stage('Simulate Test') {
            steps {
                sh 'echo Hello from SmartCart!'
            }
        }
        stage('Finish') {
            steps {
                echo '🎉 All steps finished successfully'
            }
        }
    }
}
