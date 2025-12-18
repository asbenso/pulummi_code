# Pulumi EKS Cluster Setup

This Pulumi project sets up a complete AWS EKS cluster with VPC, subnets, NAT gateways, and node groups.

## Project Structure

- **`Pulumi.yaml`** - Project metadata
- **`Pulumi.dev.yaml`** - Stack configuration for development environment
- **`config.py`** - Configuration variables for VPC, EKS cluster, and node groups
- **`__main__.py`** - Main Pulumi program that creates all AWS resources
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This file

## Prerequisites

- Python 3.8+
- Pulumi CLI installed
- AWS CLI configured with appropriate credentials
- AWS account with necessary permissions

## Configuration

Edit the configuration in `config.py` to customize:

### VPC Configuration
- `vpc_name` - Name of the VPC (default: 'eks-vpc')
- `vpc_cidr` - CIDR block for VPC (default: '10.0.0.0/16')
- `availability_zones` - List of AZs (default: ['us-east-1a', 'us-east-1b'])

### Subnet Configuration
- `public_subnet_1_cidr` - CIDR for public subnet 1 (default: '10.0.101.0/24')
- `public_subnet_2_cidr` - CIDR for public subnet 2 (default: '10.0.102.0/24')
- `private_subnet_1_cidr` - CIDR for private subnet 1 (default: '10.0.1.0/24')
- `private_subnet_2_cidr` - CIDR for private subnet 2 (default: '10.0.2.0/24')

### EKS Cluster Configuration
- `cluster_name` - EKS cluster name (default: 'eks-cluster')
- `cluster_version` - Kubernetes version (default: '1.28')
- `cluster_role_name` - IAM role name for cluster (default: 'eks-cluster-role')

### Node Group Configuration
- `node_group_name` - Name of the node group (default: 'eks-node-group')
- `node_desired_count` - Desired number of nodes (default: 2)
- `node_min_count` - Minimum number of nodes (default: 1)
- `node_max_count` - Maximum number of nodes (default: 4)
- `node_instance_type` - EC2 instance type (default: 't3.medium')
- `node_role_name` - IAM role name for nodes (default: 'eks-node-role')

### Horizontal Pod Autoscaler (HPA) Configuration
- `enable_hpa` - Enable HPA setup (default: true)
- `hpa_min_replicas` - Minimum pod replicas (default: 2)
- `hpa_max_replicas` - Maximum pod replicas (default: 10)
- `hpa_cpu_threshold` - CPU utilization threshold % (default: 70)
- `hpa_memory_threshold` - Memory utilization threshold % (default: 80)
- `demo_namespace` - Kubernetes namespace for demo app (default: 'default')
- `demo_app_name` - Demo application name (default: 'demo-app')
- `demo_app_image` - Docker image for demo app (default: 'nginx:latest')
- `demo_app_replicas` - Initial replicas for demo app (default: 2)
- `demo_app_port` - Application port (default: 80)

### AWS & Tagging
- `aws_region` - AWS region (default: 'us-east-1')
- `environment` - Environment tag (default: 'dev')
- `project` - Project tag (default: 'eks-project')

## Usage

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Pulumi Stack

```bash
pulumi stack init dev
```

### 3. Set Configuration (Optional)

Override defaults by setting config values:

```bash
pulumi config set aws:region us-west-2
pulumi config set vpc_name my-vpc
pulumi config set vpc_cidr 10.1.0.0/16
pulumi config set cluster_name my-eks-cluster
pulumi config set node_instance_type t3.large
pulumi config set node_desired_count 3

# HPA Configuration
pulumi config set enable_hpa true
pulumi config set hpa_min_replicas 2
pulumi config set hpa_max_replicas 10
pulumi config set hpa_cpu_threshold 70
pulumi config set hpa_memory_threshold 80
```

### 4. Preview Changes

```bash
pulumi preview
```

### 5. Deploy

```bash
pulumi up
```

### 6. Get Outputs

```bash
pulumi stack output
```

### 7. Configure kubectl

After the cluster is created, configure kubectl:

```bash
aws eks update-kubeconfig --name <cluster_name> --region <region>
```

## Resources Created

### Network
- VPC with configurable CIDR block
- 2 Public Subnets (with route to Internet Gateway)
- 2 Private Subnets (with routes to NAT Gateways)
- Internet Gateway
- 2 NAT Gateways with Elastic IPs
- Route tables for public and private subnets

### Security
- Security groups for cluster and nodes
- IAM roles for cluster and nodes
- IAM policies for EKS and worker nodes

### EKS
- EKS Cluster
- Node Group with auto-scaling

### Kubernetes Components (HPA)
- Metrics Server (for pod metrics collection)
- Demo Deployment (nginx) with resource requests/limits
- Demo Service (LoadBalancer)
- Horizontal Pod Autoscaler (HPA v2 with CPU and Memory metrics)

## Cleanup

To destroy all resources:

```bash
pulumi destroy
```

## Troubleshooting

### Authentication Issues
- Ensure AWS CLI is configured with valid credentials
- Check IAM permissions for EKS, EC2, VPC, and IAM services

### Resource Creation Failures
- Check AWS account limits (VPCs, subnets, security groups, etc.)
- Verify IAM permissions
- Check CloudFormation events in AWS Console for detailed error messages

### Kubectl Connection Issues
- Run `aws eks update-kubeconfig` to update local kubeconfig
- Verify security groups allow your IP access to the cluster endpoint

### HPA Issues
- Ensure Metrics Server is running: `kubectl get deployment metrics-server -n kube-system`
- Check HPA status: `kubectl get hpa -n default`
- View HPA details: `kubectl describe hpa <hpa-name> -n default`
- Check pod metrics: `kubectl top pods -n default`
- Review HPA events: `kubectl describe hpa <hpa-name> -n default | grep -A 10 Events`

### Metrics Server Not Starting
- The Metrics Server installation may take a few minutes
- Check logs: `kubectl logs -n kube-system -l app.kubernetes.io/name=metrics-server`
- Ensure nodes have sufficient resources for the metrics server pod

## HPA Usage Examples

### Monitor HPA Status

```bash
# Get all HPAs
kubectl get hpa -n default

# Watch HPA in real-time
kubectl get hpa -n default -w

# Describe HPA for detailed information
kubectl describe hpa demo-app-hpa -n default
```

### View Pod Metrics

```bash
# Get current CPU/memory usage
kubectl top pods -n default

# Watch metrics in real-time
kubectl top pods -n default -l app=demo-app --watch
```

### Generate Load to Test HPA

```bash
# Get the LoadBalancer IP
SERVICE_IP=$(kubectl get svc demo-app-service -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Create a load generator pod
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://$SERVICE_IP; done"

# In another terminal, watch the HPA scale up
kubectl get hpa demo-app-hpa -n default -w
```

### Modify HPA Settings

```bash
# Edit HPA inline
kubectl edit hpa demo-app-hpa -n default

# Scale HPA thresholds via Pulumi config
pulumi config set hpa_cpu_threshold 60
pulumi up
```

## Additional Resources

- [Pulumi AWS Documentation](https://www.pulumi.com/docs/reference/pkg/aws/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Pulumi EKS Provider](https://www.pulumi.com/docs/reference/pkg/eks/)
