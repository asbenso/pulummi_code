"""
Configuration variables for EKS cluster setup
"""
import pulumi

config = pulumi.Config()

# VPC Configuration
vpc_name = config.get('vpc_name') or 'eks-vpc'
vpc_cidr = config.get('vpc_cidr') or '10.0.0.0/16'

# Availability Zones
availability_zones = config.get_object('availability_zones') or ['us-east-1a', 'us-east-1b']

# Subnet Configuration
private_subnet_1_cidr = config.get('private_subnet_1_cidr') or '10.0.1.0/24'
private_subnet_2_cidr = config.get('private_subnet_2_cidr') or '10.0.2.0/24'
public_subnet_1_cidr = config.get('public_subnet_1_cidr') or '10.0.101.0/24'
public_subnet_2_cidr = config.get('public_subnet_2_cidr') or '10.0.102.0/24'

# EKS Cluster Configuration
cluster_name = config.get('cluster_name') or 'eks-cluster'
cluster_version = config.get('cluster_version') or '1.28'
cluster_role_name = config.get('cluster_role_name') or 'eks-cluster-role'

# Node Group Configuration
node_group_name = config.get('node_group_name') or 'eks-node-group'
node_desired_count = config.get_int('node_desired_count') or 2
node_min_count = config.get_int('node_min_count') or 1
node_max_count = config.get_int('node_max_count') or 4
node_instance_type = config.get('node_instance_type') or 't3.medium'
node_role_name = config.get('node_role_name') or 'eks-node-role'

# AWS Region
aws_region = config.get('aws_region') or 'us-east-1'

# Tags
common_tags = {
    'Environment': config.get('environment') or 'dev',
    'Project': config.get('project') or 'eks-project',
    'CreatedBy': 'Pulumi',
}
