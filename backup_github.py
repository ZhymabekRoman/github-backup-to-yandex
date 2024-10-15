import logging
import os
import tarfile
from argparse import Namespace
from dataclasses import dataclass
from datetime import datetime as dt

import click
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
from pyzstd import CParameter, ZstdFile

from loguru_handler import register_loguru

register_loguru()


@dataclass
class GithubBackupConfig:
    PYZSTD_OPTIONS = {CParameter.nbWorkers: os.cpu_count() if (cpu_count := os.cpu_count()) else 1 + 1, CParameter.compressionLevel: 18}
    TIME: str = dt.now().strftime("%Y-%m-%d-%H-%M-%S")
    LOG_LEVEL: str = "DEBUG"
    BACKUP_FOLDER: str = "./backup-github"
    BACKUP_PART_SIZE_MB: int = 400
    INCREMENTAL: bool = True


logging.root.setLevel(GithubBackupConfig.LOG_LEVEL)


@click.command()
@click.option("--yd-token", prompt="Yandex Disk token")
@click.option("--github-token", prompt="GitHub classic token")
@click.option("--accounts", "-a", prompt="Accounts to backup in syntax: accountType:username", multiple=True)
def backup(yd_token: str, github_token: str, accounts: str):
    config = GithubBackupConfig()

    logger.debug("Initializing YandexDisk client...")
    yd_client = yadisk.YaDisk(token=yd_token)
    if not yd_token or not yd_client.check_token():
        raise ValueError("Yandex Disk token is invalid!")

    if not github_token:
        raise ValueError("No Github Access token was found!")

    if not accounts:
        raise ValueError("No ACCOUNTS value was found!")

    for account in accounts:
        account_type, user = account.split("|")
        is_organization = account_type.lower() == "org"

        args = Namespace(
            user=user,
            username=None,
            password=None,
            token_fine=None,
            token_classic=github_token,
            as_app=True,
            output_directory=config.BACKUP_FOLDER,
            log_level=config.LOG_LEVEL,
            incremental=config.INCREMENTAL,
            include_starred=False,
            all_starred=False,
            include_watched=False,
            include_followers=False,
            include_following=False,
            include_everything=False,
            include_issues=False,
            include_issue_comments=False,
            include_issue_events=False,
            include_pulls=False,
            include_pull_comments=False,
            include_pull_commits=False,
            include_pull_details=False,
            include_labels=False,
            include_hooks=False,
            include_milestones=False,
            include_repository=True,
            bare_clone=False,
            no_prune=False,
            lfs_clone=False,
            include_wiki=False,
            include_gists=True,
            include_starred_gists=False,
            skip_archived=False,
            skip_existing=False,
            languages=None,
            name_regex=None,
            github_host=None,
            organization=is_organization,
            repository=None,
            private=True,
            fork=True,
            prefer_ssh=False,
            osx_keychain_item_name=None,
            osx_keychain_item_account=None,
            include_releases=True,
            include_assets=False,
            throttle_limit=0,
            throttle_pause=30.0,
            exclude=None,
        )
        logger.debug(args)

        output_directory = os.path.realpath(args.output_directory)
        if not os.path.isdir(output_directory):
            logger.debug(f"Create output directory {output_directory}")
            mkdir_p(output_directory)

        # Idk, just ported from github_backup itself
        if not args.as_app:
            logger.debug(f"Backing up user {args.user} to {output_directory}")
            authenticated_user = get_authenticated_user(args)
        else:
            authenticated_user = {"login": None}

        repositories = retrieve_repositories(args, authenticated_user)
        logger.debug(repositories)
        filtered_repositories = filter_repositories(args, repositories)
        logger.debug(filtered_repositories)
        backup_repositories(args, output_directory, filtered_repositories)
        backup_account(args, output_directory)

    file_path = compress_folder(config)
    splited_backup = split_file(file_path, f"{config.BACKUP_FOLDER}-split", config.BACKUP_PART_SIZE_MB * (1048576))
    yd_client.mkdir(f"/backup/github/{config.TIME}")
    for file_path, filename in splited_backup:
        logger.debug(file_path, filename)
        yd_client.upload(file_path, f"/backup/github/{config.TIME}/{filename}.png", timeout=80_000)


def sizeof_fmt(num, suffix="B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def compress_folder(config: GithubBackupConfig) -> str:
    backup_compress_filename = f"backup-{config.TIME}"
    output_tar_filename = f"{backup_compress_filename}.tar"
    output_zstd_filename = f"{backup_compress_filename}.tar.zst"

    logger.debug("Compressing folder into tar...")
    with tarfile.open(output_tar_filename, "w") as tar:
        tar.add(config.BACKUP_FOLDER)

    logger.debug("Compressing tar into zstd...")
    with open(output_tar_filename, "rb") as tar, ZstdFile(output_zstd_filename, "w", level_or_option=config.PYZSTD_OPTIONS) as zst:
        logger.debug("Reading tar....")
        data = tar.read()
        zst.write(data)

    logger.debug(f"TAR.ZST file size: {sizeof_fmt(os.path.getsize(output_zstd_filename))}")
    return output_zstd_filename


def split_file(file: str, output_dir: str, size: int) -> list[tuple[str, str]]:
    os.makedirs(output_dir, exist_ok=True)
    split = Split(file, output_dir)
    split.bysize(size)
    return absoluteFilePaths(output_dir)


# https://stackoverflow.com/questions/9816816/get-absolute-paths-of-all-files-in-a-directory
def absoluteFilePaths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f)), f


if __name__ == "__main__":
    backup()
