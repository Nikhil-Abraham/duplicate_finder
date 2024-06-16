import os
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from collections import defaultdict
import hashlib
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DuplicateFileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Detector")
        self.root.geometry("800x600")

        self.directory = None
        self.duplicates = {}  # To store duplicates found
        self.group_checkboxes_vars = defaultdict(list)  # To store IntVar for each file in each group

        # UI elements
        self.create_widgets()

    def create_widgets(self):
        # Directory selection button
        select_directory_btn = tk.Button(self.root, text="Select Directory", command=self.select_directory)
        select_directory_btn.pack(pady=10)

        # Scan button
        scan_btn = tk.Button(self.root, text="Scan for Duplicates", command=self.scan_for_duplicates)
        scan_btn.pack(pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=300, mode='indeterminate')

        # Select All and Select All But One buttons
        select_all_btn = tk.Button(self.root, text="Select All", command=self.select_all)
        select_all_btn.pack(side=tk.LEFT, padx=10)

        select_all_but_one_btn = tk.Button(self.root, text="Select All But One", command=self.select_all_but_one)
        select_all_but_one_btn.pack(side=tk.LEFT, padx=10)

        # Delete selected duplicates button
        delete_btn = tk.Button(self.root, text="Delete Selected Duplicates", command=self.delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=10)

    def select_directory(self):
        self.directory = filedialog.askdirectory(parent=self.root)
        if self.directory:
            messagebox.showinfo("Directory Selected", f"Selected Directory: {self.directory}")

    def scan_for_duplicates(self):
        if not self.directory:
            messagebox.showerror("Error", "Please select a directory first.")
            return

        self.scan_directory_and_detect_duplicates()

    def scan_directory_and_detect_duplicates(self):
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.root.update_idletasks()  # Update GUI to show progress bar

        self.duplicates = self.detect_duplicates(self.directory)

        self.progress_bar.stop()
        self.progress_bar.pack_forget()  # Remove progress bar after completion

        self.display_duplicates()

    def scan_directory(self, directory):
        logging.info(f"Scanning directory: {directory}")
        file_info = []
        for root, _, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                try:
                    size = os.path.getsize(path)
                    file_info.append((path, size))
                except OSError as e:
                    logging.error(f"Error accessing {path}: {e}")
        logging.info(f"Completed scanning. Found {len(file_info)} files.")
        return file_info

    def group_by_size(self, file_info):
        logging.info("Grouping files by size.")
        size_dict = defaultdict(list)
        for path, size in file_info:
            size_dict[size].append(path)
        logging.info(f"Completed grouping by size. Found {len(size_dict)} size groups.")
        return size_dict

    def hash_file(self, path, quick=False, blocksize=65536):
        hasher = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                if quick:
                    buf = f.read(4096)  # Read the first 4KB
                else:
                    buf = f.read(blocksize)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = f.read(blocksize)
        except Exception as e:
            logging.error(f"Error hashing {path}: {e}")
            return None
        return hasher.hexdigest()

    def find_duplicates(self, size_dict):
        logging.info("Finding duplicates.")
        duplicates = defaultdict(list)
        for size, files in tqdm(size_dict.items(), desc="Processing size groups"):
            if len(files) < 2:
                continue
            
            # Quick hash comparison
            quick_hashes = defaultdict(list)
            for file in tqdm(files, desc=f"Quick hashing files of size {size}", leave=False):
                quick_hash = self.hash_file(file, quick=True)
                if quick_hash:
                    quick_hashes[quick_hash].append(file)
            
            # Full hash comparison
            for quick_hash, files in tqdm(quick_hashes.items(), desc="Full hashing", leave=False):
                if len(files) < 2:
                    continue
                
                full_hashes = defaultdict(list)
                for file in tqdm(files, desc="Full hashing files", leave=False):
                    full_hash = self.hash_file(file)
                    if full_hash:
                        full_hashes[full_hash].append(file)
                
                for full_hash, dup_files in full_hashes.items():
                    if len(dup_files) > 1:
                        duplicates[full_hash].extend(dup_files)
        logging.info(f"Completed finding duplicates. Found {len(duplicates)} duplicate groups.")
        return duplicates

    def detect_duplicates(self, directory):
        logging.info(f"Starting duplicate detection in directory: {directory}")
        file_info = self.scan_directory(directory)
        size_dict = self.group_by_size(file_info)
        duplicates = self.find_duplicates(size_dict)
        logging.info("Duplicate detection completed.")
        return duplicates

    def display_duplicates(self):
        # Clear previous display
        for widget in self.root.pack_slaves():
            widget.pack_forget()

        # Display duplicate groups
        group_index = 1
        for group_name, files in self.duplicates.items():
            group_label = tk.Label(self.root, text=f"Group {group_index}")
            group_label.pack(pady=5)

            for file in files:
                # Create a frame to hold the checkbox and label
                frame = tk.Frame(self.root)
                frame.pack(anchor=tk.W, pady=2)

                # Checkbox for selection
                var = tk.IntVar()
                checkbox = tk.Checkbutton(frame, variable=var)
                checkbox.pack(side=tk.LEFT)

                # Label as a hyperlink
                label = tk.Label(frame, text=file, fg="blue", cursor="hand2")
                label.pack(side=tk.LEFT)
                label.bind("<Button-1>", lambda event, path=file: self.open_file(path))

                # Store the variable for later use
                self.group_checkboxes_vars[group_name].append(var)

            group_index += 1

        # Buttons
        self.create_widgets()  # Re-create the buttons after displaying duplicates

    def open_file(self, path):
        try:
            os.startfile(path)  # Opens the file with its default application
        except OSError as e:
            logging.error(f"Error opening file {path}: {str(e)}")



    def select_all(self):
        for group_name, vars_list in self.group_checkboxes_vars.items():
            for var in vars_list:
                var.set(1)

    def select_all_but_one(self):
        for group_name, vars_list in self.group_checkboxes_vars.items():
            first_checked = False
            for var in vars_list:
                if var.get() == 0:
                    var.set(1)
                elif not first_checked:
                    var.set(0)
                    first_checked = True

    def delete_selected(self):
        files_to_delete = []
        for group_name, vars_list in self.group_checkboxes_vars.items():
            for file, var in zip(self.duplicates[group_name], vars_list):
                if var.get() == 1:
                    files_to_delete.append(file)

        for file in files_to_delete:
            try:
                os.remove(file)
            except Exception as e:
                logging.error(f"Error deleting file {file}: {str(e)}")

        # After deleting, refresh display
        self.duplicates = self.detect_duplicates(self.directory)
        self.display_duplicates()

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFileApp(root)
    root.mainloop()
