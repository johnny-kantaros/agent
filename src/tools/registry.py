TOOLS = {}

def register(tool_instance):
    TOOLS[tool_instance.name] = tool_instance

def get_tool(name):
    return TOOLS.get(name)