import pkg_resources

import voyager.utils as U


def load_prompt(prompt) -> str:
    package_path = pkg_resources.resource_filename("voyager", "")
    prompt = U.load_text(f"{package_path}/prompts/{prompt}.txt")
    return str(prompt)
