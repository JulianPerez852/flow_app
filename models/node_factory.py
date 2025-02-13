# models/node_factory.py
from models.inicio_node import InicioNode
from models.accion_node import AccionNode
from models.condicional_node import CondicionalNode
from models.multiples_node import MultiplesNode
from models.llm_node import LLMNode
from models.python_node import PythonNode
from models.smtp_node import SmtpNode
from models.nodes import DefaultNode

class NodeFactory:
    @staticmethod
    def create_node(node_type, x, y):
        if node_type == "inicio":
            return InicioNode(x, y)
        elif node_type == "accion":
            return AccionNode(x, y)
        elif node_type == "condicional":
            return CondicionalNode(x, y)
        elif node_type == "multiples":
            return MultiplesNode(x, y)
        elif node_type == "llm":
            return LLMNode(x, y)
        elif node_type == "python":
            return PythonNode(x, y)
        elif node_type == "smtp":
            return SmtpNode(x, y)
        else:
            return DefaultNode(x, y, node_type, f"{node_type.capitalize()} Node")
