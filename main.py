import tkinter as tk
from app.db import init_db, crear_usuario_inicial
from app.ui_login import LoginWindow
from app.ui_menu import MainMenu


def lanzar_menu(root):
    # Limpia la ventana y carga el menú principal
    for widget in root.winfo_children():
        widget.destroy()
    MainMenu(root)


def main():
    # Inicializar DB y usuario por defecto
    init_db()
    crear_usuario_inicial()

    root = tk.Tk()

    # Cuando el login sea correcto, se ejecuta lanzar_menu
    LoginWindow(root, on_login_ok=lambda: lanzar_menu(root))

    root.mainloop()


if __name__ == "__main__":
    main()
