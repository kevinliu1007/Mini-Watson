import sys
import question_answering
from tkinter import *
from tkinter import Tk, Label, Button, Entry, IntVar, END, W, E
from tkinter import ttk


def calculate(*args):
    try:
        value = string.get()
        answer = question_answering.qa(value)
        meters.set(answer)
    except ValueError:
        pass

# check their answer function
def calculate2(*args):
    try:
        value2 = ans.get()
        #correct.set('Yo Momma2')
    except ValueError:
        pass
    
root = Tk()
root.title("NLP- tinyWatson by Ishta & Kevin")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

string = StringVar()
meters = StringVar()

ttk.Label(mainframe, text="Enter Your Question:").grid(column=1, row=1, sticky=W)
string_entry = ttk.Entry(mainframe, width=61, textvariable=string)
string_entry.grid(column=2, row=1, sticky=(W, E))

ttk.Label(mainframe, textvariable=meters).grid(column=2, row=2, sticky=(W, E))
ttk.Button(mainframe, text="Ask!", command=calculate).grid(column=3, row=1, sticky=W)
ttk.Label(mainframe, text="Answer:").grid(column=1, row=2, sticky=E)
ttk.Label(mainframe, text="Try Again?").grid(column=1, row=3, sticky=W)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

string_entry.focus()

root.bind('<Return>', calculate)

root.mainloop()

