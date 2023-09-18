import tarfile
import pyzstd
from filesplit.merge import Merge

OUTPUT_FILENAME = "full_github_backup"
OUTPUT_FILENAME_TAR = f"{OUTPUT_FILENAME}.tar"
OUTPUT_FILENAME_TAR_ZST = f"{OUTPUT_FILENAME}.tar.zst"


def main(backup_folder: str):
    merge = Merge(inputdir=backup_folder, outputdir="BACKUP_OUTPUT_FOLDER", outputfilename=OUTPUT_FILENAME)
    merge.merge()

    with open(OUTPUT_FILENAME_TAR_ZST, 'rb') as zst, open(OUTPUT_FILENAME_TAR, 'wb') as tar:
        data = zst.read()
        tar.write(pyzstd.decompress(data))

    with tarfile.open(OUTPUT_FILENAME_TAR, 'rb') as tar:
        tar.extractall()


main()
