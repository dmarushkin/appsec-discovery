from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse


def hello(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hello World!")


app = Starlette(routes=[Route("/", hello)])