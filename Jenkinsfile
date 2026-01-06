pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run unit tests') {
            steps {
                script {
                    docker.image('python:3.11.9').inside {
                        sh '''
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                            pytest tests/*
                        '''
                    }
                }
            }
        }
    }
}
