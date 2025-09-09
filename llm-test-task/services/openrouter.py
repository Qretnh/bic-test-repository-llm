import httpx


class OpenRouterManager:
    def __init__(self):
        self.models = self._find_openrouter_models()
        self.model_names = [model["id"] for model in self.models]

    def get_model_names(self):
        return self.model_names

    @staticmethod
    def filter_free_models(models: list) -> list:
        result = []
        for model in models:
            if (
                "text" in model["architecture"]["input_modalities"]
                and "text" in model["architecture"]["output_modalities"]
            ):
                for type in model["pricing"]:
                    if model["pricing"][type] != 0:
                        break
                result.append(model)
        return result

    @staticmethod
    def _find_openrouter_models(free=True) -> list:
        models = httpx.get("https://openrouter.ai/api/v1/models").json()["data"]
        if free:
            models = OpenRouterManager.filter_free_models(models)
        return models

    def check_correct_model(self, model: str) -> bool:
        return model in self.model_names


models_manager = OpenRouterManager()


def get_models_manager() -> OpenRouterManager:
    return models_manager
