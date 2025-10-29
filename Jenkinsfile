pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'order-service'
        IMAGE_TAG = "v${BUILD_NUMBER}"
        REGISTRY = 'registry.default.svc.cluster.local:5000'
        FULL_IMAGE = "${REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG}"
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
                    echo "Building ${FULL_IMAGE}"
                    sh """
                        docker build -t ${FULL_IMAGE} ./services/order-service
                    """
                }
            }
        }
        
        stage('Push to Registry') {
            steps {
                script {
                    echo "Pushing to registry"
                    sh """
                        docker push ${FULL_IMAGE}
                    """
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes"
                    sh """
                        kubectl set image deployment/order-service \
                            order-service=${FULL_IMAGE} \
                            --record
                        
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
                        
                        ./pod-killer.sh > chaos_result.txt 2>&1
                        
                        RECOVERY_TIME=\$(grep "Recovery time:" chaos_result.txt | awk '{print \$3}')
                        echo "Recovery Time: \${RECOVERY_TIME} seconds"
                        
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