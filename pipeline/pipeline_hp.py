import kfp
import kfp.dsl as dsl
from kfp.dsl import get_pipeline_conf
from kfp.compiler import Compiler
from kfp.components import create_component_from_func
from components.tasks import prep_data, train, eval
from kf_utils.client import get_client
import datetime
import logging
from kubeflow.katib import (
    ApiClient,
    V1beta1AlgorithmSpec,
    V1beta1EarlyStoppingSetting,
    V1beta1EarlyStoppingSpec,
    V1beta1ExperimentSpec,
    V1beta1FeasibleSpace,
    V1beta1ObjectiveSpec,
    V1beta1ParameterSpec,
    V1beta1TrialParameterSpec,
    V1beta1TrialTemplate,
)

NAMESPACE = "kubeflow-user-example-com"
ENDPOINT = "http://127.0.0.1:8080"
BASE_IMAGE = "195565468328.dkr.ecr.us-east-1.amazonaws.com/kubeflow-demo-v14:v1"
BUCKET = "kubeflow-demo-v14"
TRAIN_PATH = "data/train.npz"

# HP Tuning Spec
# Experiment name and namespace.
experiment_name = f"hptune-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
experiment_namespace = "kubeflow-user-example-com"

# Trial count specification.
max_trial_count = 10
max_failed_trial_count = 0
parallel_trial_count = 2

# Objective specification.
objective = V1beta1ObjectiveSpec(
    type="maximize",
    objective_metric_name="auc",
)

# Algorithm specification.
algorithm = V1beta1AlgorithmSpec(
    algorithm_name="random",
)

# Experiment search space.
# In this example we tune learning rate, number of layer and optimizer.
# Learning rate has bad feasible space to show more early stopped Trials.
parameters = [
    V1beta1ParameterSpec(
        name="n_estimators",
        parameter_type="int",
        feasible_space=V1beta1FeasibleSpace(min="10", max="1000"),
    ),
    V1beta1ParameterSpec(
        name="max_depth",
        parameter_type="int",
        feasible_space=V1beta1FeasibleSpace(min="5", max="20"),
    ),
]

# JSON template specification for the Trial's Worker Kubernetes Job.
trial_spec = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "spec": {
        "template": {
            "metadata": {"annotations": {"sidecar.istio.io/inject": "false"}},
            "spec": {
                "containers": [
                    {
                        "name": "training-container",
                        "image": BASE_IMAGE,
                        "command": [
                            "python3",
                            "/app/trainer/task.py",
                            f"--train_path='{TRAIN_PATH}'",
                            f"--bucket='{BUCKET}'",
                            "--n_estimators=${trialParameters.nEstimators}",
                            "--max_depth=${trialParameters.maxDepth}",
                        ],
                    }
                ],
                "restartPolicy": "Never",
            },
        }
    },
}

# Configure parameters for the Trial template.
# We set the retain parameter to "True" to not clean-up the Trial Job's Kubernetes Pods.
trial_template = V1beta1TrialTemplate(
    retain=True,
    primary_container_name="training-container",
    trial_parameters=[
        V1beta1TrialParameterSpec(
            name="nEstimators",
            description="number of trees in the forest",
            reference="n_estimators",
        ),
        V1beta1TrialParameterSpec(
            name="maxDepth",
            description="max depth of the tree",
            reference="max_depth",
        ),
    ],
    trial_spec=trial_spec,
)

experiment_spec = V1beta1ExperimentSpec(
    max_trial_count=max_trial_count,
    max_failed_trial_count=max_failed_trial_count,
    parallel_trial_count=parallel_trial_count,
    objective=objective,
    algorithm=algorithm,
    parameters=parameters,
    trial_template=trial_template,
)

# Get the Katib launcher.
katib_experiment_launcher_op = kfp.components.load_component_from_url(
    "https://raw.githubusercontent.com/kubeflow/pipelines/master/components/kubeflow/katib-launcher/component.yaml"
)


# Create the HP Tuning Pipeline
@dsl.pipeline(
    name="Launch Katib Experiment",
    description="An example to launch Katib Experiment",
)

def trial_run():
    # Katib launcher component.
    # Experiment Spec should be serialized to a valid Kubernetes object.

    # Set to always retrieve the image from the registry
    get_pipeline_conf().set_image_pull_policy("Always")

    op = katib_experiment_launcher_op(
        experiment_name=experiment_name,
        experiment_namespace=experiment_namespace,
        experiment_spec=ApiClient().sanitize_for_serialization(experiment_spec),
        experiment_timeout_minutes=60,
        delete_finished_experiment=False,
    )


client = get_client(ENDPOINT, NAMESPACE, "user@example.com")
Compiler().compile(trial_run, "pipeline_hp.tar.gz")
response = client.create_run_from_pipeline_package(
    "pipeline_hp.tar.gz",
    run_name=f"rfc-hp-run-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    arguments={},
    experiment_name="rfc-test",
    namespace="kubeflow-user-example-com",
)
print(response)
