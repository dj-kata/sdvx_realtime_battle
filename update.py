#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import zipfile
import shutil
import subprocess
import threading
import time
from pathlib import Path
from packaging import version
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse

import logging, logging.handlers
import traceback
from bs4 import BeautifulSoup
import icon

# バージョン取得の改良版
def get_version():
    """
    複数の方法でバージョンを取得する
    優先順位: 1. version.py 2. Git 3. フォールバック
    """
    # 1. version.pyから取得（make時に自動生成）
    try:
        from version import __version__
        return __version__
    except ImportError:
        pass
    
    # 2. Gitタグから直接取得
    try:
        import subprocess
        result = subprocess.run(['git', 'describe', '--tags', '--always'], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            git_version = result.stdout.strip()
            # v.1.0.0 や v1.0.0 形式を 1.0.0 に正規化
            if git_version.startswith('v.'):
                return git_version[2:]
            elif git_version.startswith('v'):
                return git_version[1:]
            return git_version
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # 3. パッケージメタデータから取得（setup.pyがある場合）
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version(__package__ or 'sdvx_arena')
    except ImportError:
        try:
            import pkg_resources
            return pkg_resources.get_distribution(__package__ or 'sdvx_arena').version
        except:
            pass
    
    # 4. 従来のversion.txtから取得（フォールバック）
    try:
        with open('version.txt', 'r') as f:
            return f.readline().strip()
    except FileNotFoundError:
        pass
    
    # 5. 最終フォールバック
    return "0.0.0-unknown"

os.makedirs('log', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hdl = logging.handlers.RotatingFileHandler(
    f'log/{os.path.basename(__file__).split(".")[0]}.log',
    encoding='utf-8',
    maxBytes=1024*1024*2,
    backupCount=1,
)
hdl.setLevel(logging.DEBUG)
hdl_formatter = logging.Formatter('%(asctime)s %(filename)s:%(lineno)5d %(funcName)s() [%(levelname)s] %(message)s')
hdl.setFormatter(hdl_formatter)
logger.addHandler(hdl)

class GitHubUpdater:
    def __init__(self, github_author='', github_repo='', current_version=None, main_exe_name=None, updator_exe_name=None):
        """
        GitHub自動アップデータの初期化
        
        Args:
            github_repo (str): GitHubリポジトリ（例: "username/repository"）
            current_version (str): 現在のバージョン（例: "1.0.0"）。Noneの場合は自動取得
            main_exe_name (str): メインプログラムのexe名（例: "main.exe"）
            updator_exe_name (str): アップデート用プログラムのexe名 (例: "update.exe"）
        """
        self.github_author = github_author
        self.github_repo = github_repo
        self.current_version = current_version or get_version()
        self.main_exe_name = main_exe_name or "main.exe"
        self.updator_exe_name = updator_exe_name or "update.exe"
        self.base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
        self.temp_dir = self.base_dir / "tmp"
        self.backup_dir = self.base_dir / "backup"
        logger.debug(f"base_dir:{self.base_dir}, current_version:{self.current_version}")
        
        # GUI関連
        self.root = None
        self.progress_var = None
        self.status_var = None
        self.progress_bar = None

    # 以下のメソッドは元のコードと同じなので省略...
    # （ico_path, get_latest_version, check_for_updates, create_gui, update_status, 
    #  download_file, create_backup, replace_files2, create_restart_script, cleanup, 
    #  cancel_update, run_update, extract_zip_file, check_and_update, restart_program）

def main():
    # バージョンを自動取得
    SWVER = get_version()
    logger.info(f"Current version: {SWVER}")

    updater = GitHubUpdater(
        github_author='dj-kata',
        github_repo='otoge_realtime_battle',
        current_version=SWVER,           # 自動取得されたバージョン
        main_exe_name="sdvx_arena.exe",  # メインプログラムのexe名
        updator_exe_name="update.exe",   # アップデート用プログラムのexe名
    )
    
    # メインプログラムから呼び出す場合
    updater.check_and_update()

if __name__ == "__main__":
    main()