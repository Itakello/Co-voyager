from voyager import Voyager

# You can also use mc_port instead of azure_login, but azure_login is highly recommended
azure_login = {
    "client_id": "1f118a64-7c94-4ee0-8537-0c844b91b97b",
    "redirect_url": "https://127.0.0.1/auth-response",
    "secret_value": "",
    "version": "fabric-loader-0.14.18-1.19",
}
openai_api_key = "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"

voyager = Voyager(
    azure_login=azure_login,
    openai_api_key=openai_api_key,
)

# start lifelong learning
voyager.learn()
