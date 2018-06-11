from json import loads
import pathlib
from time import sleep
from os import environ

from googleapiclient import discovery
from kubernetes import client, config
from prometheus_client import Gauge, start_http_server
from oauth2client.client import GoogleCredentials

ING_ANNOTATION = 'ingress.kubernetes.io/backends'

credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

project = environ.get("GOOGLE_PROJECT_ID")
region = environ.get("GOOGLE_PROJECT_REGION")
zone = environ.get("GOOGLE_PROJECT_ZONE")

labels = ('project', 'region', 'backend', 'health_route', 'health_port',
          'status', 'ingress_name')
guage = Gauge('kube_ingress_status', 'ingress backends status in kubernetes',
              labels)


url_prefix = "https://www.googleapis.com/compute/v1/projects/{}/global/healthChecks/" # noqa
url_prefix = url_prefix.format(project)


def record_ingress(ingress_name, backend_name, check, state):
    http = check['httpHealthCheck']
    guage.labels(project=project, region=region, backend=backend_name,
                 health_route=http['requestPath'], health_port=http['port'],
                 status=state, ingress_name=ingress_name).set(1)


def load_health_checks(backend_name):
    def get_health_check(check):
        check_id = check.replace(url_prefix, '')
        request = service.healthChecks().get(project=project,
                                             healthCheck=check_id)
        return request.execute()

    backend = service.backendServices().get(project=project,
                                            backendService=backend_name)
    backend = backend.execute()
    return [get_health_check(h) for h in backend['healthChecks']]


def monitor_ingress():
    k8s_extensions = client.ExtensionsV1beta1Api()
    all_ingress = k8s_extensions.list_namespaced_ingress('default')
    for ing in all_ingress.items:
        if ING_ANNOTATION not in ing.metadata.annotations:
            continue

        backends_json = ing.metadata.annotations[ING_ANNOTATION]
        ing_backends = loads(backends_json)
        for backend, state in ing_backends.items():
            health_checks = load_health_checks(backend)

            # Normally only a single health checks will exist, handling array
            # response
            for check in health_checks:
                record_ingress(ing.metadata.name, backend, check,
                               state.lower())


def generate_kube_config(endpoint, username, password):
    config = """apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://{endpoint}
  name: c
contexts:
- context:
    cluster: c
    user: c
  name: c
current-context: c
kind: Config
preferences: {{}}
users:
- name: c
  user:
    password: {password}
    username: {username}"""

    home = str(pathlib.Path.home())
    pathlib.Path("{}/.kube".format(home)).mkdir(exist_ok=True)
    with open("{}/.kube/config".format(home), "w") as f:
        f.write(config.format(endpoint=endpoint, username=username,
                              password=password))


def load_kube_config(cluster):
    container_service = discovery.build(
            'container', 'v1', credentials=credentials)

    request = container_service.projects().zones().clusters().get(
            projectId=project, zone=zone, clusterId=cluster)

    response = request.execute()

    username = response['masterAuth']['username']
    password = response['masterAuth']['password']
    return response['endpoint'], username, password


def main():
    cluster = environ.get("GOOGLE_CLUSTER_ID")

    endpoint, username, password = load_kube_config(cluster)
    generate_kube_config(endpoint, username, password)
    config.load_kube_config()

    start_http_server(environ.get("PORT", 8080))

    while True:
        monitor_ingress()
        sleep(15)


if __name__ == "__main__":
    main()
