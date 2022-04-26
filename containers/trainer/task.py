import logging
import sys
import fire
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import numpy as np
from kf_utils.aws import download_blob

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def run(train_path, bucket, **kwargs):

    logger.info(train_path)
    logger.info(bucket)
    logger.info(kwargs)

    # Download the dataset
    try:
        train_path_local = "train.npz"
        download_blob(bucket, train_path, train_path_local)
    except:
        logger.warning("Unable to local dataset in AWS... trying locally")

    # Load the dataset
    logger.info("Load the dataset...")
    X_data = np.load(train_path_local)["xtrain"]
    y_data = np.load(train_path_local)["ytrain"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_data, y_data, test_size=0.2, random_state=20
    )
    logger.debug((X_train.shape, X_test.shape, y_train.shape, y_test.shape))

    clf = RandomForestClassifier(**kwargs)
    clf.fit(X_train, y_train)

    y_preds = clf.predict_proba(X_test)[:, 1]
    auc_metric = roc_auc_score(y_test, y_preds)
    logger.debug(auc_metric)
    print(f"auc={auc_metric}")


if __name__ == "__main__":
    fire.Fire(run)
