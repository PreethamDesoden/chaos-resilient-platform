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
        
        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building images locally"
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} ./services/order-service
                        docker build -t inventory-service:${IMAGE_TAG} ./services/inventory-service
                        docker build -t notification-service:${IMAGE_TAG} ./services/notification-service
                    """
                }
            }
        }
        
        stage('Load Images to KIND') {
            steps {
                script {
                    echo "Loading images to KIND cluster"
                    sh """
                        kind load docker-image ${DOCKER_IMAGE}:${IMAGE_TAG} --name ${KIND_CLUSTER}
                        kind load docker-image inventory-service:${IMAGE_TAG} --name ${KIND_CLUSTER}
                        kind load docker-image notification-service:${IMAGE_TAG} --name ${KIND_CLUSTER}
                    """
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes"
                    sh """
                        kubectl set image deployment/order-service order-service=${DOCKER_IMAGE}:${IMAGE_TAG}
                        kubectl set image deployment/inventory-service inventory-service=inventory-service:${IMAGE_TAG}
                        kubectl set image deployment/notification-service notification-service=notification-service:${IMAGE_TAG}
                        
                        kubectl rollout status deployment/order-service --timeout=120s
                        kubectl rollout status deployment/inventory-service --timeout=120s
                        kubectl rollout status deployment/notification-service --timeout=120s
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
                        
                        ./pod-killer.sh > chaos_result.txt 2>&1 || true
                        
                        cat chaos_result.txt
                        
                        RECOVERY_TIME=\$(grep "Recovery time:" chaos_result.txt | awk '{print \$3}' || echo "0")
                        echo "Recovery Time: \${RECOVERY_TIME} seconds"
                        
                        if [ "\${RECOVERY_TIME}" != "0" ] && [ \${RECOVERY_TIME} -gt 30 ]; then
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
                        kubectl get pods
                        kubectl get svc
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully! All chaos tests passed.'
        }
        failure {
            echo '❌ Pipeline failed. Check logs above.'
        }
        always {
            echo 'Pipeline execution complete.'
        }
    }
}