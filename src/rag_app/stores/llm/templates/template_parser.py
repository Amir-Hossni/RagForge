from pathlib import Path
from importlib import import_module
from string import Template

class TemplateParser:

    
    def __init__(self, language: str = None, default_language: str = "en"):
        self.current_path = Path(__file__).resolve().parent
        self.locales_path = self.current_path / "locales"

        self.default_language = default_language
        self.language = None

        self.set_language(language=language)

    def _get_group_path(self, group: str, language: str) -> Path:
        return self.locales_path / language / f"{group}.py"

    def set_language(self, language: str = None):

        if not language:
            self.language = self.default_language
            return

        language_path = self.locales_path / language

        if language_path.is_dir():
            self.language = language
        else:
            self.language = self.default_language

    def get(self, group: str, key: str, vars: dict = None):

        if not group or not key:
            raise ValueError("Both 'group' and 'key' are required.")

        target_language = self.language
        group_path = self._get_group_path(group=group, language=target_language)

        if not group_path.is_file():
            target_language = self.default_language
            group_path = self._get_group_path(group=group, language=target_language)

        if not group_path.is_file():
            raise FileNotFoundError(
                f"Prompt group '{group}' was not found "
                f"for language '{self.language}' "
                f"or default language '{self.default_language}'."
            )

        module_path = (
            f"src.rag_app.stores.llm.templates.locales."
            f"{target_language}.{group}"
        )

        module = import_module(module_path)

        key_attribute = getattr(module, key, None)

        if key_attribute is None:
            raise AttributeError(
                f"Prompt '{key}' was not found in group '{group}' "
                f"for language '{target_language}'."
            )

        if not isinstance(key_attribute, Template):
            raise TypeError(
                f"Prompt '{key}' in group '{group}' must be a Template."
            )

        if vars is None:
            vars = {}

        return key_attribute.substitute(vars)

 