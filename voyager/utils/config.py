import configparser
import os

import voyager.utils as U

# Load configuration from INI file
config = configparser.ConfigParser()
config.read("config.ini")


def set_openai_config():
    os.environ["OPENAI_API_VERSION"] = config.get("gpt4_client", "api_version")
    os.environ["OPENAI_API_KEY"] = config.get("gpt35_client", "api_key")
    os.environ["AZURE_OPENAI_ENDPOINT"] = config.get("gpt4_client", "azure_endpoint")
    os.environ["AZURE_OPENAI_API_KEY"] = config.get("gpt4_client", "api_key")


def get_azure_login():
    azure_login = {
        "client_id": config.get("azure_login", "client_id"),
        "redirect_url": config.get("azure_login", "redirect_url"),
        "secret_value": config.get("azure_login", "secret_value"),
        "version": config.get("azure_login", "version"),
    }
    return azure_login


def reset_worlds():
    U.file_utils.f_remove(
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat"
    )
    U.file_utils.f_copy(
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat-template",
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat",
    )


def backup_world():
    U.file_utils.f_copy(
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat",
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat-backup",
    )


def restore_world():
    U.file_utils.f_remove(
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat"
    )
    U.file_utils.f_copy(
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat-backup",
        "C:\\Users\\maxst\\AppData\\Roaming\\.minecraft\\saves\\Superflat",
    )
