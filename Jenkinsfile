pipeline {
    agent any
    
    options {
        // Add timeout and retry options
        timeout(time: 1, unit: 'HOURS')
        retry(3)
    }
    
    environment {
        // ...existing environment variables...
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    try {
                        echo 'Checking out code from Git...'
                        deleteDir()
                        git branch: 'main',
                            url: 'https://github.com/sunnysavita10/automated-research-report-generation.git',
                            credentialsId: 'github-credentials' // Add this credential in Jenkins
                    } catch (Exception e) {
                        error "Failed to checkout code: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    try {
                        echo 'Setting up Python environment...'
                        sh '''
                            python3 --version || exit 1
                            python3 -m venv venv
                            . venv/bin/activate
                            python3 -m pip install --upgrade pip
                        '''
                    } catch (Exception e) {
                        error "Failed to setup Python: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    try {
                        echo 'Installing Python dependencies...'
                        sh '''
                            . venv/bin/activate
                            pip3 install -r requirements.txt
                        '''
                    } catch (Exception e) {
                        error "Failed to install dependencies: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    try {
                        echo 'Running tests...'
                        sh '''
                            . venv/bin/activate
                            python3 -c "from research_and_analyst.api.main import app; print('Imports successful')"
                        '''
                    } catch (Exception e) {
                        error "Tests failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Login to Azure') {
            steps {
                script {
                    try {
                        echo 'Logging in to Azure...'
                        withCredentials([
                            string(credentialsId: 'azure-client-id', variable: 'AZURE_CLIENT_ID'),
                            string(credentialsId: 'azure-client-secret', variable: 'AZURE_CLIENT_SECRET'),
                            string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID'),
                            string(credentialsId: 'azure-subscription-id', variable: 'AZURE_SUBSCRIPTION_ID')
                        ]) {
                            sh '''
                                az login --service-principal \
                                    -u $AZURE_CLIENT_ID \
                                    -p $AZURE_CLIENT_SECRET \
                                    --tenant $AZURE_TENANT_ID || exit 1
                                
                                az account set --subscription $AZURE_SUBSCRIPTION_ID || exit 1
                            '''
                        }
                    } catch (Exception e) {
                        error "Failed to login to Azure: ${e.getMessage()}"
                    }
                }
            }
        }
        
        // ...existing stages...
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            // Cleanup
            sh 'deactivate || true'
            cleanWs()
        }
        failure {
            echo 'Pipeline failed! Check the logs for details.'
            // Send notification
            emailext (
                subject: "Pipeline Failed: ${currentBuild.fullDisplayName}",
                body: "Check console output at ${BUILD_URL} for details.",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
            sh 'deactivate || true'
            cleanWs()
        }
        always {
            echo 'Performing cleanup...'
            sh '''
                az logout || true
                deactivate || true
            '''
            cleanWs()
        }
    }
}