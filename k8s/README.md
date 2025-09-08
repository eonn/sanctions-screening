# Kubernetes Deployment for Sanctions Screening Platform

This directory contains Kubernetes manifests for deploying the Sanctions Screening Platform.

## Author
**Eon (Himanshu Shekhar)**  
Email: eonhimanshu@gmail.com  
GitHub: https://github.com/eonn/sanctions-screening

## Prerequisites

1. **Kubernetes cluster** (minikube, kind, or cloud provider)
2. **kubectl** configured to access your cluster
3. **Docker** for building the application image
4. **kustomize** (optional, for advanced deployments)

## Quick Start

### 1. Build the Docker Image

First, build the application Docker image:

```bash
# From the project root directory
docker build -t sanctions-screening:latest .
```

### 2. Deploy to Kubernetes

Deploy all components using kubectl:

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or use kustomize (if available)
kubectl apply -k k8s/
```

### 3. Check Deployment Status

```bash
# Check all resources
kubectl get all -n sanctions-screening

# Check pod status
kubectl get pods -n sanctions-screening

# Check services
kubectl get services -n sanctions-screening
```

### 4. Access the Application

#### Option 1: Port Forward (for testing)
```bash
# Forward nginx service
kubectl port-forward -n sanctions-screening service/nginx-service 8080:80

# Access the application
open http://localhost:8080
```

#### Option 2: LoadBalancer (if supported by your cluster)
```bash
# Get the external IP
kubectl get service nginx-service -n sanctions-screening

# Access using the external IP
open http://<EXTERNAL-IP>
```

#### Option 3: Ingress (if ingress controller is installed)
```bash
# Add to /etc/hosts (or equivalent)
echo "127.0.0.1 sanctions-screening.local" >> /etc/hosts

# Access the application
open http://sanctions-screening.local
```

## Components

### Core Application
- **sanctions-screening-app**: Main FastAPI application
- **nginx**: Web server and load balancer

### Data Layer
- **postgres**: PostgreSQL database
- **redis**: Redis cache

### Messaging
- **rabbitmq**: RabbitMQ message broker
- **kafka**: Apache Kafka for streaming
- **zookeeper**: Zookeeper for Kafka

### Configuration
- **configmap**: Application configuration
- **secret**: Sensitive data (passwords, keys)

## Configuration

### Environment Variables

The application is configured via ConfigMap and Secret. Key settings:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MQ_HOST`: RabbitMQ host
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka servers
- `BERT_MODEL_NAME`: BERT model for NLP
- `SIMILARITY_THRESHOLD`: Matching threshold

### Secrets

Update the secret with your production values:

```bash
# Update secret values
kubectl create secret generic sanctions-screening-secret \
  --from-literal=postgres-password=your-secure-password \
  --from-literal=secret-key=your-secret-key \
  --from-literal=mq-password=your-mq-password \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Scaling

### Horizontal Pod Autoscaling

```bash
# Create HPA for the application
kubectl autoscale deployment sanctions-screening-app \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n sanctions-screening
```

### Manual Scaling

```bash
# Scale the application
kubectl scale deployment sanctions-screening-app --replicas=5 -n sanctions-screening

# Scale nginx
kubectl scale deployment nginx --replicas=3 -n sanctions-screening
```

## Monitoring

### Health Checks

```bash
# Check application health
kubectl get pods -n sanctions-screening -o wide

# Check logs
kubectl logs -f deployment/sanctions-screening-app -n sanctions-screening

# Check service endpoints
kubectl get endpoints -n sanctions-screening
```

### Metrics

The application exposes Prometheus metrics at `/metrics`:

```bash
# Port forward to access metrics
kubectl port-forward -n sanctions-screening service/sanctions-screening-service 8000:8000

# Access metrics
curl http://localhost:8000/metrics
```

## Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod <pod-name> -n sanctions-screening
   kubectl logs <pod-name> -n sanctions-screening
   ```

2. **Database connection issues**
   ```bash
   kubectl logs deployment/postgres -n sanctions-screening
   kubectl exec -it deployment/postgres -n sanctions-screening -- psql -U postgres
   ```

3. **Service discovery issues**
   ```bash
   kubectl get services -n sanctions-screening
   kubectl get endpoints -n sanctions-screening
   ```

### Debug Commands

```bash
# Get all resources
kubectl get all -n sanctions-screening

# Describe resources
kubectl describe deployment sanctions-screening-app -n sanctions-screening

# Check events
kubectl get events -n sanctions-screening --sort-by='.lastTimestamp'

# Access pod shell
kubectl exec -it <pod-name> -n sanctions-screening -- /bin/bash
```

## Production Considerations

### Security
- Update all default passwords in secrets
- Use proper TLS certificates
- Enable network policies
- Use RBAC for access control

### Performance
- Configure resource limits and requests
- Use persistent volumes for data
- Enable horizontal pod autoscaling
- Configure proper health checks

### Monitoring
- Set up Prometheus and Grafana
- Configure log aggregation
- Set up alerting
- Monitor resource usage

### Backup
- Regular database backups
- Configuration backup
- Disaster recovery plan

## Cleanup

To remove all resources:

```bash
kubectl delete namespace sanctions-screening
```

Or delete individual components:

```bash
kubectl delete -f k8s/
```
