from tkinter import *
from tkinter import ttk
from tkinter.ttk import Progressbar
import os

# Create main window
root = Tk()

# Load image
image = PhotoImage(file="/loading.png")

# Define window dimensions
height = 430
width = 530

# Calculate position to center the window
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)

# Set geometry and other window properties
root.geometry(f"{width}x{height}+{x}+{y}")
root.config(background="#000000")

# Add a label
welcome = Label(
    text="Enter at your own risk", 
    bg="#2F6C60", 
    font=("Trebuchet Ms", 15, "bold"), 
    fg="#FFFFFF"
)
welcome.place(x=130, y=25)

# Prevent resizing
root.resizable(False, False)

# Run the Tkinter main loop
root.mainloop()
