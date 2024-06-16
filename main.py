import os
from collections import defaultdict
import hashlib
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scan_directory(directory):
    logging.info(f"Scanning directory: {directory}")
    file_info = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            try:
                size = os.path.getsize(path)
                file_info.append((path, size))
            except OSError as e:
                logging.error(f"Error accessing {path}: {e}")
    logging.info(f"Completed scanning. Found {len(file_info)} files.")
    return file_info

def group_by_size(file_info):
    logging.info("Grouping files by size.")
    size_dict = defaultdict(list)
    for path, size in file_info:
        size_dict[size].append(path)
    logging.info(f"Completed grouping by size. Found {len(size_dict)} size groups.")
    return size_dict

def hash_file(path, quick=False, blocksize=65536):
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

def find_duplicates(size_dict):
    logging.info("Finding duplicates.")
    duplicates = defaultdict(list)
    for size, files in tqdm(size_dict.items(), desc="Processing size groups"):
        if len(files) < 2:
            continue
        
        # Quick hash comparison
        quick_hashes = defaultdict(list)
        for file in tqdm(files, desc=f"Quick hashing files of size {size}", leave=False):
            quick_hash = hash_file(file, quick=True)
            if quick_hash:
                quick_hashes[quick_hash].append(file)
        
        # Full hash comparison
        for quick_hash, files in tqdm(quick_hashes.items(), desc="Full hashing", leave=False):
            if len(files) < 2:
                continue
            
            full_hashes = defaultdict(list)
            for file in tqdm(files, desc="Full hashing files", leave=False):
                full_hash = hash_file(file)
                if full_hash:
                    full_hashes[full_hash].append(file)
            
            for full_hash, dup_files in full_hashes.items():
                if len(dup_files) > 1:
                    duplicates[full_hash].extend(dup_files)
    logging.info(f"Completed finding duplicates. Found {len(duplicates)} duplicate groups.")
    return duplicates

def detect_duplicates(directory):
    logging.info(f"Starting duplicate detection in directory: {directory}")
    file_info = scan_directory(directory)
    size_dict = group_by_size(file_info)
    duplicates = find_duplicates(size_dict)
    logging.info("Duplicate detection completed.")
    return duplicates

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def list_files(directory):
    print('Listing Files in Directory:')
    if not os.path.exists(directory):
        logging.error(f"Directory does not exist: {directory}")
        return
    
    logging.info(f"Listing files in directory: {directory}")
    
    file_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            print(path)
            logging.debug(f"Found file: {path}")
            file_count += 1
    
    if file_count == 0:
        logging.info("No files found in the directory.")
    else:
        logging.info(f"Total files found: {file_count}")

# Example usage:
if __name__ == "__main__":
    directory = "H:\A7M4 Backup\/01-02-2024 Kochi"
    print(os.path.exists(directory))
    # list_files(directory)
    duplicates = detect_duplicates(directory)

    # Output duplicates
    for hash_val, files in duplicates.items():
        print(f"Duplicate group (hash: {hash_val}):")
        for file in files:
            print(f"  {file}")

        # Here you can add logic to delete or handle duplicates
