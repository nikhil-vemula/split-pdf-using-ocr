import os
from collections import deque
from multiprocessing import Process
from tkinter import Tk, ttk, filedialog, Text, END, StringVar, DISABLED, scrolledtext, messagebox
from pathlib import Path
from io import StringIO
import fitz  # PyMuPDF
import configparser
import pytesseract
from PIL import Image
import re
from PyPDF2 import PdfWriter, PdfReader
import threading
from queue import Queue

#Windows
if os.name == 'nt':
    #Tesseract installation issues: https://stackoverflow.com/a/67657995/11436515
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def center_window(width=300, height=200):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))

# Create the main window
root = Tk()
ttk.Style().theme_use('clam')
root.title("PDF Splitter")
center_window(1000, 600)
# root.minsize(width='1000', height='500')


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

progress = scrolledtext.ScrolledText(tab1, state=DISABLED, bg='white', fg='black')
progress.grid(row=5, column=0, columnspan=4, sticky='ew', pady=20)

def clear_progress():
  progress.configure(state='normal')
  progress.delete(1.0, END)
  progress.configure(state='disabled')

def append_progress_info(msg):
  progress.configure(state='normal')
  progress.insert(END, msg + '\n')
  progress.configure(state='disabled')
  progress.update_idletasks()

def process_pdf(pdf_path, output_path, ocr_config):
  pdf_reader = PdfReader(pdf_path)
  pdf = fitz.open(pdf_path)

  current_doc_type = None
  current_writer = None
  defendant_id = os.path.splitext(os.path.basename(pdf_path))[0]

  # Create a subdirectory for the current PDF file
  file_output_path = os.path.join(output_path, defendant_id)
  if not os.path.exists(file_output_path):
      os.makedirs(file_output_path)

  for page_num in range(len(pdf)):
      page = pdf[page_num]
      page_found = False
      pix = page.get_pixmap()

      for doc_type, bbox in ocr_config.items():
          # Extract sub-image using the bbox
          adjusted_bbox = fitz.Rect(bbox)
          sub_pix = page.get_pixmap(clip=adjusted_bbox)
          sub_img = Image.frombytes("RGB", [sub_pix.width, sub_pix.height], sub_pix.samples)

          # Use pytesseract to do OCR on the extracted sub-image
          text_raw = pytesseract.image_to_string(sub_img).lower()
          text = ' '.join(text_raw.replace('\n', ' ').split())
          text = re.sub(r'[^a-zA-Z0-9 -]', '', text)

          if doc_type in text:
              page_found = True
              if current_writer is not None:
                  output_file_path = os.path.join(file_output_path, f"{defendant_id}_{current_doc_type}.pdf")
                  with open(output_file_path, "wb") as f_out:
                      current_writer.write(f_out)
              current_doc_type = doc_type
              current_writer = PdfWriter()
              current_writer.add_page(pdf_reader.pages[page_num])
              break
      if not page_found and current_writer is not None:
          current_writer.add_page(pdf_reader.pages[page_num])

  if current_writer is not None:
      output_file_path = os.path.join(file_output_path, f"{defendant_id}_{current_doc_type}.pdf")
      with open(output_file_path, "wb") as f_out:
          current_writer.write(f_out)

  pdf.close()

def process_file(filename, ocr_config, input_path, output_path):
    try:
        pdf_path = os.path.join(input_path, filename)
        # print('Processing', pdf_path)
        # append_progress_info(f'Processing {pdf_path}')
        process_pdf(pdf_path, output_path, ocr_config)
        # append_progress_info(f'Processed {pdf_path}')
    except Exception as e:
        append_progress_info(f'Failed to process {filename}: {str(e)}')

def get_ocr_config():
  config_file = config_file_entry.get()
  if not config_file:
      messagebox.showerror("Error", "Configuration file is required!")
      return
  
  config = configparser.ConfigParser()
  config.read(config_file)

  ocr_config = {}
  ocr_pattern = re.compile(r'text(\d+)')
  for section in config.sections():
      if section == 'OCR':
          for key, value in config[section].items():
              match = ocr_pattern.match(key)
              if match:
                  index = match.group(1)  # The digit part from 'Text' key
                  doc_type = value.strip('"').lower()
                  loc_key = f'loc{index}'  # Corresponding 'Loc' key
                  if loc_key in config[section]:
                      loc = tuple(map(int, config[section][loc_key].split(',')))
                      ocr_config[doc_type] = loc
  return ocr_config

