# # registry.py
# class ErrorRegistry:
#     def __init__(self):
#         self.errors = {}
#         self.load_yaml()

#     def load_yaml(self):
#         import importlib.resources as pkg_resources
#         import yaml

#         with pkg_resources.open_text("ora_exception_lib.resources", "exception-application.yml") as f:
#             data = yaml.safe_load(f)
#             self.errors = data.get("errors", {})

#     def get_error(self, key: str, lang: str = "en"):
#         data = self.errors.get(key)

#         if not data:
#             return Error(
#                 code="GENERIC_ERROR",
#                 category="GENERAL",
#                 message="Something went wrong",
#                 status=500,
#             )

#         # If YAML is nested (unused lang feature)
#         if isinstance(data, dict) and lang in data:
#             data = data[lang]

#         return Error(
#             code=data.get("code"),
#             category=data.get("category"),
#             message=data.get("message"),
#             status=data.get("status"),
#         )




# class Error:
#     def __init__(self, code, category, message, status):
#         self.code = code
#         self.category = category
#         self.message = message
#         self.status = status



# registry.py
import yaml
import importlib.resources as pkg_resources
from typing import Dict, Optional

class Error:
    def __init__(self, code: str, category: str, message: str, status: int):
        self.code = code
        self.category = category
        self.message = message
        self.status = status

class ErrorRegistry:
    def __init__(self):
        # errors: mapping from error code -> dict (code, category, message OR message_key, status)
        self.errors: Dict[str, Dict] = {}
        # messages: mapping lang -> mapping (message_key_or_code -> localized string)
        self.messages: Dict[str, Dict[str, str]] = {}
        self.load_yaml()

    def load_yaml(self):
        # load exception definitions
        with pkg_resources.open_text("ora_exception_lib.resources", "exception-application.yml") as f:
            data = yaml.safe_load(f) or {}
            self.errors = data.get("errors", {})

        # try to load localized messages files under resources/locale
        # expected names: messages_en.yml, messages_hi.yml, ...
        # If they don't exist it's fine — we fall back to literal messages in exception file.
        try:
            # list of languages you support (scan resources/locale). We try common names:
            locales = ["en", "hi"]
            for lang in locales:
                pkg = "ora_exception_lib.resources.locale"
                filename = f"messages_{lang}.yml"

                # filename = f"locale/messages_{lang}.yml"
                try:
                    with pkg_resources.open_text(pkg, filename) as mf:
                        mdata = yaml.safe_load(mf) or {}
                        # if file contains top-level mapping, use it directly
                        self.messages[lang] = mdata
                except FileNotFoundError:
                    # ignore missing locale file
                    self.messages[lang] = {}
        except Exception:
            # safe fallback, ensure at least empty dicts
            for l in ("en", "hi"):
                self.messages.setdefault(l, {})

    def get_error(self, key: str, lang: str = "en") -> Error:
        """
        Retrieve an Error object for 'key' and language 'lang'.
        Language resolution tries:
          1) messages[lang].get(key)   -> localized string keyed by error code
          2) messages[lang].get(message_key) -> if exception-application.yml uses 'message_key'
          3) fallback to literal message defined in exception-application.yml
          4) fallback to GENERIC_ERROR
        """
        lang = (lang or "en").split(",")[0].strip().lower()[0:2]

        data = self.errors.get(key)
        if not data:
            # fallback generic
            return Error(
                code="GENERIC_ERROR",
                category="GENERAL",
                message="Something went wrong",
                status=500,
            )

        # Determine message: prefer localized message files
        # 1) if messages[lang] contains the error code key, use it
        localized = self.messages.get(lang, {}).get(key)
        if localized:
            message = localized
        else:
            # 2) if exception data contains a message_key, try it
            message_key = data.get("message_key")
            if message_key:
                localized = self.messages.get(lang, {}).get(message_key)
                message = localized if localized else data.get("message", "")
            else:
                # 3) Try lookup by message text in messages (if message acts as key)
                candidate = data.get("message")
                if candidate and candidate in self.messages.get(lang, {}):
                    message = self.messages.get(lang, {}).get(candidate)
                else:
                    # literal fallback
                    message = data.get("message", "")

        return Error(
            code=data.get("code", key),
            category=data.get("category", "GENERAL"),
            message=message or "Something went wrong",
            status=int(data.get("status", 500)),
        )
