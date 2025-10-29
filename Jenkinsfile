pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'order-service'
        IMAGE_TAG = "v${BUILD_NUMBER}"
        KIND_CLUSTER = 'chaos-platform'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building ${DOCKER_IMAGE}:${IMAGE_TAG}"
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} ./services/order-service
                        docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }
        
        stage('Load Image to KIND') {
            steps {
                script {
                    echo "Loading image to KIND cluster"
                    sh "kind load docker-image ${DOCKER_IMAGE}:${IMAGE_TAG} --name ${KIND_CLUSTER}"
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes"
                    sh """
                        kubectl set image deployment/order-service order-service=${DOCKER_IMAGE}:${IMAGE_TAG}
                        kubectl rollout status deployment/order-service --timeout=120s
                    """
                }
            }
        }
        
        stage('Run Chaos Tests') {
            steps {
                script {
                    echo "Running chaos engineering tests"
                    sh """
                        cd kubernetes/chaos
                        chmod +x pod-killer.sh
                        
                        # Run pod killer and capture recovery time
                        ./pod-killer.sh > chaos_result.txt 2>&1
                        
                        # Extract recovery time
                        RECOVERY_TIME=\$(grep "Recovery time:" chaos_result.txt | awk '{print \$3}')
                        echo "Recovery Time: \${RECOVERY_TIME} seconds"
                        
                        # Fail if recovery > 30 seconds
                        if [ \${RECOVERY_TIME} -gt 30 ]; then
                            echo "FAIL: Recovery time exceeded 30 seconds threshold"
                            exit 1
                        fi
                        
                        echo "PASS: Recovery within acceptable threshold"
                    """
                }
            }
        }
        
        stage('Verify Service Health') {
            steps {
                script {
                    echo "Verifying service health"
                    sh """
                        kubectl get pods -l app=order-service
                        kubectl get svc order-service
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Check logs above.'
        }
        always {
            echo 'Cleaning up...'
        }
    }
}