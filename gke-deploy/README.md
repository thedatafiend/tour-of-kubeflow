# Getting Started with Kubeflow on GKE


## Cluster Creation (Script Automation)
This is adapted from the following [documentation](https://zero-to-jupyterhub.readthedocs.io/en/latest/kubernetes/google/step-zero-gcp.html)

1. Ensure that `gcloud` is installed locally and that you have access to the target project

    for more info regarding private cluster creation, see this [link](https://cloud.google.com/kubernetes-engine/docs/how-to/private-clusters)

2. For a quick cluster creation, the following files are included:

   * `cluster.env`
   * `setup.sh`

   To run the cluster creation using `setup.sh`, you must first set up `cluster.env` with appropriate values. For example,

   ```bash
   export CLUSTER_NAME=kubeflow-private
   export SUBNET_NAME=kubeflow-subnet-1
   export EMAIL_ADDRESS=my.email@mail.com
   export NETWORK_ID=173
   export CLUSTER_VERSION=1.20.10
   ```

    > ***WARNING***: It's especially important that if multiple clusters are running in the same region, that the `NETWORK_ID` for the master ipv4 CIDR be different and **DOES NOT** overlap the `NETWORK_ID` of another cluster or resource. For example, if a cluster is already running with a `NETWORK_ID=173` within the same region and another cluster is desired, set the `NETWORK_ID` for the new cluster to `174`.
 
    > ***NOTE***: The `workload-pool` parameter must be set in order for identities on the cluster to make API calls to external Google Cloud
    services such as BigQuery or Dataflow.

   After which, source the `setup.sh` file as follows:
   ```bash
   ./setup.sh
   ```


## Cluster Access (Post-Deplopyment)
1. Ensure that `gloud` is properly configured for your local environment

2. Validate your access:
    ```bash
    kubectl get node
    ```

3. Port-forward the istio gateway to your local host:
    ```bash
    kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
    ```

4. To access the Kubeflow UI, go to `https://localhost/8080`


## Cluster Scaling and Deletion
* To scale the node pool down:
    ```bash
    gcloud container clusters resize ${CLUSTER_NAME} --num-nodes 0
    ```

* To delete the cluster:
    ```bash
    gcloud container clusters delete ${CLUSTER_NAME}
    ```


## Configuring Access to External Google Cloud Resources
The preferred approach to authenticating Kubeflow identities to Google Cloud resources such as BigQuery or Dataflow (which are external to your cluster) is to use [Kubernetes Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity). Workload Identity allows you to connect your Kubernetes Service Accounts (KSAs) to your Google Cloud Service Accounts (GSAs).

If you set the `workload-pool` parameter correctly when creating your K8s cluster, which you should have if you followed the instructions outlined in this README, then K8s workload identity should already be enabled for your cluster. Additional steps are required, however, for you to make your API calls.

1. You'll first need to identify the **KSA** and **namespace** that your Kubeflow workload is using. For example, if you want to make API calls from a hosted Jupyter Notebook, you'll need to double check the configuration of the notebook server in order to determine the KSA and namespace that it is using.
1. Next, you'll need the **email address** of a Google Cloud service account that has the appropriate IAM roles to perform your desired API calls.
1. Once you've obtained the three pieces of information outlined above, you'll then need to add an IAM policy binding to allow the KSA you identified earlier to impersonate the GSA. You'll need both the KSA as well as the Kubeflow namespace in order to do this.
1. Finally, you'll need to add an annotation to the KSA using the email address of the GSA.

An example is shown below:
```bash
export PROJECT_ID=${PROJECT_ID}
export KSA_NAME="default"
export K8S_NAMESPACE="default"
export GSA_NAME="kubeflow-notebooks"

# Add IAM policy binding using gcloud
gcloud iam service-accounts add-iam-policy-binding ${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${KSA_NAME}]"

# Add annotation using kubectl
kubectl annotate serviceaccount ${KSA_NAME} \
    --namespace ${K8S_NAMESPACE} \
    iam.gke.io/gcp-service-account=${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

### Manual Deployment Steps
The following steps below are automatically run in the `setup.sh` script. They are included here for reader understanding:  

1. Authenticate `kubectl` to the newly created cluster (ensure that your `gcloud` instance is already authenticated to the correct project)
    ```bash
    gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=us-central1-c
    ```

2. Ensure the cluster is up and running
    ```bash
    kubectl get node
    ```

3.  Give your account permissions to perform all administrative actions needed
    
    > ***WARNING***: You will need the `container.clusterRoleBindings.create` permission to run the following command:
    > ```bash
    > kubectl create clusterrolebinding cluster-admin-binding \
    > --clusterrole=cluster-admin \
    > --user=${EMAIL_ADDRESS}
    > ```
    >

4. Port ranges that are opened in cluster creation:
    There's a many ports that need to be opened to allow the API server to communicate with the rest of the nodes. TCP Port List:
    * **istio**: 8080, 8443, 15010, 15012, 15014, 15017, 15020, 15021, 15443, 31400
    * **kfserving**: 6443, 8443, 9443
    * **kubeflow**: 8008, 8012, 8013, 8081, 8080, 9090, 9443

    ```bash
    gcloud compute firewall-rules update ${FIREWALL_RULE_NAME} \ 
    --allow tcp:10250,tcp:443,tcp:8443,tcp:8080,tcp:8008,tcp:8012,tcp:8013, \
    tcp:8081,tcp:9090,tcp:6443,tcp:9443,tcp:15010,tcp:15012,tcp:15014, \
    tcp:15017,tcp:15021,tcp:15443,tcp:31400
    ```

    *NOTE:* The above ports were obtained from a [thread](https://kubeflow.slack.com/archives/C7REE0ETX/p1632303621195500?thread_ts=1631168126.095600&cid=C7REE0ETX) on the official Kubeflow Slack channel


## Additional Resources
For further reading on how to set up a private GKE cluster with Kubeflow see [this article](https://medium.com/dkatalis/installing-kubeflow-1-3-on-an-existing-and-private-gke-cluster-895283d49ed1).