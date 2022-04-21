# Getting Started With Kubeflow on EKS

## Prerequisites
You must have the following installed on your local computer.

* `kustomize` (version `3.2.0`): for working with Kubeflow manifests to install Kubeflow components ([link](https://weaveworks-gitops.awsworkshop.io/20_weaveworks_prerequisites/15_install_kustomize.html)).
* `kubectl` (version `1.20`): for running install commands, and interacting with running Kubernetes cluster
* `eksctl`: for interacting with Amazon EKS clusters ([link](https://weaveworks-gitops.awsworkshop.io/20_weaveworks_prerequisites/11_install_eksctl.html)).
* `AWS CLI` tool for interacting with aws resources In addition, you will need appropriate permissions to create EKS clusters (and their underlying resources like EC2 nodes, VPCs, and etc.) on an AWS account and region. The following sections assume that you have already authenticated, and have access to an AWS cloud account and its resources ([link](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)).

> ***WARNING*** Your `kubectl` version must be within one `MINOR` version of the K8s version you deploy (e.g. `v1.20` of `kubectl` will work with with K8s versions: `1.19`, `1.20`, and `1.21`)

One option for setting up AWS account access is to run the command aws configure and enter the requested information. Alternatively, you may go the route of setting the environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`. The easiest way is to have these set in your environment before initiating Jupyter Notebook. Take a moment if needed to stop Jupyter, configure access to AWS from the command line, and then restart Jupyter and open this notebook.

## Cluster Creation
Using the `eks-cluster.yaml` file, run the following to deploy your EKS cluster

```bash
eksctl create cluster -f eks-cluster.yaml
```

After the cluster has been created (will take several minutes), you can run the following command to update your `~/.kube/config` for `kubectl` to gain access to the cluster

```bash
eksctl get cluster kubeflow-deployment --region ${SELECTED-REGION}
```

Test out your `kubectl` command:

```bash
kubectl get nodes
```

## Kubeflow Installation
Once the cluster is up and running and you have access to the cluster via `kubectl`, it is time to deploy Kubeflow to our newly created cluster. We will install Kubeflow version `1.5.0` using the manifests found [here](https://github.com/kubeflow/manifests/tree/v1.5.0). Specifically, these manifests will use `kustomize` to deploy the applications to the cluster.

> ***NOTE*** Manifests are just `.yaml` files that essentially set up different applications, services, etc. You can read more about Kuberenetes manifests [here](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)

I ***HIGHLY*** encourage you to poke around that repo a bit and go through the `README`; it will only help solidify what you are trying to accomplish. While we could set up a script to automatically deploy the manifests (like what is done in the `gke-deploy` section of this repo), we will take finer control over this deployment and install each resource on its own. The reason for this is simple: so that you understand a little bit of what deploying things to Kubernetes is!

### Get the Manifests
Start out by cloning the `1.5.0` manifests locally and `cd` to the directory:

```bash
git clone --depth 1 --branch v1.5.0 https://github.com/kubeflow/manifests.git
cd manifests
```

What follows now is the installation of the different applications and serivices that makes Kubeflow tick. Again, I encourage you to take a minute to understand what each service is and what its function is.

...ok, if you ***really*** want to be lazy, just run the following to install the entire Kubeflow suite:
```
while ! kustomize build example | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

Otherwise run each step below:

### Cert-Manager
```
kustomize build common/cert-manager/cert-manager/base | kubectl apply -f -
kustomize build common/cert-manager/kubeflow-issuer/base | kubectl apply -f -
```

### Istio
```
kustomize build common/istio-1-11/istio-crds/base | kubectl apply -f -
kustomize build common/istio-1-11/istio-namespace/base | kubectl apply -f -
kustomize build common/istio-1-11/istio-install/base | kubectl apply -f -
```

### Dex
In this default installation, it includes a static user with email `user@example.com`. By default, the user's password is `12341234`.
```
kustomize build common/dex/overlays/istio | kubectl apply -f -
```

### OIDC AuthService
```
kustomize build common/oidc-authservice/base | kubectl apply -f -
```

### Knative
```
kustomize build common/knative/knative-serving/overlays/gateways | kubectl apply -f -
kustomize build common/istio-1-11/cluster-local-gateway/base | kubectl apply -f -
```

### Knative Event Logging
```
kustomize build common/knative/knative-eventing/base | kubectl apply -f -
```

### Kubeflow Namespace
```
kustomize build common/kubeflow-namespace/base | kubectl apply -f -
```

### Kubeflow Roles
```
kustomize build common/kubeflow-roles/base | kubectl apply -f -
```

### Kubeflow Istio Resources
```
kustomize build common/istio-1-11/kubeflow-istio-resources/base | kubectl apply -f -
```

### Kubeflow Pipelines
```
kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user | kubectl apply -f -
```

### KServe
```
kustomize build contrib/kserve/kserve | kubectl apply -f -
```

### Models Web App
```
kustomize build contrib/kserve/models-web-app/overlays/kubeflow | kubectl apply -f -
```

### Katib
```
kustomize build apps/katib/upstream/installs/katib-with-kubeflow | kubectl apply -f -
```

### Central Dashboard
```
kustomize build apps/centraldashboard/upstream/overlays/kserve | kubectl apply -f -
```

### Admission Webhook
```
kustomize build apps/admission-webhook/upstream/overlays/cert-manager | kubectl apply -f -
```

### Notebooks
```
kustomize build apps/jupyter/notebook-controller/upstream/overlays/kubeflow | kubectl apply -f -
kustomize build apps/jupyter/jupyter-web-app/upstream/overlays/istio | kubectl apply -f -
```

### Profiles + KFAM
```
kustomize build apps/profiles/upstream/overlays/kubeflow | kubectl apply -f -
```

### Volumes Web App
```
kustomize build apps/volumes-web-app/upstream/overlays/istio | kubectl apply -f -
```

### Tensorboard
```
kustomize build apps/tensorboard/tensorboards-web-app/upstream/overlays/istio | kubectl apply -f -
kustomize build apps/tensorboard/tensorboard-controller/upstream/overlays/kubeflow | kubectl apply -f -
```

### Training Operator
```
kustomize build apps/training-operator/upstream/overlays/kubeflow | kubectl apply -f -
```

### User Namespace
```
kustomize build common/user-namespace/base | kubectl apply -f -
```

## Connect to Your Kubeflow Cluser
The next step is to FINALLY connect to your Kubeflow cluster. The simplest way to get started is to simply use `kubectl` to port forward the `istio-ingressgateway` service to you personal computer:

```
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

After this, Kubeflow UI will be accessible at `http://localhost:8080`