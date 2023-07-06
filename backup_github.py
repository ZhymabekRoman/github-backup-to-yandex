import base64
import logging
import os
import shutil
import sys
from argparse import Namespace
from datetime import datetime as dt

import yadisk
from filesplit.split import Split
from github_backup.github_backup import (
    backup_account,
    backup_repositories,
    filter_repositories,
    get_authenticated_user,
    mkdir_p,
    retrieve_repositories,
)
from loguru import logger

from loguru_handler import register_loguru

TIME = dt.now().strftime('%Y-%m-%d-%H-%M-%S')
LOG_LEVEL = "DEBUG"
BACKUP_FOLDER = "./backup-github"
BACKUP_PART_SIZE_MB = 400


# def base64_sink(message):
#     encoded_message = base64.b64encode(message.encode('utf-8')).decode('utf-8')
#     print(encoded_message)
# logger.add(base64_sink)

logging.root.setLevel(LOG_LEVEL)


def main(github_token: str, accounts_raw: str):
  if not github_token:
      raise ValueError("No ACCESS_TOKEN was found!")

  if not accounts_raw:
      raise ValueError("No ACCOUNTS value was found!")

  for account in accounts_raw.split(","):
    account_type, user = account.split("||")
    if account_type.lower() == "org":
        organization = True
    else:
        organization = False

    args = Namespace(user=user, username=None, password=None, token=github_token, as_app=False, output_directory=BACKUP_FOLDER, log_level=LOG_LEVEL, incremental=True, include_starred=False, all_starred=False, include_watched=False, include_followers=False, include_following=False, include_everything=False, include_issues=False, include_issue_comments=False, include_issue_events=False, include_pulls=False, include_pull_comments=False, include_pull_commits=False, include_pull_details=False, include_labels=False, include_hooks=False, include_milestones=False, include_repository=True, bare_clone=False, no_prune=False, lfs_clone=False, include_wiki=False, include_gists=True, include_starred_gists=False, skip_archived=False, skip_existing=False, languages=None, name_regex=None, github_host=None, organization=organization, repository=None, private=True, fork=True, prefer_ssh=False, osx_keychain_item_name=None, osx_keychain_item_account=None, include_releases=True, include_assets=False, throttle_limit=0, throttle_pause=30.0, exclude=None)
    logger.debug(args)

    output_directory = os.path.realpath(args.output_directory)
    if not os.path.isdir(output_directory):
        logger.debug(f'Create output directory {output_directory}')
        mkdir_p(output_directory)

    if not args.as_app:
        logger.debug(f'Backing up user {args.user} to {output_directory}')
        authenticated_user = get_authenticated_user(args)
    else:
        authenticated_user = {'login': None}

    repositories = retrieve_repositories(args, authenticated_user)
    repositories = filter_repositories(args, repositories)
    backup_repositories(args, output_directory, repositories)
    backup_account(args, output_directory)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def zip_folder(folder: str = BACKUP_FOLDER):
    backup_zip_filename = f"backup-{TIME}"
    output_zip_file = shutil.make_archive(backup_zip_filename, 'zip', folder)
    logger.debug(f"ZIP file size: {sizeof_fmt(os.path.getsize(output_zip_file))}")
    return backup_zip_filename, output_zip_file


def split_file(file: str, output_dir: str, size: int):
    os.makedirs(output_dir, exist_ok=True)
    split = Split(file, output_dir)
    split.manfilename = f"manifest_{TIME}"
    split.bysize(size)
    return absoluteFilePaths(output_dir)


# https://stackoverflow.com/questions/9816816/get-absolute-paths-of-all-files-in-a-directory
def absoluteFilePaths(directory):
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f)), f


# https://medium.com/@kai_kebutsuka/how-to-upload-files-to-yandex-disk-using-python-d3211007d574
def yandex_upload(yandex_token: str, filename: str, file_path: str, file_ext: str):
    if not yandex_token:
        raise ValueError("No yandex token was found!")

    client = yadisk.YaDisk(token=yandex_token)
    if not client.check_token():
        raise ValueError("Yandex token is invalid!")

    client.upload(file_path, f"/backup/github/{filename}.{file_ext}", timeout=80_000)


if __name__ == '__main__':
    args = sys.argv[1:]
    logger.debug(args)
    try:
        register_loguru()
        main(args[0], args[1])
        filename, file_path = zip_folder()
        splited_backup = split_file(file_path, f"{BACKUP_FOLDER}-split", BACKUP_PART_SIZE_MB*(1048576))
        for file_path, filename in splited_backup:
            logger.debug(file_path, filename)
            yandex_upload(args[2], filename, file_path, 'png')
    except Exception as e:
        logger.exception(str(e))
        sys.exit(1)
