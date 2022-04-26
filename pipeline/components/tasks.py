from typing import NamedTuple
from kfp.components import OutputPath


def prep_data(
    input_path: str,
    bucket: str,
    target: str = "is_bad",
    features: list = ["annual_inc", "revol_util"],
    seed: int = 20,
    cloud_type: str = "aws",
) -> NamedTuple("Outputs", [("train_path", str), ("test_path", str)],):

    import logging
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from collections import namedtuple
    from os import mkdir

    if cloud_type == "aws":
        from kf_utils.aws import upload_blob
    elif cloud_type == "gcs":
        from kf_utils.gcs import upload_blob
    else:
        raise Exception("Invalid cloud option")

    pd.options.mode.use_inf_as_na = True

    # Set up logging
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Read in the data
    logger.info(f"Reading in data file {input_path}...")
    df = pd.read_csv(input_path, sep="\t")

    # Initial data prep
    logger.info("Feature engineering...")
    df = df[features + [target]]
    df["annual_inc"].fillna(df.annual_inc.median(), inplace=True)
    df["revol_util"].fillna(df.revol_util.median(), inplace=True)

    # Define the features and target
    logger.info("Creating features and target...")
    num_cols = list(df._get_numeric_data().columns)
    num_cols.remove(target)

    # Log transform some of the numeric features
    def log_trans(x):
        return np.log(x + 1)

    temp_cols = num_cols.copy()
    temp_cols.remove("revol_util")
    df[temp_cols] = df[temp_cols].apply(log_trans)

    # Split out the data
    logger.info("Splitting the data...")
    X_train, X_test, y_train, y_test = train_test_split(
        df.drop(target, axis=1), df[target], test_size=0.20, random_state=seed
    )

    # Standard scale the numeric data
    logger.info("Scaling the numeric data...")
    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    # Save the data
    logger.info("Saving the data...")
    try:
        mkdir("./data")
    except FileExistsError:
        logger.warn("folder already exists.")

    train_path_local = "train.npz"
    test_path_local = "test.npz"

    train_path = f"data/{train_path_local}"
    test_path = f"data/{test_path_local}"

    np.savez_compressed(file=train_path_local, xtrain=X_train, ytrain=y_train)
    np.savez_compressed(file=test_path_local, xtest=X_test, ytest=y_test)

    upload_blob(bucket, train_path_local, train_path)
    upload_blob(bucket, test_path_local, test_path)

    output = namedtuple("Outputs", ["train_path", "test_path"])
    return output(train_path, test_path)


def train(
    bucket: str,
    train_path: str,
    model_dir: str,
    cloud_type: str = "aws",
    params: dict = {"objective": "binary", "seed": 20},
) -> str:

    from sklearn.ensemble import RandomForestClassifier
    import logging
    from datetime import datetime
    import numpy as np
    from joblib import dump

    if cloud_type == "aws":
        from kf_utils.aws import upload_blob, download_blob
    elif cloud_type == "gcs":
        from kf_utils.gcs import upload_blob, download_blob
    else:
        raise Exception("Invalid cloud option")

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    # Download the dataset to the container
    train_path_local = "train.npz"
    download_blob(bucket, train_path, train_path_local)

    # Load the training dataset
    logger.info("Load the dataset...")
    X_train = np.load(train_path_local)["xtrain"]
    y_train = np.load(train_path_local)["ytrain"]

    # Set up the model params
    logger.info("Begin training...")
    params = {
        "n_estimators": 100,
        "max_depth": 4,
    }
    clf = RandomForestClassifier(**params)
    clf.fit(X_train, y_train)

    # Save the trained model for evaluation
    logger.info("Saving the model...")
    local_model_path = "./rfclf-model.joblib"
    dump(clf, local_model_path)
    model_path = (
        f"{model_dir}/rfc-model-{datetime.now().strftime('%Y%m%d%H%M%S')}.joblib"
    )
    upload_blob(bucket, local_model_path, model_path)

    return model_path


def eval(
    bucket: str,
    model_path: str,
    test_path: str,
    mlpipeline_metrics: OutputPath("Metrics"),
    cloud_type: str = "aws",
    target: str = "is_bad",
    seed: int = 20,
):

    import numpy as np
    from sklearn.metrics import roc_auc_score
    from kf_utils.gcs import download_blob
    import logging
    import json
    from joblib import load

    if cloud_type == "aws":
        from kf_utils.aws import upload_blob, download_blob
    elif cloud_type == "gcs":
        from kf_utils.gcs import upload_blob, download_blob
    else:
        raise Exception("Invalid cloud option")

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Load the data
    local_data_path = "test.npz"
    logger.info("Loading test data...")
    download_blob(bucket, test_path, local_data_path)

    X_test = np.load(local_data_path)["xtest"]
    y_test = np.load(local_data_path)["ytest"]

    # Load model
    local_model_path = "model.joblib"
    logger.info("Loading the model...")
    download_blob(bucket, model_path, local_model_path)

    clf = load(local_model_path)

    # Evaluate the model
    y_preds = clf.predict(X_test)
    auc_metric = roc_auc_score(y_test, y_preds)
    logging.info(f"AUC Score {auc_metric}")

    # Log the metrics
    metrics = {
        "metrics": [
            {
                "name": "auc-score",
                "numberValue": round(auc_metric, 3),
                "format": "RAW",
            }
        ]
    }

    with open(mlpipeline_metrics, "w") as f:
        json.dump(metrics, f)


def generate_serve_manifest(
    model_name: str, storage_uri: str, inference_type: str = "lightgbm"
) -> dict:
    manifest = {
        "apiVersion": "serving.kserve.io/v1beta1",
        "kind": "InferenceService",
        "metadata": {"name": model_name},
        "spec": {"predictor": {inference_type: {"storageUri": storage_uri}}},
    }

    return manifest


if __name__ == "__main__":
    pass