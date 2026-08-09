from typing import Callable, Dict, List, Any

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            self._tools[name] = {
                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                    }
                },
                "func": func
            }
            return func
        return decorator

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool["schema"] for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not registered")
        return self._tools[name]["func"](**kwargs)

# Global registry instance
registry = ToolRegistry()
