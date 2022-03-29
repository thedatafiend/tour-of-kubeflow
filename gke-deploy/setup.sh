#!/bin/bash

# Source the environment variables
set -e
source ./cluster.env

# Initialize the cluster creation
gcloud container clusters create \
--machine-type n1-standard-8 \
--num-nodes 3 \
--zone us-central1-c \
--cluster-version ${CLUSTER_VERSION} \
--subnetwork=${SUBNET_NAME} \
--no-enable-master-authorized-networks \
--enable-ip-alias --enable-private-nodes \
--master-ipv4-cidr ${NETWORK_ID}.16.0.32/28 \
--workload-pool=${PROJECT_ID}.svc.id.goog \
--project ${PROJECT_ID} \
${CLUSTER_NAME}

# Get credentials for the new cluster
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=us-central1-c --project ${PROJECT_ID}

# Make yourself an admin for the cluster
kubectl create clusterrolebinding cluster-admin-binding --clusterrole=cluster-admin --user=${EMAIL_ADDRESS}

# Set all firewall rules and required ports
FIREWALL_RULE_NAME=$(gcloud compute firewall-rules list --format="value(name)" | grep "gke-${CLUSTER_NAME}.*-master")
gcloud compute firewall-rules update ${FIREWALL_RULE_NAME} \
--allow="tcp:10250,tcp:443,tcp:8443,tcp:8080,tcp:8008,tcp:8012,tcp:8013,\
tcp:8081,tcp:9090,tcp:6443,tcp:9443,tcp:15010,tcp:15012,tcp:15014,tcp:15017,tcp:15021,tcp:15443,tcp:31400"

# Download the kubeflow deployment 
git clone --depth 1 --branch v${KUBEFLOW_VERSION} https://github.com/kubeflow/manifests.git
cd manifests

# Deploy Kubeflow to the cluster
while ! kustomize build example | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user | kubectl delete -f -
kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user-pns | kubectl apply -f -

# Add IAM policy binding using gcloud
gcloud --project=${PROJECT_ID} iam service-accounts add-iam-policy-binding ${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${KSA_NAME}]"

# Add annotation using kubectl
kubectl annotate serviceaccount ${KSA_NAME} \
    --namespace ${K8S_NAMESPACE} \
    iam.gke.io/gcp-service-account=${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com