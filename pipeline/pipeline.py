import kfp
import kfp.dsl as dsl
from kfp.compiler import Compiler
from kfp.components import create_component_from_func
from components.tasks import prep_data, train

NAMESPACE = "kubeflow-user-example-com"
ENDPOINT = "http://localhost:8080"

prep_data_func = create_component_from_func(
    prep_data, output_component_file="components/prep_data.yaml", base_image=""
)

train_func = create_component_from_func(
    train, output_component_file="components/train.yaml", base_image=""
)


@dsl.pipeline(
    name="Training Pipeline",
    description="Simple Example of a Kubeflow Training Pipeline",
)
def train_pipeline(
    raw_data: str = "",
    bucket: str = "",
    model_dir: str = "",
):

    # Prepare the data
    prep_data_op = prep_data_func(
        raw_data,
        bucket,
    )

    # Train on the prepared data
    train_lgbm_op = train_func(
        bucket,
        prep_data_op.outputs["xtrain_path"],
        prep_data_op.outputs["ytrain_path"],
        model_dir,
    )


arguments = {
    "raw_data": "gs://amazing-public-data/lending_club/lending_club_data.tsv",
    "bucket": "mw-mlops-example-data",
    "model_dir": "model/",
}

client = kfp.Client(host=ENDPOINT, namespace=NAMESPACE)
Compiler().compile(train_pipeline, "pipeline.tar.gz")
response = client.create_run_from_pipeline_package(
    "pipeline.tar.gz",
    arguments=arguments,
    experiment_name="default",
    namespace="kubeflow-user-example-com",
)
print(response)
