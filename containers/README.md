# Creating Containers

## AWS Elastic Container Registry
Before you can push your image to AWS ECR, you need to first login to the registry via your local Docker runtime. You will need either to create or use an existing ECR registry. In this example, I created a private registry called `kubeflow-demo-v14`.

```
domain="195565468328.dkr.ecr.us-east-1.amazonaws.com/kubeflow-demo-v14"
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${domain}
```

To push the image, modify the `build_image.sh` script and run it with the following (ensure it is exectuble, e.g. `chmod +x`):

```
./build_image.sh
```

## GCP Container Registry
TODO

## MicroK8s Local Registry
TODO