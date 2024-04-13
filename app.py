import os
from collections import deque
from multiprocessing import Process
from tkinter import Tk, ttk, filedialog, Text, END, StringVar, DISABLED, scrolledtext
from pathlib import Path

# Create the main window
root = Tk()
ttk.Style().theme_use('clam')
root.title("PDF Splitter")
root.minsize(width='1000', height='500')


# Create the notebook (tabs)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")
notebook.bind("<<NotebookTabChanged>>", lambda _: root.update_idletasks())

def select_config_file():
  filepath = filedialog.askopenfilename(
      initialdir=str(Path.home()),
      title="Select a configuration file",
      filetypes=[("Config files", ".cfg")]
  )
  if filepath:
    config_file_entry.delete(0,END)
    config_file_entry.insert(0,filepath)

def select_input_path():
  filepath = filedialog.askdirectory(
      initialdir=str(Path.home()),
      title="Select a input directory"
  )
  if filepath:
    input_path_entry.delete(0,END)
    input_path_entry.insert(0,filepath)

def select_output_path():
  filepath = filedialog.askdirectory(
      initialdir=str(Path.home()),
      title="Select a output directory"
  )
  if filepath:
    output_path_entry.delete(0,END)
    output_path_entry.insert(0,filepath)

# Tab 1
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Split")

tab1.grid_columnconfigure(1, weight=1)

config_file_label = ttk.Label(tab1, text="Configuration file")
config_file_label.grid(row = 1, column = 0, sticky = 'W', pady = 2)

config_file_entry = ttk.Entry(tab1)
config_file_entry.grid(row = 1, column = 1, sticky = 'EW', pady = 2)

config_file_select = ttk.Button(tab1, text="Select File", command=select_config_file)
config_file_select.grid(row = 1, column = 2, padx=4, pady=2)
def open_create_config_tab():
  notebook.select(tab2)
create_config_file = ttk.Button(tab1, text="Create", command=open_create_config_tab)
create_config_file.grid(row = 1, column = 3, padx=4)


input_path_label = ttk.Label(tab1, text="Input Path")
input_path_label.grid(row = 2, column = 0, sticky = 'W', pady = 2)

input_path_entry = ttk.Entry(tab1)
input_path_entry.grid(row = 2, column = 1, sticky = 'EW', pady = 2)

input_path_select = ttk.Button(tab1, text="Select", command=select_input_path)
input_path_select.grid(row = 2, column = 2, padx = 2, pady=2)


output_path_label = ttk.Label(tab1, text="Output Path")
output_path_label.grid(row = 3, column = 0, sticky = 'W', pady = 2)

output_path_entry = ttk.Entry(tab1)
output_path_entry.grid(row = 3, column = 1, sticky = 'EW', pady = 2)

output_path_select = ttk.Button(tab1, text="Select", command=select_output_path)
output_path_select.grid(row = 3, column = 2, padx = 2, pady=2)

progress_msgs = deque()
progress = scrolledtext.ScrolledText(tab1, state=DISABLED, bg='white', fg='black')
progress.grid(row=5, column=0, columnspan=4, sticky='ew', pady=20)

def append_progress():
  if progress_msgs:
    msg = progress_msgs.popleft()
    progress.configure(state='normal')
    progress.insert(END, msg + '\n')
    progress.configure(state='disabled')
    progress.update_idletasks()
  progress.after(100, append_progress)

progress.after(100, append_progress)

def process_file(file):
  progress_msgs.append('Processing file ' + file + '....')
  pass

def process_all_files():
  progress.configure(state='normal')
  progress.delete(1.0, END)
  progress.configure(state='disabled')

  config_file = config_file_entry.get()
 
  if not config_file:
    progress_msgs.append('ERROR: Configuration file can not be empty')
    return

  if not os.path.exists(config_file):
    progress_msgs.append('ERROR: Configuration file not found')
    return

  input_path = input_path_entry.get()
  if not input_path:
    progress_msgs.append('ERROR: Input directory can not be empty')
    return

  if not os.path.exists(input_path):
    progress_msgs.append('ERROR: Input directory not found')
    return
  
  output_path = output_path_entry.get()
  if not output_path:
    progress_msgs.append('ERROR: Output directory can not be empty')
    return

  if not os.path.exists(output_path):
    progress_msgs.append('ERROR: Output directory not found')
    return
  
  for file in os.listdir(input_path):
    filename, file_extension = os.path.splitext(file)
    if file_extension not in ['.pdf']:
      continue
    process_file(file)

def run():
  p = Process(target=process_all_files)
  p.run()

run_button = ttk.Button(tab1, text='Split Files', command=run)
run_button.grid(row=4, column=1, columnspan=2)


# Tab 2


tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Create Configuration")
notebook.select(tab2)
tab2.grid_columnconfigure(1, weight=1)

template_pdf_label = ttk.Label(tab2, text="Template PDF")
template_pdf_label.grid(row = 0, column = 0, sticky = 'W', pady = 2)

template_pdf_entry = ttk.Entry(tab2)
template_pdf_entry.grid(row = 0, column = 1, sticky = 'EW', pady = 2)

create_config_progress = scrolledtext.ScrolledText(tab2, bg='white', fg='black', insertbackground='black', font=("Arial 16"))
create_config_progress.grid(row=1, column=0, columnspan=4, sticky='ew', pady=20)

def clear_create_config_progress():
  create_config_progress.delete(1.0, END)

def set_create_config_progress(msg):
   create_config_progress.insert(END, msg + '\n')
  
set_create_config_progress("Select template pdf and click 'Process'")

def select_template_pdf_file():
  filepath = filedialog.askopenfilename(
      title="Select a template pdf file",
      filetypes=[("PDF FIles", ".pdf")]
  )
  if filepath:
    template_pdf_entry.delete(0, END)
    template_pdf_entry.insert(0, filepath)


template_pdf_button = ttk.Button(tab2, text="Select File", command=select_template_pdf_file)
template_pdf_button.grid(row = 0, column = 2, padx = 2, pady=2)

def get_configuration(filepath):
  return 'configuration'

def process_pdf_template():
  clear_create_config_progress()
  template_pdf = template_pdf_entry.get()

  if not template_pdf:
    set_create_config_progress('ERROR: Please provide template pdf file')
    return

  if not os.path.exists(template_pdf):
    set_create_config_progress('ERROR: File not found')
    return
  
  set_create_config_progress(get_configuration(template_pdf))

template_pdf_process_button = ttk.Button(tab2, text="Process", command=process_pdf_template)
template_pdf_process_button.grid(row = 0, column = 3, padx = 2, pady=2)

def cancel_config_file():
  clear_create_config_progress()
  set_create_config_progress("Select template pdf and click 'Process'")
  template_pdf_entry.delete(0, END)
  root.update_idletasks()

config_cancel_button = ttk.Button(tab2, text="Cancel", command=cancel_config_file)
config_cancel_button.grid(row = 2, column = 2, padx =10, pady=10)

def save_config_file():
   content = create_config_progress.get(1.0, END).strip()
   f = filedialog.asksaveasfile(initialfile = 'sample_config.cfg', defaultextension=".cfg",filetypes=[("Config Files","*.cfg")])
   f.write(content)
   f.close()

config_save_button = ttk.Button(tab2, text="Save", command=save_config_file)
config_save_button.grid(row = 2, column = 3, padx =10, pady=10)

# Tab 3
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Tools")

# Run the main loop
root.mainloop()
