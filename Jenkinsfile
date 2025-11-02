pipeline {
    agent any
    
    options {
        timeout(time: 1, unit: 'HOURS')
        retry(3)
        disableConcurrentBuilds()
    }
    
    environment {
        // Azure credentials from Jenkins
        AZURE_CREDENTIALS = credentials('azure-credentials')
        AZURE_CLIENT_ID = "${AZURE_CREDENTIALS_USR}"
        AZURE_CLIENT_SECRET = "${AZURE_CREDENTIALS_PSW}"
        AZURE_TENANT_ID = credentials('azure-tenant-id')
        AZURE_SUBSCRIPTION_ID = credentials('azure-subscription-id')
        
        // ACR credentials
        ACR_CREDENTIALS = credentials('acr-credentials')
        ACR_USERNAME = "${ACR_CREDENTIALS_USR}"
        ACR_PASSWORD = "${ACR_CREDENTIALS_PSW}"
        
        // Storage credentials
        STORAGE_CREDENTIALS = credentials('storage-credentials')
        STORAGE_ACCOUNT_NAME = "${STORAGE_CREDENTIALS_USR}"
        STORAGE_ACCOUNT_KEY = "${STORAGE_CREDENTIALS_PSW}"
        
        // API Keys
        API_KEYS = credentials('api-keys')
        OPENAI_API_KEY = "${API_KEYS_openai}"
        GOOGLE_API_KEY = "${API_KEYS_google}"
        GROQ_API_KEY = "${API_KEYS_groq}"
        TAVILY_API_KEY = "${API_KEYS_tavily}"
        LLM_PROVIDER = "${API_KEYS_provider}"
        
        // App configuration
        APP_RESOURCE_GROUP = 'research-report-app-rg'
        APP_NAME = 'research-report-app'
        ACR_NAME = 'researchreportacr'
        IMAGE_NAME = 'research-report-app'
        CONTAINER_ENV = 'research-report-env'
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    try {
                        echo 'Checking out code...'
                        deleteDir()
                        git branch: 'main',
                            url: 'https://github.com/Shubh-kesh/automated-research-report-generation.git',
                            credentialsId: 'github-credentials'
                    } catch (Exception e) {
                        error "Failed to checkout code: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Setup Python') {
            steps {
                script {
                    try {
                        echo 'Setting up Python environment...'
                        sh '''
                            python3 -m venv .venv
                            . .venv/bin/activate
                            python3 -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } catch (Exception e) {
                        error "Failed to setup Python: ${e.getMessage()}"
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
                            . .venv/bin/activate
                            python -m pytest tests/ --junitxml=test-results.xml
                        '''
                    } catch (Exception e) {
                        error "Tests failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Azure Login') {
            steps {
                script {
                    try {
                        echo 'Logging in to Azure...'
                        sh '''
                            az login --service-principal \
                                -u $AZURE_CLIENT_ID \
                                -p $AZURE_CLIENT_SECRET \
                                --tenant $AZURE_TENANT_ID
                            
                            az account set --subscription $AZURE_SUBSCRIPTION_ID
                        '''
                    } catch (Exception e) {
                        error "Azure login failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Deploy to Azure') {
            steps {
                script {
                    try {
                        echo 'Deploying to Azure Container Apps...'
                        sh '''
                            # Get latest image tag
                            IMAGE_TAG=$(az acr repository show-tags \
                                --name $ACR_NAME \
                                --repository $IMAGE_NAME \
                                --orderby time_desc \
                                --output tsv \
                                | head -n 1)
                                
                            if [ -z "$IMAGE_TAG" ]; then
                                echo "No image found in ACR"
                                exit 1
                            fi
                            
                            # Deploy container app
                            az containerapp create \
                                --name $APP_NAME \
                                --resource-group $APP_RESOURCE_GROUP \
                                --environment $CONTAINER_ENV \
                                --image ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG} \
                                --registry-server ${ACR_NAME}.azurecr.io \
                                --registry-username $ACR_USERNAME \
                                --registry-password $ACR_PASSWORD \
                                --target-port 8000 \
                                --ingress external \
                                --min-replicas 1 \
                                --max-replicas 3 \
                                --cpu 1.0 \
                                --memory 2.0Gi \
                                --env-vars LLM_PROVIDER=$LLM_PROVIDER
                                
                            # Set secrets
                            az containerapp secret set \
                                --name $APP_NAME \
                                --resource-group $APP_RESOURCE_GROUP \
                                --secrets \
                                    openai-api-key=$OPENAI_API_KEY \
                                    google-api-key=$GOOGLE_API_KEY \
                                    groq-api-key=$GROQ_API_KEY \
                                    tavily-api-key=$TAVILY_API_KEY
                        '''
                    } catch (Exception e) {
                        error "Deployment failed: ${e.getMessage()}"
                    }
                }
            }
        }
        
        stage('Verify') {
            steps {
                script {
                    try {
                        echo 'Verifying deployment...'
                        sh '''
                            APP_URL=$(az containerapp show \
                                --name $APP_NAME \
                                --resource-group $APP_RESOURCE_GROUP \
                                --query properties.configuration.ingress.fqdn -o tsv)
                            
                            echo "Waiting for application startup..."
                            sleep 30
                            
                            if curl -f -s https://$APP_URL/health; then
                                echo "Application is healthy"
                            else
                                echo "Health check failed"
                                exit 1
                            fi
                        '''
                    } catch (Exception e) {
                        error "Verification failed: ${e.getMessage()}"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            emailext (
                subject: "SUCCESS: ${currentBuild.fullDisplayName}",
                body: "Pipeline completed successfully.\nCheck: ${BUILD_URL}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        failure {
            echo 'Pipeline failed!'
            emailext (
                subject: "FAILED: ${currentBuild.fullDisplayName}",
                body: "Pipeline failed.\nCheck: ${BUILD_URL}",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        always {
            echo 'Cleaning up...'
            sh '''
                az logout || true
                deactivate || true
            '''
            cleanWs()
        }
    }
}