#!/bin/bash

# Deployment script for Sanctions Screening Platform
# Author: Eon (Himanshu Shekhar)
# Email: eonhimanshu@gmail.com
# GitHub: https://github.com/eonn/sanctions-screening
# Created: 2024

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists kubectl; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    if docker build -t sanctions-screening:latest .; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to deploy to Kubernetes
deploy_k8s() {
    print_status "Deploying to Kubernetes..."
    
    # Apply all manifests
    if kubectl apply -f k8s/; then
        print_success "Kubernetes manifests applied successfully"
    else
        print_error "Failed to apply Kubernetes manifests"
        exit 1
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    print_status "Waiting for deployments to be ready..."
    
    # Wait for namespace
    kubectl wait --for=condition=Active namespace/sanctions-screening --timeout=60s
    
    # Wait for database
    kubectl wait --for=condition=Available deployment/postgres -n sanctions-screening --timeout=300s
    
    # Wait for Redis
    kubectl wait --for=condition=Available deployment/redis -n sanctions-screening --timeout=300s
    
    # Wait for RabbitMQ
    kubectl wait --for=condition=Available deployment/rabbitmq -n sanctions-screening --timeout=300s
    
    # Wait for Kafka
    kubectl wait --for=condition=Available deployment/zookeeper -n sanctions-screening --timeout=300s
    kubectl wait --for=condition=Available deployment/kafka -n sanctions-screening --timeout=300s
    
    # Wait for application
    kubectl wait --for=condition=Available deployment/sanctions-screening-app -n sanctions-screening --timeout=300s
    
    # Wait for nginx
    kubectl wait --for=condition=Available deployment/nginx -n sanctions-screening --timeout=300s
    
    print_success "All deployments are ready"
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    
    # Show pods
    kubectl get pods -n sanctions-screening
    
    echo ""
    print_status "Services:"
    kubectl get services -n sanctions-screening
    
    echo ""
    print_status "Persistent Volume Claims:"
    kubectl get pvc -n sanctions-screening
}

# Function to show access information
show_access_info() {
    print_status "Access Information:"
    echo ""
    
    # Get service information
    local nginx_service=$(kubectl get service nginx-service -n sanctions-screening -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    local app_service=$(kubectl get service sanctions-screening-service -n sanctions-screening -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    
    if [ -n "$nginx_service" ]; then
        print_success "Application accessible at: http://$nginx_service"
    else
        print_warning "LoadBalancer IP not available. Use port forwarding:"
        echo "  kubectl port-forward -n sanctions-screening service/nginx-service 8080:80"
        echo "  Then access: http://localhost:8080"
    fi
    
    if [ -n "$app_service" ]; then
        print_success "API accessible at: http://$app_service:8000"
    else
        print_warning "API LoadBalancer IP not available. Use port forwarding:"
        echo "  kubectl port-forward -n sanctions-screening service/sanctions-screening-service 8000:8000"
        echo "  Then access: http://localhost:8000"
    fi
    
    echo ""
    print_status "Useful commands:"
    echo "  View logs: kubectl logs -f deployment/sanctions-screening-app -n sanctions-screening"
    echo "  Check health: kubectl get pods -n sanctions-screening"
    echo "  Access shell: kubectl exec -it <pod-name> -n sanctions-screening -- /bin/bash"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up deployment..."
    
    if kubectl delete namespace sanctions-screening; then
        print_success "Deployment cleaned up successfully"
    else
        print_error "Failed to cleanup deployment"
        exit 1
    fi
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            build_image
            deploy_k8s
            wait_for_deployment
            show_status
            show_access_info
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [deploy|status|cleanup|help]"
            echo ""
            echo "Commands:"
            echo "  deploy  - Build image and deploy to Kubernetes (default)"
            echo "  status  - Show deployment status"
            echo "  cleanup - Remove all resources"
            echo "  help    - Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

