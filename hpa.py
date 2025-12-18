"""
Horizontal Pod Autoscaler (HPA) Configuration
This module sets up HPA for scaling Kubernetes deployments based on CPU/memory metrics
"""
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    PodSpecArgs, PodTemplateSpecArgs, ContainerArgs, ResourceRequirementsArgs,
    ServiceArgs, ServiceSpecArgs, ServicePortArgs
)
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs, LabelSelectorArgs
from pulumi_kubernetes.autoscaling.v2 import (
    HorizontalPodAutoscalerArgs, HorizontalPodAutoscalerSpecArgs,
    MetricSpecArgs, ResourceMetricSourceArgs, TargetAverageUtilizationMetricStatusArgs
)

config = pulumi.Config()

# HPA Configuration
enable_hpa = config.get_bool('enable_hpa') or True
hpa_min_replicas = config.get_int('hpa_min_replicas') or 2
hpa_max_replicas = config.get_int('hpa_max_replicas') or 10
hpa_cpu_threshold = config.get_int('hpa_cpu_threshold') or 70
hpa_memory_threshold = config.get_int('hpa_memory_threshold') or 80

# Demo Deployment Configuration
demo_namespace = config.get('demo_namespace') or 'default'
demo_app_name = config.get('demo_app_name') or 'demo-app'
demo_app_image = config.get('demo_app_image') or 'nginx:latest'
demo_app_replicas = config.get_int('demo_app_replicas') or 2
demo_app_port = config.get_int('demo_app_port') or 80

common_tags = {
    'ManagedBy': 'Pulumi',
    'Component': 'HPA',
}


def create_metrics_server(provider: k8s.Provider) -> None:
    """
    Install Metrics Server for HPA to collect metrics
    """
    if enable_hpa:
        metrics_chart = k8s.helm.v3.Chart(
            'metrics-server',
            k8s.helm.v3.ChartOpts(
                chart='metrics-server',
                namespace='kube-system',
                values={
                    'args': [
                        '--kubelet-insecure-tls',
                        '--kubelet-preferred-address-types=InternalIP'
                    ]
                },
                repo='https://kubernetes-sigs.github.io/metrics-server/charts',
            ),
            opts=pulumi.ResourceOptions(provider=provider)
        )
        pulumi.export('metrics_server_chart', metrics_chart.id)


def create_demo_deployment(provider: k8s.Provider) -> k8s.apps.v1.Deployment:
    """
    Create a demo deployment to demonstrate HPA
    """
    app_labels = {
        'app': demo_app_name,
        **common_tags
    }

    deployment = k8s.apps.v1.Deployment(
        demo_app_name,
        metadata=ObjectMetaArgs(
            namespace=demo_namespace,
            labels=app_labels,
        ),
        spec=DeploymentSpecArgs(
            replicas=demo_app_replicas,
            selector=LabelSelectorArgs(match_labels={'app': demo_app_name}),
            template=PodTemplateSpecArgs(
                metadata=ObjectMetaArgs(labels=app_labels),
                spec=PodSpecArgs(
                    containers=[
                        ContainerArgs(
                            name=demo_app_name,
                            image=demo_app_image,
                            ports=[{'container_port': demo_app_port}],
                            resources=ResourceRequirementsArgs(
                                requests={
                                    'cpu': '100m',
                                    'memory': '128Mi',
                                },
                                limits={
                                    'cpu': '500m',
                                    'memory': '512Mi',
                                }
                            ),
                        )
                    ]
                ),
            ),
        ),
        opts=pulumi.ResourceOptions(provider=provider)
    )

    return deployment


def create_demo_service(provider: k8s.Provider) -> k8s.core.v1.Service:
    """
    Create a service for the demo deployment
    """
    service = k8s.core.v1.Service(
        f'{demo_app_name}-service',
        metadata=ObjectMetaArgs(
            namespace=demo_namespace,
            labels={'app': demo_app_name},
        ),
        spec=ServiceSpecArgs(
            selector={'app': demo_app_name},
            ports=[ServicePortArgs(port=80, target_port=demo_app_port)],
            type='LoadBalancer',
        ),
        opts=pulumi.ResourceOptions(provider=provider)
    )

    return service


def create_hpa(deployment: k8s.apps.v1.Deployment, provider: k8s.Provider) -> k8s.autoscaling.v2.HorizontalPodAutoscaler:
    """
    Create Horizontal Pod Autoscaler for the deployment
    """
    if not enable_hpa:
        return None

    hpa = k8s.autoscaling.v2.HorizontalPodAutoscaler(
        f'{demo_app_name}-hpa',
        metadata=ObjectMetaArgs(
            namespace=demo_namespace,
            labels={'app': demo_app_name},
        ),
        spec=HorizontalPodAutoscalerSpecArgs(
            scale_target_ref={
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'name': deployment.metadata['name'],
            },
            min_replicas=hpa_min_replicas,
            max_replicas=hpa_max_replicas,
            metrics=[
                {
                    'type': 'Resource',
                    'resource': {
                        'name': 'cpu',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': hpa_cpu_threshold,
                        }
                    }
                },
                {
                    'type': 'Resource',
                    'resource': {
                        'name': 'memory',
                        'target': {
                            'type': 'Utilization',
                            'averageUtilization': hpa_memory_threshold,
                        }
                    }
                }
            ],
        ),
        opts=pulumi.ResourceOptions(
            provider=provider,
            depends_on=[deployment]
        )
    )

    return hpa


def setup_hpa_infrastructure(provider: k8s.Provider) -> dict:
    """
    Main function to set up all HPA-related infrastructure
    """
    if not enable_hpa:
        pulumi.info("HPA is disabled. Skipping HPA setup.")
        return {}

    # Install Metrics Server
    create_metrics_server(provider)

    # Create demo deployment
    deployment = create_demo_deployment(provider)

    # Create service
    service = create_demo_service(provider)

    # Create HPA
    hpa = create_hpa(deployment, provider)

    # Export outputs
    return {
        'deployment_name': deployment.metadata['name'],
        'service_name': service.metadata['name'],
        'hpa_name': hpa.metadata['name'],
        'hpa_min_replicas': hpa_min_replicas,
        'hpa_max_replicas': hpa_max_replicas,
        'hpa_cpu_threshold': hpa_cpu_threshold,
        'hpa_memory_threshold': hpa_memory_threshold,
    }
