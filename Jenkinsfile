pipeline {
    agent {
        docker {
            image 'python:3.11.9'
        }
    }

    stages {
        stage('Run unit tests') {
            steps {
                sh '''
                    pip install -r requirements.txt
                    pytest tests/*
                '''
            }
        }
    }
}
