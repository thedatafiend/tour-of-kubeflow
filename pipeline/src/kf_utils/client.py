import requests
import re
import getpass
from kfp import Client
from typing import Union


def get_client(
    kf_endpoint: str,
    namespace: str,
    username: Union[str, None] = None,
    password: Union[str, None] = None,
):
    """Get an authorized kfp client

    Args:
        kf_endpoint (str): The KFP endpoint (e.g. http://localhost:8080)
        namespace (str): The user's namespace (e.g. kubeflow-user-example-com)
        username (Union[str, None], optional): The user id or email (e.g. user@example.com). Defaults to None.
        password (Union[str, None], optional): The user password (e.g. 12341234). Defaults to None.

    Returns:
        kfp.Client: The KFP Client with an authorized session key
    """
    # get session
    sess = requests.Session()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    # login
    res = sess.get(kf_endpoint)
    req = re.search(pattern=".*req=([A-z0-9_-]+)", string=res.history[-1].text).groups(
        1
    )[0]
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    uname = username if username else getpass.getuser()
    pword = password if password else getpass.getpass("Password: ")
    data = {"login": uname, "password": pword}
    url3 = f"{kf_endpoint}/dex/auth/local?req={req}"
    sess.post(url3, headers=headers, data=data)
    
    # attach session cookie to new client
    cookie = sess.cookies.get_dict()["authservice_session"]

    client = Client(
        host=kf_endpoint.rstrip("/") + "/pipeline",
        cookies=f"authservice_session={cookie}",
        namespace=namespace,
    )
    return client
