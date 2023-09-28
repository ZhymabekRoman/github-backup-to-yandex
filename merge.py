import os
from filesplit.merge import Merge

def delete_file_extension(filename):
    """Deletes the file extension of a file.

    Args:
        filename: The path to the file.
    """

    basename = os.path.basename(filename)
    ext = os.path.splitext(basename)[1]
    new_filename = basename.replace(ext, "")
    os.rename(filename, os.path.join(os.path.dirname(filename), new_filename))


def delete_file_extensions_in_folder(folder_path):
    """Deletes the file extension of all files in a folder.

    Args:
        folder_path: The path to the folder.
    """

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            delete_file_extension(file_path)


def main(folder: str = "./", output_folder: str = "BACKUP_OUTPUT_FOLDER"):
    delete_file_extensions_in_folder(folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    merge = Merge(inputdir=./, outputdir=output_folder, outputfilename="full_github_backup.tar.zstd")
    merge.merge()


main()
