# models/nodes.py
import uuid
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import Toplevel, ttk

class FlowNode(ABC):
    def __init__(self, x, y, node_type, text, title=""):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.node_type = node_type  # Ejemplo: "inicio", "accion", "smtp", etc.
        self.text = text
        self.title = title
        self.config = {}            # Configuración específica del nodo
        self.connected_from = None  # Nodo que conecta a este (entrada)
        self.connected_to = None    # Nodo al que conecta (salida)

    @abstractmethod
    def execute(self, context):
        """
        Ejecuta la acción del nodo.
        'context' es un diccionario que contiene variables, memoria, etc.
        Debe retornar (generalmente) el siguiente nodo a ejecutar.
        """
        raise NotImplementedError("Debe implementarse en la subclase.")

    @abstractmethod
    def configure(self, parent, variable_manager):
        """
        Lanza el diálogo de configuración para el nodo.
        'parent' es la ventana padre (Tk) y 'variable_manager' permite elegir variables.
        """
        raise NotImplementedError("Debe implementarse en la subclase.")

    @property
    def input_point(self):
        return (self.x, self.y + 25)

    @property
    def output_point(self):
        return (self.x + 100, self.y + 25)

class DefaultNode(FlowNode):
    """
    Nodo genérico para tipos que no tengan una implementación específica.
    Se usará, por ejemplo, para "inicio", "accion", "final", etc.
    """
    def __init__(self, x, y, node_type, text, title=""):
        super().__init__(x, y, node_type, text, title)

    def execute(self, context):
        print(f"Ejecutando {self.text}")
        return self.connected_to

    def configure(self, parent, variable_manager):
        dialog = Toplevel(parent)
        dialog.title("Configurar Nodo")
        dialog.transient(parent)
        dialog.grab_set()

        lbl_title = ttk.Label(dialog, text="Título:")
        lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_title = ttk.Entry(dialog, width=40)
        entry_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        if self.title:
            entry_title.insert(0, self.title)

        def on_ok():
            self.title = entry_title.get().strip()
            self.text = self.title if self.title else self.text
            dialog.destroy()

        btn_ok = ttk.Button(dialog, text="OK", command=on_ok)
        btn_ok.grid(row=1, column=0, padx=10, pady=10)
        btn_cancel = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
        btn_cancel.grid(row=1, column=1, padx=10, pady=10)
        dialog.wait_window(dialog)