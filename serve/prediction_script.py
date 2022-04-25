import re
import json
import requests


# Get Predictions
def get_preds(sess, model_name, input_path, cluster_ip, hostname, session):
    print("Requesting prediction...")
    endpoint = f"http://{cluster_ip}/v1/models/{model_name}:predict"
    out = sess.post(
        endpoint,
        headers={"Host": hostname, "Cookie": f"authservice_session={session}"},
        data=open(input_path),
    )
    print(out)
    print(out.text)
    pred_output = json.loads(out.text)
    print(f"\nPredictions: {pred_output['predictions']}")


# Get Session
def get_session(cluster_ip):
    sess = requests.Session()
    sess_res = sess.get(f"http://{cluster_ip}")

    # req number
    req = re.search(
        pattern=".*req=([A-z0-9_-]+)", string=sess_res.history[-1].text
    ).groups(1)[0]

    # login
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"login": "user@example.com", "password": "12341234"}
    url3 = f"http://{cluster_ip}/dex/auth/local?req={req}"
    sess_res = sess.post(url3, headers=headers, data=data)
    return (sess, sess_res)


if __name__ == "__main__":
    CLUSTER_IP = "localhost:8080"
    MODEL_NAME = "sklearn-iris"
    INPUT_PATH = "./iris-input.json"
    SERVICE_HOSTNAME = "sklearn-iris.kubeflow-user-example-com.example.com"
    namespace = "kubeflow-user-example-com"
    # get session
    sess, sess_res = get_session(CLUSTER_IP)
    SESSION = sess_res.history[2].cookies["authservice_session"]
    # get preds
    get_preds(sess, MODEL_NAME, INPUT_PATH, CLUSTER_IP, SERVICE_HOSTNAME, SESSION)
