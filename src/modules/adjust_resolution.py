import tkinter as tk

ORIGINAL = 96

def get_dpi():
    screen = tk.Tk()
    current = screen.winfo_fpixels('1i')
    screen.destroy()
    return current

SCALE = get_dpi()/ORIGINAL

def scaled(original_width, scale):
    return round(original_width * scale)

