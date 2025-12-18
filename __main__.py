"""
Main Pulumi program to set up an AWS EKS cluster with VPC
"""
import pulumi
import pulumi_aws as aws
import pulumi_eks as eks
import json

from config import (
    vpc_name, vpc_cidr, availability_zones,
    private_subnet_1_cidr, private_subnet_2_cidr,
    public_subnet_1_cidr, public_subnet_2_cidr,
    cluster_name, cluster_version, cluster_role_name,
    node_group_name, node_desired_count, node_min_count,
    node_max_count, node_instance_type, node_role_name,
    aws_region, common_tags
)

# ==================== VPC Setup ====================

# Create VPC
vpc = aws.ec2.Vpc(vpc_name,
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**common_tags, 'Name': vpc_name}
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway('eks-igw',
    vpc_id=vpc.id,
    tags={**common_tags, 'Name': 'eks-igw'}
)

# Create Public Subnets
public_subnet_1 = aws.ec2.Subnet('eks-public-subnet-1',
    vpc_id=vpc.id,
    cidr_block=public_subnet_1_cidr,
    availability_zone=availability_zones[0],
    map_public_ip_on_launch=True,
    tags={**common_tags, 'Name': 'eks-public-subnet-1', 'Type': 'Public'}
)

public_subnet_2 = aws.ec2.Subnet('eks-public-subnet-2',
    vpc_id=vpc.id,
    cidr_block=public_subnet_2_cidr,
    availability_zone=availability_zones[1],
    map_public_ip_on_launch=True,
    tags={**common_tags, 'Name': 'eks-public-subnet-2', 'Type': 'Public'}
)

# Create Private Subnets
private_subnet_1 = aws.ec2.Subnet('eks-private-subnet-1',
    vpc_id=vpc.id,
    cidr_block=private_subnet_1_cidr,
    availability_zone=availability_zones[0],
    tags={**common_tags, 'Name': 'eks-private-subnet-1', 'Type': 'Private'}
)

private_subnet_2 = aws.ec2.Subnet('eks-private-subnet-2',
    vpc_id=vpc.id,
    cidr_block=private_subnet_2_cidr,
    availability_zone=availability_zones[1],
    tags={**common_tags, 'Name': 'eks-private-subnet-2', 'Type': 'Private'}
)

# Create Elastic IPs for NAT Gateways
eip_1 = aws.ec2.Eip('eks-eip-1',
    vpc=True,
    tags={**common_tags, 'Name': 'eks-eip-1'}
)

eip_2 = aws.ec2.Eip('eks-eip-2',
    vpc=True,
    tags={**common_tags, 'Name': 'eks-eip-2'}
)

# Create NAT Gateways
nat_gateway_1 = aws.ec2.NatGateway('eks-nat-gateway-1',
    subnet_id=public_subnet_1.id,
    allocation_id=eip_1.id,
    tags={**common_tags, 'Name': 'eks-nat-gateway-1'},
    opts=pulumi.ResourceOptions(depends_on=[igw])
)

nat_gateway_2 = aws.ec2.NatGateway('eks-nat-gateway-2',
    subnet_id=public_subnet_2.id,
    allocation_id=eip_2.id,
    tags={**common_tags, 'Name': 'eks-nat-gateway-2'},
    opts=pulumi.ResourceOptions(depends_on=[igw])
)

# Create Route Table for Public Subnets
public_route_table = aws.ec2.RouteTable('eks-public-rt',
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block='0.0.0.0/0',
            gateway_id=igw.id,
        )
    ],
    tags={**common_tags, 'Name': 'eks-public-rt'}
)

# Associate Public Subnets with Public Route Table
public_route_table_assoc_1 = aws.ec2.RouteTableAssociation('eks-public-rta-1',
    subnet_id=public_subnet_1.id,
    route_table_id=public_route_table.id
)

public_route_table_assoc_2 = aws.ec2.RouteTableAssociation('eks-public-rta-2',
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id
)

# Create Route Tables for Private Subnets
private_route_table_1 = aws.ec2.RouteTable('eks-private-rt-1',
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block='0.0.0.0/0',
            nat_gateway_id=nat_gateway_1.id,
        )
    ],
    tags={**common_tags, 'Name': 'eks-private-rt-1'}
)

private_route_table_2 = aws.ec2.RouteTable('eks-private-rt-2',
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block='0.0.0.0/0',
            nat_gateway_id=nat_gateway_2.id,
        )
    ],
    tags={**common_tags, 'Name': 'eks-private-rt-2'}
)

# Associate Private Subnets with Private Route Tables
private_route_table_assoc_1 = aws.ec2.RouteTableAssociation('eks-private-rta-1',
    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table_1.id
)

