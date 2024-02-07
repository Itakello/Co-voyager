import configparser

from openai import AzureOpenAI, OpenAI

from voyager import Voyager

# Load configuration from INI file
config = configparser.ConfigParser()
config.read("config.ini")

azure_login = {
    "client_id": config.get("azure_login", "client_id"),
    "redirect_url": config.get("azure_login", "redirect_url"),
    "secret_value": config.get("azure_login", "secret_value"),
    "version": config.get("azure_login", "version"),
}

gpt4_client = AzureOpenAI(
    azure_endpoint=config.get("gpt4_client", "azure_endpoint"),
    azure_deployment=config.get("gpt4_client", "azure_deployment"),
    api_key=config.get("gpt4_client", "api_key"),
    api_version=config.get("gpt4_client", "api_version"),
)

gpt35_client = OpenAI(
    api_key=config.get("gpt35_client", "api_key"),
    model=config.get("gpt35_client", "model"),
)

voyager = Voyager(
    azure_login=azure_login,
    gpt35_client=gpt35_client,
    gpt4_client=gpt4_client,
)

# start lifelong learning
voyager.learn()
