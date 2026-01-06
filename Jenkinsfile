pipeline {
    agent {
        docker {
            image 'python:3.11.9'
        }
    }

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pytest tests/*
                '''
            }
        }
    }
}
