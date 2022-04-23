from typing import NamedTuple
from kfp.components import OutputPath


def prep_data(
    input_path: str,
    bucket: str,
    target: str = "is_bad",
    features: list = ["annual_inc", "revol_util"],
    seed: int = 20,
) -> NamedTuple("Outputs", [("train_path", str), ("test_path", str)],):

    import logging
    import pandas as pd
    import numpy as np
    import lightgbm as lgbm
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from collections import namedtuple
    from kf_utils.gcs import upload_blob
    from os import mkdir

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

    train_path_local = "train.bin"
    test_path_local = "test.npz"

    train_path = f"data/{train_path_local}"
    test_path = f"data/{test_path_local}"

    dtrain = lgbm.Dataset(X_train, label=y_train)
    dtrain.save_binary(train_path_local)
    np.savez_compressed(file=test_path_local, xtest=X_test, ytest=y_test)

    upload_blob(bucket, train_path_local, train_path)
    upload_blob(bucket, test_path_local, test_path)

    output = namedtuple("Outputs", ["train_path", "test_path"])
    return output(train_path, test_path)


def train(
    bucket: str,
    train_path: str,
    model_dir: str,
    gcp_project: bool = True,
    params: dict = {"objective": "binary", "seed": 20}
) -> str:

    import lightgbm as lgbm
    from kf_utils.gcs import download_blob, upload_blob
    import logging
    from datetime import datetime

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Download the dataset to the container
    train_path_local = "train.bin"

    if gcp_project:
        download_blob(bucket, train_path, train_path_local)
    else:
        train_path_local = train_path

    # Load the training dataset
    logger.info("Load the dataset...")
    dtrain = lgbm.Dataset(data=train_path_local)
    dtrain.construct()

    # Set up the model params
    logger.info("Begin training...")
    params = {
        "num_leaves": 100,
        "learning_rate": 0.01,
        "num_iterations": 1000,
        "max_bin": 255,
        "objective": "binary",
        "seed": 20,
        "verbosity": 3,
    }
    model = lgbm.train(
        params=params,
        train_set=dtrain,
    )

    # Save the trained model for evaluation
    logger.info("Saving the model...")
    local_model_path = "./lgbm-model.txt"
    model.save_model(local_model_path)
    model_path = f"{model_dir}/lgbm-model-{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"

    if gcp_project:
        upload_blob(bucket, local_model_path, model_path)

    return model_path


def eval(
    bucket: str,
    model_path: str,
    test_path: str,
    mlpipeline_metrics: OutputPath('Metrics'),
    gcp_project: bool = True,
    target: str = "is_bad",
    seed: int = 20,
):

    import lightgbm as lgbm
    import numpy as np
    from sklearn.metrics import roc_auc_score
    from kf_utils.gcs import download_blob
    import logging
    import json

    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Load the data
    local_data_path = "test.npz"
    logger.info("Loading test data...")
    
    if gcp_project:
        download_blob(bucket, test_path, local_data_path)
    else:
        local_data_path = test_path
    
    X_test = np.load(local_data_path)["xtest"]
    y_test = np.load(local_data_path)["ytest"]

    # Load model
    local_model_path = "model.txt"
    logger.info("Loading the model...")
    if gcp_project:
        download_blob(bucket, model_path, local_model_path)
    else:
        local_model_path = model_path
    
    model = lgbm.Booster(model_file=local_model_path)

    # Evaluate the model
    y_preds = model.predict(X_test)
    auc_metric = roc_auc_score(y_test, y_preds)
    logging.info(f"AUC Score {auc_metric}")

    # Log the metrics
    metrics = {
        "metrics": [{
            "name": "auc-score",
            "numberValue": round(auc_metric, 3),
            "format": "RAW",
        }]
    }

    with open(mlpipeline_metrics, "w") as f:
        json.dump(metrics, f)


if __name__ == "__main__":
    train(
        bucket="",
        train_path="./dtrain.bin",
        model_dir="",
        gcp_project=False,
        target="is_bad",
        seed=20,
    )
