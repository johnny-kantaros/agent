
from src.tools.registry import register
from src.tools.examples.echo.tool import EchoTool

def register_tools():
    register(EchoTool())

register_tools()