pipeline {
    agent {
        docker {
            // Use the same python image as the application release
            image 'python:3.11.9'
        }
    }

    stages {
        
        // Checkout stage to pull the latest code from SCM (e.g., Git)
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        // Run unit tests using pytest after installing dependencies
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
