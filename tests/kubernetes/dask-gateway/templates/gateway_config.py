import os
import json

_PROPERTIES = json.loads({{- $values | toJson | quote }})

def get_property(key, default=None):
    """Read a property from the configured helm values."""
    value = _PROPERTIES
    for key2 in key.split("."):
        if not isinstance(value, dict) or key2 not in value:
            return default
        value = value[key2]
    return value

c.DaskGateway.log_level = "{{ .Values.gateway.loglevel }}"

# Configure addresses
c.DaskGateway.address = ":8000"
c.KubeBackend.api_url = 'http://{{ include "dask-gateway.apiName" . }}.{{ .Release.Namespace }}:8000/api'

# Configure the backend
c.DaskGateway.backend_class = "dask_gateway_server.backends.kubernetes.KubeBackend"
c.KubeBackend.gateway_instance = "{{ include "dask-gateway.fullname" . }}"

# Configure the dask cluster image
image_name = get_property("gateway.backend.image.name")
if image_name:
    image_tag = get_property("gateway.backend.image.tag")
    c.KubeClusterConfig.image = (
        "%s:%s" % (image_name, image_tag) if image_tag else image_name
    )

# Forward dask cluster configuration
for field, prop_name in [
    # Scheduler config
    ("scheduler_cores", "scheduler.cores.request"),
    ("scheduler_cores_limit", "scheduler.cores.limit"),
    ("scheduler_memory", "scheduler.memory.request"),
    ("scheduler_memory_limit", "scheduler.memory.limit"),
    ("scheduler_extra_container_config", "scheduler.extraContainerConfig"),
    ("scheduler_extra_pod_config", "scheduler.extraPodConfig"),
    # Worker config
    ("worker_cores", "worker.cores.request"),
    ("worker_cores_limit", "worker.cores.limit"),
    ("worker_memory", "worker.memory.request"),
    ("worker_memory_limit", "worker.memory.limit"),
    ("worker_extra_container_config", "worker.extraContainerConfig"),
    ("worker_extra_pod_config", "worker.extraPodConfig"),
    # Additional fields
    ("image_pull_policy", "image.pullPolicy"),
    ("environment", "environment"),
    ("namespace", "namespace"),
]:
    value = get_property("gateway.backend." + prop_name)
    if value is not None:
        setattr(c.KubeClusterConfig, field, value)

# Authentication
auth_type = get_property("gateway.auth.type")
if auth_type == "simple":
    c.DaskGateway.authenticator_class = "dask_gateway_server.auth.SimpleAuthenticator"
    password = get_property("gateway.auth.simple.password")
    if password is not None:
        c.SimpleAuthenticator.password = password
elif auth_type == "kerberos":
    c.DaskGateway.authenticator_class = "dask_gateway_server.auth.KerberosAuthenticator"
    keytab = get_property("gateway.auth.kerberos.keytab")
    if keytab is not None:
        c.KerberosAuthenticator.keytab = keytab
elif auth_type == "jupyterhub":
    c.DaskGateway.authenticator_class = "dask_gateway_server.auth.JupyterHubAuthenticator"
    api_url = get_property("gateway.auth.jupyterhub.apiUrl")
    if api_url is None:
        try:
            api_url = "http://{HUB_SERVICE_HOST}:{HUB_SERVICE_PORT}/hub/api".format(**os.environ)
        except Exception:
            raise ValueError(
                "Failed to infer JupyterHub API url from environment, "
                "please specify `gateway.auth.jupyterhub.apiUrl` in "
                "your config file"
            )
    c.DaskGateway.JupyterHubAuthenticator.jupyterhub_api_url = api_url
elif auth_type == "custom":
    auth_cls = get_property("gateway.auth.custom.class")
    c.DaskGateway.authenticator_class = auth_cls
    auth_cls_name = auth_cls.rsplit('.', 1)[-1]
    auth_config = c[auth_cls_name]
    auth_config.update(get_property("gateway.auth.custom.config") or {})
else:
    raise ValueError("Unknown authenticator type %r" % auth_type)