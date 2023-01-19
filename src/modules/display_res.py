import tkinter as tk

def get_dpi():
    screen = tk.Tk()
    current_dpi = screen.winfo_fpixels('1i')
    screen.destroy()
    return current_dpi

def scaled(original):
    scale = get_dpi()/96
    return round(original * scale)