import tkinter as tk
from tkinter import ttk
from tkinter import font, colorchooser, filedialog, messagebox
import os
from PIL import Image, ImageTk


main_application = tk.Tk()
main_application.geometry("1200x800")
main_application.title('Vpad text editor')

############### main menu ##############
main_menu = tk.Menu()


# main menu file
#icons
new_icon = tk.PhotoImage(file='img/new.png')
open_icon = tk.PhotoImage(file='img/new.png')
save_icon = tk.PhotoImage(file='img/new.png')
save_as_icon = tk.PhotoImage(file='img/new.png')
exit_icon = tk.PhotoImage(file='img/new.png')
file = tk.Menu(main_menu, tearoff = False)

# main menu view
view = tk.Menu(main_menu, tearoff = False)

# main menu edit
edit = tk.Menu(main_menu, tearoff = False)

# main menu color theam
color_theam = tk.Menu(main_menu, tearoff = False)
color_dict = {
    "Light Default": ('#000000', '#ffffff'),
    "Light Plus": ('#474747', '#e0e0e0'),
    "Dark": ('#c4c4c4, #2d2d2d'),
    "Red": ('#2d2d2d', '#ffe8e8'),
    "Monokai": ('#d3b774', '#474747'),
    "Night Blue": ('#ededed', '#6b9dc2')
}


# cascade, to add elements to main menu
main_menu.add_cascade(label='File', menu=file)
main_menu.add_cascade(label='Edit', menu=edit)
main_menu.add_cascade(label='View', menu=view)
main_menu.add_cascade(label='Color_Theam', menu=color_theam)


#-------------- main menu end ----------#


############### toolbar ##############
tool_bar = ttk.Label(main_application)
tool_bar.pack(side=tk.TOP, fill=tk.X)

# to get all font families, it returns all the names of font in the form of tuple
font_tupels = tk.font.families()
font_family = tk.StringVar()

font_box = ttk.Combobox(tool_bar, width=30, textvariable=font_family, state='readonly')
font_box['values'] = font_tupels
#font_box.current(0)
font_box.current(font_tupels.index('Arial'))
font_box.grid(row=0, column=0, padx=5)

# size box
size_var = tk.IntVar()
font_size = ttk.Combobox(tool_bar, width=3, textvariable=size_var, state='readonly')
font_size['values'] = tuple(range(8,80,2))
font_size.current(0)
font_size.grid(row=0, column=1, padx=5)


#button
bold_img = tk.PhotoImage(file='img/new.png')
bold_btn = ttk.Button(tool_bar, image=bold_img)
bold_btn.grid(row=0, column=2, padx=5)

italic_img = tk.PhotoImage(file='img/new.png')
italic_btn = ttk.Button(tool_bar, image=italic_img)
italic_btn.grid(row=0, column=3, padx=5)
#-------------- toolbar end ----------#


############### text editor ##############
text_editor = tk.Text(main_application)
text_editor.config(wrap='word', relief=tk.FLAT)

scrol_bar = tk.Scrollbar(main_application)

text_editor.focus_set()
scrol_bar.pack(side=tk.RIGHT, fill=tk.Y)
text_editor.pack(fill=tk.BOTH, expand=True)
scrol_bar.config(command=text_editor.yview)
text_editor.config(yscrollcommand=scrol_bar.set)


# font family and font size functionality
current_font_family = 'Arial'
current_font_size = 12

def change_font(main_application):
    global current_font_family, current_font_size
    current_font_family = font_family.get()
    current_font_size = size_var.get()
    text_editor.config(font=(current_font_family, current_font_size))

#font_box.bind('<<ComboboxSelected>>', change_font)
font_box.bind('<<ComboboxSelected>>', change_font)
font_size.bind('<<ComboboxSelected>>', change_font)

text_editor.config(font=('Arial', 12))


# buttons functionality
# bold function
def change_bold():
    text_property = tk.font.Font(font=text_editor['font'])
    if text_property.actual()['weight'] == 'normal':
        text_editor.configure(font=(current_font_family, current_font_size, 'bold'))
    else:
        text_editor.configure(font=(current_font_family, current_font_size, 'normal'))

bold_btn.config(command=change_bold)

def change_italic():
    text_property = tk.font.Font(font=text_editor['font'])
    if text_property.actual()['slant'] == 'roman':
        text_editor.config(font=(current_font_family, current_font_size, 'italic'))
    else:
        text_editor.config(font=(current_font_family, current_font_size, 'roman'))

italic_btn.config(command=change_italic)
#------------ text editor end ------------#


############### statusbar ##############
status_bar = ttk.Label(main_application, text="Status Bar")
status_bar.pack(side=tk.BOTTOM)

#------------- statusbar end -------------#


############### main menu function ##############
# file commands
file.add_command(label='New', compound=tk.LEFT, accelerator='Ctrl+N')
file.add_command(label='Open', compound=tk.LEFT, accelerator='Ctrl+O')
file.add_command(label='Save', compound=tk.LEFT, accelerator='Ctrl+S')
file.add_command(label='Save As', compound=tk.LEFT, accelerator='Alt+Ctrl+S')
file.add_command(label='Quit', compound=tk.LEFT, accelerator='Ctrl+X')
# compound is used to place the image
# accelerator is used to add shortcut key text beside the label 

# add checkbox
view.add_checkbutton(label='Good')
view.add_checkbutton(label='Bad')

# add color theam

theam_choice = tk.StringVar()
count = 0
for i in color_dict:
    color_theam.add_radiobutton(label=i, variable=theam_choice)
    count+=1

#------------- main menu function end -------------#


main_application.config(menu=main_menu)
main_application.mainloop()