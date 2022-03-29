from typing import NamedTuple


def prep_data(
    input_path: str,
    train_dir: str,
    test_dir: str,
    target: list = "is_bad",
    seed: int = 20,
) -> NamedTuple(
    "Outputs",
    [
        ("xtrain_path", str),
        ("xtest_path", str),
        ("ytrain_path", str),
        ("ytest_path", str),
    ],
):

    import logging
    import pandas as pd
    import numpy as np
    from sklearn import preprocessing
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from collections import namedtuple

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
    df["delinq_2yrs"] = df.delinq_2yrs.fillna(0)
    df["inq_last_6mths"].fillna(0, inplace=True)
    df["mths_since_last_delinq"].fillna(0, inplace=True)
    df["mths_since_last_record"].max()
    df["mths_since_last_record"].fillna(df.mths_since_last_record.max(), inplace=True)
    df["mths_since_last_record"] = df["mths_since_last_record"].astype(int)
    df["pub_rec"].fillna(0, inplace=True)
    df["pub_rec"] = df["pub_rec"].astype(int)
    df.earliest_cr_line = pd.to_datetime(df.earliest_cr_line)
    df["cr_line_yrs"] = df.earliest_cr_line.dt.year
    df["cr_line_mths"] = df.earliest_cr_line.dt.month
    df["cr_line_days"] = df.earliest_cr_line.dt.day
    df.drop("cr_line_days", axis=1, inplace=True)
    df.drop("earliest_cr_line", axis=1, inplace=True)
    df["cr_line_mths"].fillna(df.cr_line_mths.mode()[0], inplace=True)
    df["cr_line_mths"] = df["cr_line_mths"].astype(int)
    df.drop("collections_12_mths_ex_med", axis=1, inplace=True)
    df["annual_inc"].fillna(df.annual_inc.median(), inplace=True)
    df["open_acc"].fillna(df.open_acc.median(), inplace=True)
    df["revol_util"].fillna(df.revol_util.median(), inplace=True)
    df["total_acc"].fillna(df.total_acc.median(), inplace=True)
    df["cr_line_yrs"].fillna(df.cr_line_yrs.median(), inplace=True)
    df.drop("zip_code", axis=1, inplace=True)

    # Define the features and target
    logger.info("Creating features and target...")
    num_cols = list(df._get_numeric_data().columns)
    cat_cols = list(set(df.columns) - set(df._get_numeric_data().columns))
    num_cols.remove(target)

    # Log transform some of the numeric features
    def log_trans(x):
        return np.log(x + 1)

    temp_cols = num_cols.copy()
    temp_cols.remove("debt_to_income")
    temp_cols.remove("revol_util")

    df[temp_cols] = df[temp_cols].apply(log_trans)

    # Label and OH encoding

    count = 0
    for col in df:
        if df[col].dtype == "object":
            if len(list(df[col].unique())) <= 2:
                le = preprocessing.LabelEncoder()
                df[col] = le.fit_transform(df[col])
                count += 1
                logger.info(f"Encoding the following column: {col}")

    df = pd.get_dummies(df)

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
    xtrain_path = f"{train_dir}/Xtrain.npz"
    ytrain_path = f"{train_dir}/ytrain.npz"

    xtest_path = f"{test_dir}/Xtest.npz"
    ytest_path = f"{test_dir}/ytest.npz"

    np.savez_compressed(xtrain_path, X_train)
    np.savez_compressed(ytrain_path, y_train)
    
    np.savez_compressed(xtest_path, X_test)
    np.savez_compressed(ytest_path, y_test)

    output = namedtuple(
        "Outputs", ["xtrain_path", "xtest_path", "ytrain_path", "ytest_path"]
    )
    return output(xtrain_path, xtest_path, ytrain_path, ytest_path)


def train(
    Xtrain_path: str,
    ytrain_path: str,
    model_dir: str,
    target: list = "is_bad",
    seed: int = 20,
) -> NamedTuple(
    "Outputs",
    [("model_path", str)],
):
    pass


def eval():
    pass

