pipeline {
    agent any

    stages {
        stage('Run unit tests in Docker') {
            agent {
                docker {
                    image 'python:3.11.9'
                }
            }
            steps {
                checkout scm
                sh '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pytest tests/*
                '''
            }
        }
    }
}
