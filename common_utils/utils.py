import os


def parse_json(result):
    if result.startswith("```"):
        return "\n".join(result.split("\n")[1:-1])
    if not result.startswith("{"):
        start_index = result.find("```json")
        if start_index != -1:
            start_index += len("```json\n")
            end_index = result.find("```", start_index)
            return result[start_index:end_index].strip()
    return result


def get_env_var(name):
    return os.getenv(name)
