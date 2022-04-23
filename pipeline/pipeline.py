import kfp.dsl as dsl
from kfp.dsl import get_pipeline_conf
from kfp.compiler import Compiler
from kfp.components import create_component_from_func
from components.tasks import prep_data, train, eval
from kf_utils.client import get_client
import datetime
import logging

logger = logging.basicConfig(level=logging.INFO)

NAMESPACE = "kubeflow-user-example-com"
ENDPOINT = "http://127.0.0.1:8080"

prep_data_func = create_component_from_func(
    prep_data,
    output_component_file="components/prep_data.yaml",
    base_image="gcr.io/my-org/my-image-name:latest",
)

train_func = create_component_from_func(
    train,
    output_component_file="components/train.yaml",
    base_image="gcr.io/my-org/my-image-name:latest",
)

eval_func = create_component_from_func(
    eval,
    output_component_file="components/eval.yaml",
    base_image="gcr.io/my-org/my-image-name:latest",
)


@dsl.pipeline(
    name="Training Pipeline",
    description="Simple Example of a Kubeflow Training Pipeline",
)
def train_pipeline(
    raw_data: str,
    bucket: str,
    model_dir: str,
):

    # Set to always retrieve the image from the registry
    get_pipeline_conf().set_image_pull_policy("Always")

    # Prepare the data
    prep_data_op = prep_data_func(
        raw_data,
        bucket,
    )
    prep_data_op.execution_options.caching_strategy.max_cache_staleness = "P0D"

    # Train on the prepared data
    train_lgbm_op = train_func(
        bucket,
        prep_data_op.outputs["train_path"],
        model_dir,
    )
    train_lgbm_op.execution_options.caching_strategy.max_cache_staleness = "P0D"

    # Evaluate the prepared data
    eval_lgbm_op = eval_func(
        bucket,
        model_path=train_lgbm_op.output,
        test_path=prep_data_op.outputs["test_path"],
    )
    eval_lgbm_op.execution_options.caching_strategy.max_cache_staleness = "P0D"


arguments = {
    "raw_data": "gs://amazing-public-data/lending_club/lending_club_data.tsv",
    "bucket": "mw-mlops-example-data",
    "model_dir": "model",
}

client = get_client(ENDPOINT, NAMESPACE, "user@example.com")
Compiler().compile(train_pipeline, "pipeline.tar.gz")
response = client.create_run_from_pipeline_package(
    "pipeline.tar.gz",
    run_name=f"lgbm-run-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    arguments=arguments,
    experiment_name="default",
    namespace="kubeflow-user-example-com",
)
logging.info(response)
