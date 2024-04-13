import os
from collections import deque
from multiprocessing import Process
from tkinter import Tk, ttk, filedialog, Text, END, StringVar, DISABLED, scrolledtext

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
      title="Select a configuration file",
      filetypes=[("Config files", ".cfg")]
  )
  if filepath:
    config_file_entry.delete(0,END)
    config_file_entry.insert(0,filepath)

def select_input_path():
  filepath = filedialog.askdirectory(
      title="Select a input directory"
  )
  if filepath:
    input_path_entry.delete(0,END)
    input_path_entry.insert(0,filepath)

def select_output_path():
  filepath = filedialog.askdirectory(
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
  
  for file in os.listdir(output_path):
    progress_msgs.append('Processing file ' + file + '....')
    process_file(file)

def run():
  p = Process(target=process_all_files)
  p.run()

run_button = ttk.Button(tab1, text='Split Files', command=run)
run_button.grid(row=4, column=1, columnspan=2)


# Tab 2
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Create Configuration")
tab2.grid_columnconfigure(1, weight=1)

label1 = ttk.Label(tab2, text="Template PDF")
label1.grid(row = 0, column = 0, sticky = 'W', pady = 2)

entry1 = ttk.Entry(tab2)
entry1.grid(row = 0, column = 1, sticky = 'EW', pady = 2)

button1 = ttk.Button(tab2, text="Select File", command=select_config_file)
button1.grid(row = 0, column = 2, padx = 2, pady=2)

# Tab 3
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Tools")

# Run the main loop
root.mainloop()
