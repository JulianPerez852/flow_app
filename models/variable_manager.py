# models/variable_manager.py
class Variable:
    def __init__(self, name, var_type, value=None):
        self.name = name
        self.var_type = var_type
        self.value = value

    def __str__(self):
        return f"{self.name} ({self.var_type}) = {self.value}"

class VariableManager:
    def __init__(self):
        self.variables = {}

    def add_variable(self, name, var_type, value=None):
        if name in self.variables:
            raise ValueError("La variable ya existe")
        var = Variable(name, var_type, value)
        self.variables[name] = var
        return var

    def update_variable(self, name, value):
        if name in self.variables:
            self.variables[name].value = value

    def get_variable(self, name):
        return self.variables.get(name)

    def get_all_variables(self):
        return list(self.variables.values())

    def load_variables(self, variables_data):
        self.variables = {}
        for var in variables_data:
            self.variables[var["name"]] = Variable(var["name"], var["var_type"], var.get("value"))
