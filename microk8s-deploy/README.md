# Deploy Kubeflow On a Local MicroK8s Installation
This tutorial walks you through how to deploy Kubeflow locally to a MicroK8s installation running on a personal box. It assumes you are using `v1.21` of MicroK8s and Ubuntu 20.04. 

> ***NOTE:*** There are alternative installation instructions for installing MicroK8s on Windows. The link will be in the installation section.

## Helpful Links and Resources
* Kubeflow on MicroK8s Quickstart Guide ([link](https://charmed-kubeflow.io/docs/quickstart))
* Kubeflow General Installation Guide On Any Conformant Kubernetes ([link](https://charmed-kubeflow.io/docs/install))

## MicroK8s Installation (Ubuntu)
```
sudo snap install microk8s --classic --channel=1.21/stable
```

MicroK8s is super light weight, so it runs a super low resource version of K8s. However, there are a few services we will need (and want) at a minimum to run Kubeflow.Enable the `storage`, `dns`, `ingress`, `metallb` and `dashboard` services for MicroK8s

```
microk8s enable dns storage ingress dashboard metallb:10.64.140.43-10.64.140.49
```

You can see that we added some detail when enabling MetalLB, in this case the address pool to use. More info [here](https://microk8s.io/docs).

## Install Juju
Juju is an operation Lifecycle manager(OLM) for clouds, bare metal or Kubernetes. We will use it to deploy and manage the different components that make up Kubeflow.

```
sudo snap install juju --classic
juju bootstrap microk8s
juju add-model kubeflow
```

## Deploy Kubeflow (Lite)
You can opt to deploy a full Kubeflow installation. However, in order to make that feasible, you need at least 4 cores, 12GB of RAM, and 60GB of storage that are free to use on your local cluster. For laptop or smaller deployments, going with the *lite* bundle is the best way to get your feet wet.

```
juju deploy kubeflow-lite --trust
```

You can watch the status of the deployment by using the following command (it will take several minutes to get the Kubeflow deployment completed)

```
watch -c juju status --color
```

> ***NOTE:***  You can move on to the next post-installation steps while waiting for the deployment to finish

## Post-deployment Configuration
For authentication and allowing access to the Kubeflow UI, some components (e.g. `dex`) need to be configured with the ingress URL to be allowed. Since we are setting this up as a local Microk8s installation, we know what that URL will be.

> ***WARNING:***  Finding the URL: If you have a different setup for microk8s, or you are adapting this tutorial for a different Kubernetes, you can find the URL required by examining the IP address of the `istio-ingressgateway` service. For example, you can determinine this information using kubectl: `microk8s kubectl -n kubeflow get svc istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}'`

```
juju config dex-auth public-url=http://10.64.140.43.nip.io
juju config oidc-gatekeeper public-url=http://10.64.140.43.nip.io
```

### Simple Authentication
To enable simple authentication and set a username and password for your Kubeflow deployment:

```
juju config dex-auth static-username=admin
juju config dex-auth static-password=password
```

### Accessing the Kubeflow Dashboard
