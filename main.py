# main.py
import tkinter as tk
from gui import GPXMapperGUI

if __name__ == '__main__':
    root = tk.Tk()
    app = GPXMapperGUI(root)
    root.mainloop()
