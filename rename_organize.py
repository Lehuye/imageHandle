import os
import uuid
import shutil

def rename_and_organize_files(directory):
    """
    Renames all files in the given directory using uuidv4 and organizes them
    into subdirectories based on their original extension.
    """
    renamed_files = []
    for filename in os.listdir(directory):
        if filename.startswith('.'):  # Skip hidden files
            continue

        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            name, ext = os.path.splitext(filename)
            ext = ext.lower()  # Ensure lowercase extension for consistency

            # Generate a new UUID-based filename
            new_name = str(uuid.uuid4())
            new_filename = f"{new_name}{ext}"

            # Create a subdirectory for the extension if it doesn't exist
            extension_directory = os.path.join(directory, ext[1:])  # Extension without the dot
            if not os.path.exists(extension_directory):
                os.makedirs(extension_directory)

            # Move the renamed file into the extension directory
            if os.path.abspath(directory) != os.path.abspath(extension_directory):
                new_file_path = os.path.join(extension_directory, new_filename)
                shutil.move(file_path, new_file_path)
                print(f"Renamed '{filename}' to '{new_filename}' and moved to '{extension_directory}'")
                renamed_files.append(new_file_path)
            else:
                new_file_path = os.path.join(directory, new_filename)
                os.rename(file_path, new_file_path)
                print(f"Renamed '{filename}' to '{new_filename}' in '{directory}'")
                renamed_files.append(new_file_path)
    return renamed_files
