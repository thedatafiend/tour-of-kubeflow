# Model Serving with KServe or KFServing

> ***NOTE*** Due to some issues still being experienced with `KServe v0.7`, this example uses `KFServing v0.6`. The experience is nearly identical between the two versions.

## Reference for Sample Inference Service
This simple example shows you how to deploy a model in an `Istio-Dex` environment. The biggest note is that the following annotation `sidecar.istio.io/inject: "false"` ensures that an `istio` proxy does not get deployed as a sidecar to the inference service. For further details, see this [link](https://github.com/kubeflow/kfserving-lts/tree/release-0.6/docs/samples/istio-dex)

## Running this Example
In order to run this example, you first need to deploy the sample inference service using `kubectl`:

```
kubectl apply -f sample_sklearn.yaml
```

The expected output is:
```
$ inferenceservice.serving.kubeflow.org/sklearn-iris created
```

It will take a minute or two for the example to come up. 

> ***NOTE*** You may run into an auto-scaling issue. Correct this by increasing the number of nodes in your cluster using a command similar to that found in the deployment examples. For example, on EKS to increase the number of nodes to 4 `eksctl scale nodegroup --cluster kubeflow-deployment --name kubeflow-mng -r ${CLUSTER_REGION} --nodes 4 --nodes-min 0 --nodes-max 4`

Once the model has been deployed fully, you can check it's status under "Models" in the KF UI. Then, you can test the service by running the following:

```
python prediction_script.py
```

The example assumes you are port-forwarding the `Dex` ingress service to `localhost:8080` (which you would be if you have already deployed the `pipelines` example in this repo), that you the user namespace of `kubeflow-user-example-com`, and that you have a standard python environment installed.