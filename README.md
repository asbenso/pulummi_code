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

## Additional Resources

- [Pulumi AWS Documentation](https://www.pulumi.com/docs/reference/pkg/aws/)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Pulumi EKS Provider](https://www.pulumi.com/docs/reference/pkg/eks/)
