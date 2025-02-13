# main.py
from controllers.diagram_controller import DiagramController
from views.diagram_view import DiagramView

def main():
    controller = DiagramController(None)
    view = DiagramView(controller)
    controller.view = view
    view.mainloop()

if __name__ == "__main__":
    main()