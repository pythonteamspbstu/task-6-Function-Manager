import math

from utils import build_function_record

class FunctionManager:
    def __init__(self):
        self.functions = {}

    def create_function(self, name: str, inputs: list[str], outputs: list[str], expression: str):
        if name in self.functions:
            raise ValueError(f"Function '{name}' already exists.")
        
        self.functions[name] = build_function_record(name, inputs, outputs, expression)
        return self.functions[name]

    def get_function(self, name: str):
        if name not in self.functions:
            return None
        return self.functions[name]

    def list_functions(self):
        return list(self.functions.values())

    def update_function(self, name: str, inputs: list[str], outputs: list[str], expression: str):
        if name not in self.functions:
            raise ValueError(f"Function '{name}' does not exist.")
        
        self.functions[name] = build_function_record(name, inputs, outputs, expression)
        return self.functions[name]

    def delete_function(self, name: str):
        if name in self.functions:
            del self.functions[name]
            return True
        return False

    def execute_function(self, name: str, args: dict):
        func = self.get_function(name)
        if not func:
            raise ValueError(f"Function '{name}' not found.")
        
        missing_args = [arg for arg in func['inputs'] if arg not in args]
        if missing_args:
            raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

        context = {**math.__dict__, **args}
        
        try:
            result = eval(func['expression'], {"__builtins__": {}}, context)
            return result
        except Exception as e:
            raise ValueError(f"Execution error: {str(e)}")

