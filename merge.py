import os

import click
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


@click.command()
@click.option("--folder", default="./", help="Input folder path")
@click.option("--output-folder", default="BACKUP_OUTPUT_FOLDER", help="Output folder path")
def main(folder, output_folder):
    delete_file_extensions_in_folder(folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    merge = Merge(inputdir=folder, outputdir=output_folder, outputfilename="full_github_backup.tar.zstd")
    merge.merge()


if __name__ == "__main__":
    main()
