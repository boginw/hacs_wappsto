import json
import logging
from pathlib import Path

import requests

from .const import (
    CA_CRT_KEY,
    CLIENT_CRT_KEY,
    CLIENT_KEY_KEY,
)

_LOGGER = logging.getLogger(__name__)


def get_session(username, password):
    session_json = {"username": username, "password": password, "remember_me": True}

    url = f"https://wappsto.com/services/session"
    headers = {"Content-type": "application/json"}
    data = json.dumps(session_json)

    rdata = requests.post(url=url, headers=headers, data=data)

    if rdata.status_code >= 300:
        _LOGGER.error("An error occurred during login")
        return None

    rjson = json.loads(rdata.text)
    _LOGGER.info(rjson)
    return rjson["meta"]["id"]


def create_network(session):
    request = {}

    url = f"https://wappsto.com/services/2.1/creator"
    headers = {"Content-type": "application/json", "X-session": str(session)}
    data = json.dumps(request)
    rdata = requests.post(url=url, headers=headers, data=data)

    if rdata.status_code >= 300:
        _LOGGER.error("An error occurred during Certificate retrieval")
        return None
    rjson = json.loads(rdata.text)
    _LOGGER.info("Certificate generated for new network")
    return rjson


def claim_network(session, network_uuid, dry_run=False):
    url = f"https://wappsto.com/services/2.0/network/{network_uuid}"
    headers = {"Content-type": "application/json", "X-session": str(session)}
    rdata = requests.post(url=url, headers=headers, data="{}")

    if rdata.status_code >= 300:
        _LOGGER.error("An error occurred during claiming the network")
        return None

    rjson = json.loads(rdata.text)
    _LOGGER.info("Network: %s have been claimed", network_uuid)
    return rjson


def delete_certificate_files() -> None:
    ca_file = Path(__file__).with_name("ca.crt")
    client_crt_file = Path(__file__).with_name("client.crt")
    client_key_file = Path(__file__).with_name("client.key")
    ca_file.unlink()
    client_crt_file.unlink()
    client_key_file.unlink()


def create_certificaties_files_if_not_exist(creator) -> bool:
    ca_file = Path(__file__).with_name("ca.crt")
    client_crt_file = Path(__file__).with_name("client.crt")
    client_key_file = Path(__file__).with_name("client.key")

    if ca_file.exists() and client_crt_file.exists() and client_key_file.exists():
        _LOGGER.info("All certificates exists")
        return True

    try:
        with ca_file.open("w") as file:
            file.write(creator[CA_CRT_KEY])
        with client_crt_file.open("w") as file:
            file.write(creator[CLIENT_CRT_KEY])
        with client_key_file.open("w") as file:
            file.write(creator[CLIENT_KEY_KEY])
        return True
    except Exception as err:
        _LOGGER.error("An error occurred while saving Certificates: %s", err)
        return False