private_route_table_assoc_2 = aws.ec2.RouteTableAssociation('eks-private-rta-2',
    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table_2.id
)

# ==================== IAM Roles ====================

# Create EKS Cluster Role
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "eks.amazonaws.com"
            }
        }
    ]
}

cluster_role = aws.iam.Role(cluster_role_name,
    assume_role_policy=json.dumps(assume_role_policy),
    tags={**common_tags, 'Name': cluster_role_name}
)

cluster_role_policy_attachment = aws.iam.RolePolicyAttachment('eks-cluster-policy',
    role=cluster_role.name,
    policy_arn='arn:aws:iam::aws:policy/AmazonEKSClusterPolicy'
)

cluster_role_vpc_policy_attachment = aws.iam.RolePolicyAttachment('eks-cluster-vpc-policy',
    role=cluster_role.name,
    policy_arn='arn:aws:iam::aws:policy/AmazonEKSVPCResourceController'
)

# Create EKS Node Role
node_assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            }
        }
    ]
}

node_role = aws.iam.Role(node_role_name,
    assume_role_policy=json.dumps(node_assume_role_policy),
    tags={**common_tags, 'Name': node_role_name}
)

node_role_policy_attachment = aws.iam.RolePolicyAttachment('eks-node-policy',
    role=node_role.name,
    policy_arn='arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy'
)

node_cni_policy_attachment = aws.iam.RolePolicyAttachment('eks-cni-policy',
    role=node_role.name,
    policy_arn='arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy'
)

node_registry_policy_attachment = aws.iam.RolePolicyAttachment('eks-registry-policy',
    role=node_role.name,
    policy_arn='arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'
)

# ==================== Security Groups ====================

# Security Group for EKS Cluster
cluster_security_group = aws.ec2.SecurityGroup('eks-cluster-sg',
    vpc_id=vpc.id,
    description='Security group for EKS cluster',
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp',
            from_port=443,
            to_port=443,
            cidr_blocks=['0.0.0.0/0'],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol='-1',
            from_port=0,
            to_port=0,
            cidr_blocks=['0.0.0.0/0'],
        )
    ],
    tags={**common_tags, 'Name': 'eks-cluster-sg'}
)

# Security Group for EKS Worker Nodes
node_security_group = aws.ec2.SecurityGroup('eks-node-sg',
    vpc_id=vpc.id,
    description='Security group for EKS worker nodes',
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp',
            from_port=1025,
            to_port=65535,
            security_groups=[cluster_security_group.id],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol='tcp',
            from_port=443,
            to_port=443,
            security_groups=[cluster_security_group.id],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol='-1',
            from_port=0,
            to_port=0,
            cidr_blocks=['0.0.0.0/0'],
        )
    ],
    tags={**common_tags, 'Name': 'eks-node-sg'}
)

# ==================== EKS Cluster ====================

# Create EKS Cluster
eks_cluster = aws.eks.Cluster(cluster_name,
    version=cluster_version,
    role_arn=cluster_role.arn,
    vpc_config=aws.eks.ClusterVpcConfigArgs(
        subnet_ids=[
            public_subnet_1.id,
            public_subnet_2.id,
            private_subnet_1.id,
            private_subnet_2.id,
        ],
        security_group_ids=[cluster_security_group.id],
        endpoint_private_access=True,
        endpoint_public_access=True,
    ),
    tags={**common_tags, 'Name': cluster_name}
)

# ==================== EKS Node Group ====================

# Create EKS Node Group
node_group = aws.eks.NodeGroup(node_group_name,
    cluster_name=eks_cluster.name,
    node_group_name=node_group_name,
    node_role_arn=node_role.arn,
    subnet_ids=[
        private_subnet_1.id,
        private_subnet_2.id,
    ],
    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        desired_size=node_desired_count,
        max_size=node_max_count,
        min_size=node_min_count,
    ),
    instance_types=[node_instance_type],
    tags={**common_tags, 'Name': node_group_name}
)

# ==================== Outputs ====================

pulumi.export('vpc_id', vpc.id)
pulumi.export('vpc_cidr', vpc.cidr_block)
pulumi.export('cluster_name', eks_cluster.name)
pulumi.export('cluster_endpoint', eks_cluster.endpoint)
pulumi.export('cluster_version', eks_cluster.version)
pulumi.export('cluster_arn', eks_cluster.arn)
pulumi.export('node_group_id', node_group.id)
pulumi.export('public_subnet_1_id', public_subnet_1.id)
pulumi.export('public_subnet_2_id', public_subnet_2.id)
pulumi.export('private_subnet_1_id', private_subnet_1.id)
pulumi.export('private_subnet_2_id', private_subnet_2.id)
