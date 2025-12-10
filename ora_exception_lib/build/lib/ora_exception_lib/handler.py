# from fastapi import Request
# from fastapi.responses import JSONResponse

# from .registry import ErrorRegistry
# from .errors import ErrorResponse


# class GlobalExceptionHandler:

#     def __init__(self, registry: ErrorRegistry):
#         self.registry = registry

#     def register(self, app):
       
#         @app.exception_handler(Exception)
#         async def handle_all_exceptions(request: Request, exc: Exception):

#             # Extract the actual error_code
#             if hasattr(exc, "error_code"):
#                 error_code = exc.error_code
#             elif exc.args:
#                 error_code = exc.args[0]    # <--- THIS FIXES YOUR ISSUE
#             else:
#                 error_code = "GENERIC_ERROR"

#             try:
#                 lang = request.headers.get("accept-language", "en")
#                 err = self.registry.get_error(error_code, lang=lang)
#             except Exception:
#                 err = self.registry.get_error("GENERIC_ERROR", "en")

#             response = ErrorResponse(
#                 code=err.code,
#                 category=err.category,
#                 message=err.message,
#                 status=err.status,
#             )

#             return JSONResponse(
#                 status_code=err.status,
#                 content=response.dict(),
#             )



# def register_exception_handler(app, registry=None):
#     """
#     Simple helper so client services can register exception handlers easily.
#     """
#     if registry is None:
#         # Automatically load registry from config
#         from .config import load_registry
#         registry = load_registry()

#     handler = GlobalExceptionHandler(registry)
#     handler.register(app)




# handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

from .registry import ErrorRegistry
from .errors import ErrorResponse

class GlobalExceptionHandler:

    def __init__(self, registry: ErrorRegistry):
        self.registry = registry

    def _extract_error_code(self, exc: Exception) -> str:
        # 1) If custom exception exposes attribute error_code
        code = getattr(exc, "error_code", None)
        if code:
            return str(code)

        # 2) If user raised Exception("SOME_CODE"), use the first arg
        if getattr(exc, "args", None):
            first = exc.args[0]
            # only accept if it looks like a code (string)
            if isinstance(first, str) and first.strip():
                return first.strip()

        # fallback
        return "GENERIC_ERROR"

    def _parse_lang(self, request: Request) -> str:
        # Accept-Language header: take first language token and first 2 letters
        lang = request.headers.get("accept-language", "en")
        # simple normalization; e.g. "hi-IN, en;q=0.8" -> "hi"
        try:
            first = lang.split(",")[0].strip().lower()
            return first[0:2]
        except Exception:
            return "en"

    def register(self, app):

        @app.exception_handler(Exception)
        async def handle_all_exceptions(request: Request, exc: Exception):
            error_code = self._extract_error_code(exc)

            try:
                lang = self._parse_lang(request)
                err = self.registry.get_error(error_code, lang=lang)
            except Exception:
                # Fallback if registry or messages broken
                err = self.registry.get_error("GENERIC_ERROR", lang="en")

            response = ErrorResponse(
                code=err.code,
                category=err.category,
                message=err.message,
                status=err.status,
            )

            return JSONResponse(
                status_code=err.status,
                content=response.dict(),
            )


def register_exception_handler(app, registry=None):
    """
    Simple helper so client services can register exception handlers easily.
    """
    if registry is None:
        # Automatically load registry from config
        from .config import load_registry
        registry = load_registry()

    handler = GlobalExceptionHandler(registry)
    handler.register(app)
