# models/flow_node.py
import uuid

class FlowNode:
    def __init__(self, x, y, node_type, text, title=""):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.node_type = node_type  # "inicio", "accion", "final", "condicional", "multiples", "llm"
        self.text = text            # Texto principal (por ejemplo, contenido de la acción)
        self.title = title          # Título o descriptor del nodo
        self.config = {}            # Diccionario para almacenar configuraciones adicionales
        self.connected_from = None  # Conexión entrante (única)
        self.connected_to = None    # Para nodos "normales": salida única
        # Para nodos condicionales:
        self.true_connection = None
        self.false_connection = None

    @property
    def input_point(self):
        # Punto de entrada (lado izquierdo, centrado verticalmente)
        return (self.x, self.y + 25)

    @property
    def output_point(self):
        # Punto de salida (para nodos no condicionales, lado derecho)
        return (self.x + 100, self.y + 25)