task_queue = deque()
thread_queue = []

def check_on_threads():
  # We should check on threads cause they are working for us.
  running_threads = len(thread_queue)
  can_start = 5 - running_threads

  i = 0
  while i < can_start and i < len(task_queue):
      filename, ocr_config, input_path, output_path  = task_queue.popleft()
      append_progress_info(f'Processing {input_path}')
      t = threading.Thread(target=process_file, name=input_path, args=[filename, ocr_config, input_path, output_path])
      t.start()
      thread_queue.append(t)
      i += 1
    
  i = 0
  print('Status')
  print([t.is_alive() for t in thread_queue])
  while i < len(thread_queue):
    t = thread_queue[i]
    if not t.is_alive():
      thread_queue.pop(i)
      append_progress_info(f'Processed {t.name}')
    else:
     i += 1
    
  if task_queue or thread_queue:
     root.after(1000, check_on_threads)
  else:
     print('Complete')
     messagebox.showinfo(title='Completed', message='All files processed')


def process_all_files():
  clear_progress()
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
  
  ocr_config = get_ocr_config()
  
  for file in os.listdir(input_path):
    filename, file_extension = os.path.splitext(file)
    if file_extension not in ['.pdf']:
      continue

    # Start processing each pdf file using threads
    task_queue.append((file, ocr_config, input_path, output_path))
    # process_file(file, ocr_config, input_path, output_path)
  check_on_threads()
  
  

def run():
  process_all_files()
  # p = Process(target=process_all_files)
  # p.start()

run_button = ttk.Button(tab1, text='Split Files', command=run)
run_button.grid(row=4, column=1, columnspan=2)


# Tab 2
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Create Configuration")
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

def get_configuration(pdf_name):
    doc = fitz.open(pdf_name)

    config = configparser.ConfigParser()
    config['Files'] = {'Template': '"' + pdf_name + '"'}
    config['OCR'] = {}

    annotation_count = 0
    for page_number, page in enumerate(doc):
        page_annotations = list(page.annots())
        if not page_annotations:
            continue

        for i, annotation in enumerate(page_annotations):
            rect = annotation.rect
            sub_pix = page.get_pixmap(clip=rect)
            img = Image.frombytes("RGB", [sub_pix.width, sub_pix.height], sub_pix.samples)
            extracted_text = pytesseract.image_to_string(img)
            clean_text = ' '.join(extracted_text.replace('\n', ' ').split())
            clean_text = re.sub(r'[^a-zA-Z0-9 -]', '', clean_text)
            config['OCR'][f'Text{annotation_count + 1}'] = f'"{clean_text.lower()}"'
            config['OCR'][f'Loc{annotation_count + 1}'] = f"{int(rect.x0)},{int(rect.y0)},{int(rect.x1)},{int(rect.y1)}"
            annotation_count += 1

    doc.close()

    config_string = StringIO()
    config.write(config_string)
    config_string.seek(0)

    return config_string.read()


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
  config_save_button.config(state='active')

template_pdf_process_button = ttk.Button(tab2, text="Process", command=process_pdf_template)
template_pdf_process_button.grid(row = 0, column = 3, padx = 2, pady=2)

def cancel_config_file():
  clear_create_config_progress()
  set_create_config_progress("Select template pdf and click 'Process'")
  template_pdf_entry.delete(0, END)
  config_save_button.config(state='disabled')
  root.update_idletasks()

config_cancel_button = ttk.Button(tab2, text="Cancel", command=cancel_config_file)
config_cancel_button.grid(row = 2, column = 2, padx =10, pady=10)

def save_config_file():
   content = create_config_progress.get(1.0, END).strip()
   f = filedialog.asksaveasfile(initialfile = 'sample_config.cfg', defaultextension=".cfg",filetypes=[("Config Files","*.cfg")])
   f.write(content)
   f.close()
   messagebox.showinfo(title='Success', message='Saved the configuration file successfully')

config_save_button = ttk.Button(tab2, text="Save", command=save_config_file, state=DISABLED)
config_save_button.grid(row = 2, column = 3, padx =10, pady=10)

# # Tab 3
# tab3 = ttk.Frame(notebook)
# notebook.add(tab3, text="Tools")

# Run the main loop
root.mainloop()
