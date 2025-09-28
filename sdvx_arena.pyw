#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import time
import requests
import json
import os
from PIL import Image, ImageTk
import logging
import traceback
from obssocket import OBSSocket
from detect_core import *
from enum import Enum

# 設定ファイルのパス
CONFIG_FILE = "settings.json"

class rotate_mode(Enum):
    left=0
    top=1
    right=2

    @classmethod
    def get_names(cls) -> list:
        return [i.name for i in cls]

class Config:
    def __init__(self):
        self.obs_host = "localhost"
        self.obs_port = "4444"
        self.obs_password = ""
        self.obs_scene = ""  # シーン名を保存
        self.obs_source = ""
        self.server_url = "https://otoge-realtime-battle.onrender.com"
        self.last_username = ""
        self.rotate_mode = 0 # left, top, right
        self.save_to_file = False # ファイル保存設定（デフォルト：オフ）
        self.load_config()
    
    def load_config(self):
        """設定ファイルから設定を読み込み"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.obs_host = data.get('obs_host', self.obs_host)
                    self.obs_port = data.get('obs_port', self.obs_port)
                    self.obs_password = data.get('obs_password', self.obs_password)
                    self.obs_scene = data.get('obs_scene', self.obs_scene)
                    self.obs_source = data.get('obs_source', self.obs_source)
                    self.server_url = data.get('server_url', self.server_url)
                    self.last_username = data.get('last_username', self.last_username)
                    self.rotate_mode = data.get('rotate_mode', self.rotate_mode)
                    self.save_to_file = data.get('save_to_file', self.save_to_file)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
    
    def save_config(self):
        """設定ファイルに設定を保存"""
        try:
            data = {
                'obs_host': self.obs_host,
                'obs_port': self.obs_port,
                'obs_password': self.obs_password,
                'obs_scene': self.obs_scene,
                'obs_source': self.obs_source,
                'server_url': self.server_url,
                'last_username': self.last_username,
                'rotate_mode': self.rotate_mode,
                'save_to_file': self.save_to_file
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")

class SettingsWindow:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.obs_socket = None
        self.window = tk.Toplevel(parent)
        self.window.title("設定")
        self.window.geometry("500x700")
        self.window.resizable(False, False)
        self.window.grab_set()  # モーダルダイアログにする
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        # OBS WebSocket設定
        obs_frame = ttk.LabelFrame(self.window, text="OBS WebSocket設定", padding=10)
        obs_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(obs_frame, text="ホスト:").grid(row=0, column=0, sticky="w", pady=2)
        self.host_entry = ttk.Entry(obs_frame, width=30)
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=2)
        
        ttk.Label(obs_frame, text="ポート:").grid(row=1, column=0, sticky="w", pady=2)
        self.port_entry = ttk.Entry(obs_frame, width=30)
        self.port_entry.grid(row=1, column=1, sticky="ew", pady=2)
        
        ttk.Label(obs_frame, text="パスワード:").grid(row=2, column=0, sticky="w", pady=2)
        self.password_entry = ttk.Entry(obs_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, sticky="ew", pady=2)
        
        # OBS接続ボタン
        self.connect_obs_button = ttk.Button(obs_frame, text="OBS接続", command=self.connect_obs)
        self.connect_obs_button.grid(row=3, column=0, columnspan=2, pady=(10, 5))
        
        self.obs_status_label = ttk.Label(obs_frame, text="接続状態: 未接続", foreground="red")
        self.obs_status_label.grid(row=4, column=0, columnspan=2, pady=2)
        
        obs_frame.columnconfigure(1, weight=1)
        
        # シーン・ソース選択
        scene_frame = ttk.LabelFrame(self.window, text="シーン・ソース選択", padding=10)
        scene_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(scene_frame, text="シーン:").grid(row=0, column=0, sticky="w", pady=2)
        self.scene_combo = ttk.Combobox(scene_frame, width=30, state="readonly")
        self.scene_combo.grid(row=0, column=1, sticky="ew", pady=2)
        self.scene_combo.bind("<<ComboboxSelected>>", self.on_scene_selected)
        
        ttk.Label(scene_frame, text="ソース:").grid(row=1, column=0, sticky="w", pady=2)
        self.source_combo = ttk.Combobox(scene_frame, width=30, state="readonly")
        self.source_combo.grid(row=1, column=1, sticky="ew", pady=2)
        
        scene_frame.columnconfigure(1, weight=1)
        
        # サーバー設定
        server_frame = ttk.LabelFrame(self.window, text="サーバー設定", padding=10)
        server_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(server_frame, text="サーバーURL:").grid(row=0, column=0, sticky="w", pady=2)
        self.server_url_entry = ttk.Entry(server_frame, width=30)
        self.server_url_entry.grid(row=0, column=1, sticky="ew", pady=2)
        
        server_frame.columnconfigure(1, weight=1)
        
        # その他設定
        other_frame = ttk.LabelFrame(self.window, text="その他の設定", padding=10)
        other_frame.pack(fill="x", padx=10, pady=5)
        
        # 回転モード設定
        ttk.Label(other_frame, text="画面の向き:").grid(row=0, column=0, sticky="w", pady=2)
        self.rotate_mode_var = tk.IntVar()
        rotate_frame = ttk.Frame(other_frame)
        rotate_frame.grid(row=0, column=1, sticky="w", pady=2)
        
        rotate_options = [("左回転", 0), ("回転なし", 1), ("右回転", 2)]
        for i, (text, value) in enumerate(rotate_options):
            ttk.Radiobutton(rotate_frame, text=text, variable=self.rotate_mode_var, 
                           value=value).pack(side="left", padx=(0, 10))
        
        # ファイル保存設定
        self.save_to_file_var = tk.BooleanVar()
        self.save_to_file_check = ttk.Checkbutton(other_frame, text="ファイル保存を行う(旧方式)", 
                                                 variable=self.save_to_file_var)
        self.save_to_file_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        other_frame.columnconfigure(1, weight=1)
        
        # ボタン
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self.save_settings).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self.window.destroy).pack(side="right")
    
    def load_current_settings(self):
        """現在の設定値をフィールドに読み込み"""
        self.host_entry.insert(0, self.config.obs_host)
        self.port_entry.insert(0, self.config.obs_port)
        self.password_entry.insert(0, self.config.obs_password)
        self.server_url_entry.insert(0, self.config.server_url)
        
        # 回転モードを設定
        self.rotate_mode_var.set(self.config.rotate_mode)
        
        # ファイル保存設定を読み込み
        self.save_to_file_var.set(self.config.save_to_file)
        
        # 設定済みのシーン名とソース名があれば設定
        if self.config.obs_scene:
            # シーンコンボボックスに設定値を追加（OBS未接続でも表示される）
            current_scenes = list(self.scene_combo['values']) if self.scene_combo['values'] else []
            if self.config.obs_scene not in current_scenes:
                current_scenes.append(self.config.obs_scene)
                self.scene_combo['values'] = current_scenes
            self.scene_combo.set(self.config.obs_scene)
        
        if self.config.obs_source:
            # ソースコンボボックスに設定値を追加（OBS未接続でも表示される）
            current_sources = list(self.source_combo['values']) if self.source_combo['values'] else []
            if self.config.obs_source not in current_sources:
                current_sources.append(self.config.obs_source)
                self.source_combo['values'] = current_sources
            self.source_combo.set(self.config.obs_source)
    
    def connect_obs(self):
        """OBSに接続してシーン一覧を取得"""
        try:
            host = self.host_entry.get() or "localhost"
            port = int(self.port_entry.get() or "4444")
            password = self.password_entry.get()
            
            if self.obs_socket:
                self.obs_socket.close()
            
            self.obs_socket = OBSSocket(
                host,
                port,
                password,
                "",  # ソース名は後で設定
                ""
            )
            
            # 接続テスト（シーン一覧取得）
            scenes = self.obs_socket.get_scenes()
            if scenes:
                self.obs_status_label.config(text="接続状態: 接続済み", foreground="blue")
                self.update_scene_list(scenes)
                messagebox.showinfo("成功", "OBSに接続しました。")
            else:
                self.obs_status_label.config(text="接続状態: 接続失敗", foreground="red")
                messagebox.showerror("エラー", "OBSへの接続に失敗しました。")
                
        except Exception as e:
            self.obs_status_label.config(text="接続状態: 接続失敗", foreground="red")
            messagebox.showerror("エラー", f"OBS接続エラー: {e}")
    
    def update_scene_list(self, scenes):
        """シーン一覧を更新"""
        scene_names = [scene['sceneName'] for scene in scenes]
        self.scene_combo['values'] = scene_names
        
        # 設定済みのシーンがあれば優先的に選択
        if self.config.obs_scene and self.config.obs_scene in scene_names:
            self.scene_combo.set(self.config.obs_scene)
            self.update_source_list(self.config.obs_scene)
        else:
            # 設定がない場合は現在のシーンを選択
            current_scene = None
            for scene in scenes:
                if scene.get('sceneIndex', 0) == 0:  # 現在のシーン
                    current_scene = scene['sceneName']
                    break
            
            if current_scene and current_scene in scene_names:
                self.scene_combo.set(current_scene)
                self.update_source_list(current_scene)
    
    def on_scene_selected(self, event):
        """シーン選択時の処理"""
        selected_scene = self.scene_combo.get()
        if selected_scene:
            self.update_source_list(selected_scene)
    
    def update_source_list(self, scene_name):
        """選択されたシーンのソース一覧を更新"""
        try:
            if self.obs_socket:
                sources = self.obs_socket.get_sources(scene_name)
                self.source_combo['values'] = sources
                
                # 設定に保存されているソースがあれば選択
                if self.config.obs_source in sources:
                    self.source_combo.set(self.config.obs_source)
                elif sources:
                    self.source_combo.set(sources[0])
                    
        except Exception as e:
            print(f"ソース一覧取得エラー: {e}")
    
    def save_settings(self):
        """設定を保存"""
        # ソース名が選択されているかチェック
        if not self.source_combo.get():
            messagebox.showwarning("警告", "ソースが選択されていません。\nOBSに接続してシーンとソースを選択してください。")
            return
        
        self.config.obs_host = self.host_entry.get()
        self.config.obs_port = self.port_entry.get()
        self.config.obs_password = self.password_entry.get()
        self.config.obs_scene = self.scene_combo.get()  # シーン名も保存
        self.config.obs_source = self.source_combo.get()
        self.config.server_url = self.server_url_entry.get()
        self.config.rotate_mode = self.rotate_mode_var.get()
        self.config.save_to_file = self.save_to_file_var.get()
        self.config.save_config()
        
        messagebox.showinfo("設定", "設定を保存しました。")
        self.window.destroy()

class ScoreSenderApp:
    def __init__(self):
        self.config = Config()
        self.root = tk.Tk()
        self.root.title("SDVX Realtime Battle")
        self.root.geometry("800x600")
        
        # アプリケーション状態
        self.obs_socket = None
        self.obs_connected = False
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # サーバー接続状態
        self.user_id = None
        self.username = ""
        self.server_connected = False
        
        # 部屋状態
        self.current_room_id = None
        self.current_room_name = ""
        self.rooms_data = []
        
        # ゲーム状態
        self.is_playing = False
        self.last_score_normal = 0
        self.last_score_ex = 0
        self.last_non_play_time = None  # 最後にプレイ画面でないと判定された時刻
        
        self.create_widgets()
        self.start_obs_monitoring()
    
    def create_widgets(self):
        # メニューバー
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="設定", menu=settings_menu)
        settings_menu.add_command(label="OBS/サーバー設定", command=self.open_settings)
        
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # OBS接続状態フレーム
        obs_frame = ttk.LabelFrame(main_frame, text="OBS WebSocket状態", padding=10)
        obs_frame.pack(fill="x", pady=(0, 10))
        
        self.obs_status_label = ttk.Label(obs_frame, text="接続状態: 未接続", foreground="red")
        self.obs_status_label.pack(anchor="w")
        
        ttk.Button(obs_frame, text="OBS再接続", command=self.reconnect_obs).pack(anchor="w", pady=(5, 0))
        
        # サーバー接続フレーム
        server_frame = ttk.LabelFrame(main_frame, text="サーバー接続", padding=10)
        server_frame.pack(fill="x", pady=(0, 10))
        
        # 名前入力
        name_frame = ttk.Frame(server_frame)
        name_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(name_frame, text="名前:").pack(side="left")
        self.name_entry = ttk.Entry(name_frame, width=20)
        self.name_entry.pack(side="left", padx=(5, 10))
        
        # 前回入力した名前を復元
        if self.config.last_username:
            self.name_entry.insert(0, self.config.last_username)
        
        self.connect_button = ttk.Button(name_frame, text="接続", command=self.connect_to_server)
        self.connect_button.pack(side="left")
        
        self.server_status_label = ttk.Label(server_frame, text="サーバー状態: 未接続", foreground="red")
        self.server_status_label.pack(anchor="w")
        
        # 部屋管理フレーム
        room_frame = ttk.LabelFrame(main_frame, text="部屋管理", padding=10)
        room_frame.pack(fill="both", expand=True)
        
        # 部屋操作ボタン
        room_button_frame = ttk.Frame(room_frame)
        room_button_frame.pack(fill="x", pady=(0, 10))
        
        self.refresh_button = ttk.Button(room_button_frame, text="部屋一覧更新", command=self.refresh_rooms)
        self.refresh_button.pack(side="left")
        
        self.join_button = ttk.Button(room_button_frame, text="入室", command=self.join_room, state="disabled")
        self.join_button.pack(side="left", padx=(10, 0))
        
        self.leave_button = ttk.Button(room_button_frame, text="退室", command=self.leave_room, state="disabled")
        self.leave_button.pack(side="left", padx=(10, 0))
        
        # 現在の部屋表示
        self.current_room_label = ttk.Label(room_frame, text="現在の部屋: なし", foreground="red")
        self.current_room_label.pack(anchor="w", pady=(0, 10))
        
        # 部屋一覧
        columns = ("name", "members", "rule", "password")
        self.room_tree = ttk.Treeview(room_frame, columns=columns, show="headings", height=10)
        
        self.room_tree.heading("name", text="部屋名")
        self.room_tree.heading("members", text="人数")
        self.room_tree.heading("rule", text="ルール")
        self.room_tree.heading("password", text="パスワード")
        
        self.room_tree.column("name", width=300)
        self.room_tree.column("members", width=80)
        self.room_tree.column("rule", width=100)
        self.room_tree.column("password", width=100)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(room_frame, orient="vertical", command=self.room_tree.yview)
        self.room_tree.configure(yscrollcommand=scrollbar.set)
        
        self.room_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 部屋選択イベント
        self.room_tree.bind("<<TreeviewSelect>>", self.on_room_select)
        
        # ウィンドウ終了時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def open_settings(self):
        """設定画面を開く"""
        SettingsWindow(self.root, self.config)
    
    def start_obs_monitoring(self):
        """OBS監視スレッドを開始"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self.obs_monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def stop_obs_monitoring(self):
        """OBS監視スレッドを停止"""
        self.monitoring_active = False
    
    def obs_monitoring_loop(self):
        """OBS監視メインループ"""
        while self.monitoring_active:
            try:
                # OBS接続確認
                if not self.obs_connected:
                    self.connect_obs()
                
                if self.obs_connected:
                    # 画像取得
                    img = self.get_screenshot()
                    
                    if img is not None:
                        img = get_rotate_img(img, self.config.rotate_mode)
                        img_crop = img.crop((691,396,1080,475))
                        img_score = get_monochro_img(img_crop)
                        
                        # ファイル保存設定がオンの場合は保存
                        if self.config.save_to_file:
                            img.save('tmp.png')
                        
                        # プレイ画面判定
                        was_playing = self.is_playing
                        raw_is_playing = self.is_onplay(img)
                        
                        current_time = time.time()
                        # 30秒以内に再度プレイ画面と判定しない
                        if (self.last_non_play_time is not None and 
                            current_time - self.last_non_play_time < 30 and 
                            was_playing):
                            # 40秒以内かつ前回プレイ中だった場合は強制的にプレイ中とする
                            self.is_playing = False
                            print(f"満点演出対策: プレイ継続と判定 (前回非プレイ判定から{current_time - self.last_non_play_time:.1f}秒)")
                        else:
                            self.is_playing = raw_is_playing
                        
                        # 非プレイ画面と判定された時刻を記録
                        if not self.is_playing and was_playing:
                            self.last_non_play_time = current_time
                            print(f"非プレイ画面判定時刻を記録: {current_time}")
                        
                        if self.is_playing:
                            # スコア取得
                            normal_score, ex_score = self.get_score(img_score)
                            
                            # スコア送信（値が変化した場合のみ）
                            if (normal_score != self.last_score_normal or 
                                ex_score != self.last_score_ex):
                                if normal_score is not None and int(normal_score) > 10000000:
                                    logger.error(f'不正スコアなのでスキップ ({normal_score}, {ex_score})')
                                else:
                                    self.send_score(normal_score, ex_score)
                                    self.last_score_normal = normal_score
                                    self.last_score_ex = ex_score
                        
                        elif was_playing and not self.is_playing:
                            # プレイ終了を検出
                            print("プレイ終了を検出 - 曲終了処理を実行")
                            self.finish_song()
                
                # 接続状態更新
                self.root.after(0, self.update_obs_status)
                
            except Exception as e:
                print(f"OBS監視エラー: {e}")
                self.obs_connected = False
            
            time.sleep(0.1)  # 100ms間隔で監視
    
    def connect_obs(self):
        """OBSに接続"""
        try:
            # ソース名が設定されているかチェック
            if not self.config.obs_source:
                print("警告: ソース名が設定されていません。設定画面でソースを選択してください。")
                self.obs_connected = False
                return
            
            if self.obs_socket:
                self.obs_socket.close()
            
            self.obs_socket = OBSSocket(
                self.config.obs_host,
                int(self.config.obs_port),
                self.config.obs_password,
                self.config.obs_source,  # 設定で指定されたソース名を使用
                ""  # スクリーンショット保存先は使用しない
            )
            
            # 接続テスト（シーン一覧取得）
            scenes = self.obs_socket.get_scenes()
            if scenes:
                self.obs_connected = True
                print(f"OBS接続成功 - ソース: {self.config.obs_source}")
            else:
                self.obs_connected = False
                
        except Exception as e:
            print(f"OBS接続エラー: {e}")
            self.obs_connected = False
    
    def reconnect_obs(self):
        """OBS再接続"""
        self.obs_connected = False
        self.connect_obs()
        self.update_obs_status()
    
    def update_obs_status(self):
        """OBS接続状態表示を更新"""
        if self.obs_connected:
            self.obs_status_label.config(text="接続状態: 接続済み", foreground="blue")
        else:
            self.obs_status_label.config(text="接続状態: 未接続", foreground="red")
    
    def get_screenshot(self):
        """OBSから画像を取得"""
        try:
            if self.obs_socket and self.obs_connected:
                # ソース名が設定されているかチェック
                if not self.config.obs_source:
                    print("エラー: ソース名が設定されていません")
                    self.obs_connected = False
                    return None
                
                # ファイル保存設定がオンの場合はファイル保存APIを使用
                if self.config.save_to_file:
                    import os
                    # 絶対パスでファイル保存
                    screenshot_path = os.path.abspath("screenshot_temp.png")
                    
                    # OBSのファイル保存APIを使用
                    success = self.obs_socket.save_screenshot_dst(screenshot_path)
                    if success:
                        # 保存されたファイルを読み込み
                        if os.path.exists(screenshot_path):
                            img = Image.open(screenshot_path)
                            # 一時ファイルを削除（オプション）
                            # os.remove(screenshot_path)
                            return img
                        else:
                            print(f"ファイルが見つかりません: {screenshot_path}")
                            return None
                    else:
                        print("OBSファイル保存に失敗しました")
                        # フォールバックとして通常の方法を試す
                        return self.obs_socket.get_screenshot()
                else:
                    # 通常のメモリ取得方式
                    return self.obs_socket.get_screenshot()
                    
        except Exception as e:
            print(f"スクリーンショット取得エラー: {e}")
            print("設定画面でソースが正しく選択されているか確認してください")
            self.obs_connected = False
        return None
    
    def is_onplay(self, image):
        return is_onplay(image)
    
    def get_score(self, image):
        return get_score(image), get_exscore(image)  # normal_score, ex_score
    
    def connect_to_server(self):
        """サーバーに接続"""
        username = self.name_entry.get().strip()
        if not username:
            messagebox.showwarning("警告", "名前を入力してください。")
            return
        
        try:
            url = f"{self.config.server_url}/api/connect"
            data = {"username": username}
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result["userId"]
                self.username = result["username"]
                self.server_connected = True
                
                # 接続成功時に名前を設定に保存
                self.config.last_username = username
                self.config.save_config()
                
                self.server_status_label.config(text=f"サーバー状態: 接続済み（{self.username}）", foreground="blue")
                self.connect_button.config(state="disabled")
                self.name_entry.config(state="disabled")
                self.refresh_button.config(state="normal")
                
                # 部屋一覧を自動更新
                self.refresh_rooms()
                
            else:
                messagebox.showerror("エラー", f"サーバー接続に失敗しました: {response.text}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"サーバー接続エラー: {e}")
    
    def refresh_rooms(self):
        """部屋一覧を更新"""
        if not self.server_connected:
            return
        
        try:
            url = f"{self.config.server_url}/api/rooms"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.rooms_data = response.json()
                self.update_room_list()
            else:
                messagebox.showerror("エラー", f"部屋一覧取得に失敗しました: {response.text}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"部屋一覧取得エラー: {e}")
    
    def update_room_list(self):
        """部屋一覧表示を更新"""
        # 既存のアイテムを削除
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        
        # 新しいデータを追加
        for room in self.rooms_data:
            rule_text = "EXスコア" if room["rule"] == "ex" else "通常スコア"
            password_text = "あり" if room["hasPassword"] else "なし"
            
            self.room_tree.insert("", "end", values=(
                room["name"],
                f"{room['memberCount']}人",
                rule_text,
                password_text
            ), tags=(room["id"],))
    
    def on_room_select(self, event):
        """部屋選択時の処理"""
        selection = self.room_tree.selection()
        if selection and not self.current_room_id:
            self.join_button.config(state="normal")
        else:
            self.join_button.config(state="disabled")
    
    def join_room(self):
        """部屋に入室"""
        selection = self.room_tree.selection()
        if not selection:
            return
        
        # 選択された部屋のIDを取得
        item = selection[0]
        room_values = self.room_tree.item(item, "values")
        room_name = room_values[0]
        
        # room_idを取得（tagsから）
        room_id = None
        for room in self.rooms_data:
            if room["name"] == room_name:
                room_id = room["id"]
                has_password = room["hasPassword"]
                break
        
        if not room_id:
            return
        
        password = None
        if has_password:
            password = simpledialog.askstring("パスワード", f"部屋 '{room_name}' のパスワードを入力してください:", show='*')
            if password is None:  # キャンセルされた場合
                return
        
        try:
            url = f"{self.config.server_url}/api/rooms/{room_id}/join"
            data = {"userId": self.user_id}
            if password:
                data["password"] = password
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                self.current_room_id = room_id
                self.current_room_name = room_name
                
                self.current_room_label.config(text=f"現在の部屋: {room_name}", foreground="blue")
                self.join_button.config(state="disabled")
                self.leave_button.config(state="normal")
                
                messagebox.showinfo("成功", f"部屋 '{room_name}' に入室しました。")
                
            else:
                error_data = response.json()
                messagebox.showerror("エラー", f"入室に失敗しました: {error_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"入室エラー: {e}")
    
    def leave_room(self):
        """部屋から退室"""
        if not self.current_room_id:
            return
        
        try:
            url = f"{self.config.server_url}/api/rooms/{self.current_room_id}/leave"
            data = {"userId": self.user_id}
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                room_name = self.current_room_name
                self.current_room_id = None
                self.current_room_name = ""
                
                self.current_room_label.config(text="現在の部屋: なし", foreground="red")
                self.join_button.config(state="disabled")
                self.leave_button.config(state="disabled")
                
                messagebox.showinfo("成功", f"部屋 '{room_name}' から退室しました。")
                
            else:
                messagebox.showerror("エラー", f"退室に失敗しました: {response.text}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"退室エラー: {e}")
    
    def send_score(self, normal_score, ex_score):
        """スコアをサーバーに送信"""
        if not self.current_room_id or not self.server_connected:
            return
        
        try:
            url = f"{self.config.server_url}/api/rooms/{self.current_room_id}/score"
            data = {
                "userId": self.user_id,
                "normalScore": normal_score,
                "exScore": ex_score
            }
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                print(f"スコア送信成功: {normal_score}/{ex_score}")
            else:
                print(f"スコア送信失敗: {response.text}")
                
        except Exception as e:
            print(f"スコア送信エラー: {e}")
    
    def finish_song(self):
        """曲終了をサーバーに通知"""
        if not self.current_room_id or not self.server_connected:
            return
        
        try:
            url = f"{self.config.server_url}/api/rooms/{self.current_room_id}/finish"
            data = {"userId": self.user_id}
            
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                print("曲終了通知送信成功")
            else:
                print(f"曲終了通知送信失敗: {response.text}")
                
        except Exception as e:
            print(f"曲終了通知送信エラー: {e}")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        self.stop_obs_monitoring()
        
        # 部屋から退室
        if self.current_room_id:
            self.leave_room()
        
        # OBS接続を閉じる
        if self.obs_socket:
            self.obs_socket.close()
        
        self.root.destroy()
    
    def run(self):
        """アプリケーションを実行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ScoreSenderApp()
    app.run()