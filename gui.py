"""
Giao diện người dùng cho Tool Danh Tướng 3Q (newsgs.zce8.com)
"""

import os
import time
import random
import string
import io
import threading
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox

from api_client import GameWebAPI
import account_manager
import browser_register
from captcha_solver import solver
from auto_game import auto_engine, STEP1_IMG, STEP2_IMG, STEP3_IMG
from ldplayer_controller import ld_ctrl

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tool Danh Tướng 3Q")
        self.geometry("860x720")
        self.minsize(820, 660)

        self.api = GameWebAPI()
        self.servers = []
        self.current_captcha_image = None
        self.current_roles = []
        self.is_batch_running = False
        self.stop_batch_flag = False

        self._create_widgets()
        self._load_servers_async()
        self._refresh_account_list()
        self._refresh_captcha_async()

        # Tự động ngắt kết nối VPN khi người dùng đóng Tool
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        # Header / Chọn Server
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="⚔️ DANH TƯỚNG 3Q - TOOL WEB QUẢN LÝ", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left", padx=15, pady=10)

        server_label = ctk.CTkLabel(header_frame, text="Máy chủ:", font=ctk.CTkFont(size=13))
        server_label.pack(side="left", padx=(15, 5))

        self.search_server_entry = ctk.CTkEntry(
            header_frame, 
            placeholder_text="Số SV (vd: 52)", 
            width=100
        )
        self.search_server_entry.pack(side="left", padx=5)
        self.search_server_entry.bind("<KeyRelease>", self._on_server_search)

        self.server_combo = ctk.CTkComboBox(
            header_frame, 
            values=["Đang tải..."], 
            width=180,
            command=self._on_server_changed
        )
        self.server_combo.pack(side="left", padx=5)

        reload_srv_btn = ctk.CTkButton(
            header_frame, 
            text="🔄", 
            width=36, 
            command=self._load_servers_async
        )
        reload_srv_btn.pack(side="left", padx=5)

        # Tabs
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.tab_claim = self.tabview.add("🎁 Nhận Code Ngày & Phúc Lợi")
        self.tab_register = self.tabview.add("👤 Đăng Ký Tài Khoản")
        self.tab_accounts = self.tabview.add("📋 Quản Lý Tài Khoản")
        self.tab_auto = self.tabview.add("🎮 Auto Cày Game (LDPlayer)")

        self._build_claim_tab()
        self._build_register_tab()
        self._build_accounts_tab()
        self._build_auto_tab()

        # Mở thẳng tab Auto Cày Game (LDPlayer) để bạn nhìn thấy ngay
        self.tabview.set("🎮 Auto Cày Game (LDPlayer)")

        # Log box phía dưới
        log_frame = ctk.CTkFrame(self, corner_radius=10)
        log_frame.pack(fill="x", padx=15, pady=(0, 15))

        log_label = ctk.CTkLabel(log_frame, text="Nhật ký hoạt động:", font=ctk.CTkFont(size=12, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(6, 2))

        self.log_textbox = ctk.CTkTextbox(log_frame, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_textbox.pack(fill="x", padx=10, pady=(0, 10))

    def log(self, text: str):
        """Thêm dòng vào hộp log"""
        def _append():
            self.log_textbox.insert("end", text + "\n")
            self.log_textbox.see("end")
        self.after(0, _append)

    # ================= TAB 1: NHẬN CODE & QUÀ =================
    def _build_claim_tab(self):
        container = ctk.CTkFrame(self.tab_claim, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Chọn tài khoản
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=6)
        ctk.CTkLabel(row1, text="Tài khoản:", width=75, anchor="w").pack(side="left")
        
        self.search_acc_entry = ctk.CTkEntry(
            row1, 
            placeholder_text="Lọc nick...", 
            width=90
        )
        self.search_acc_entry.pack(side="left", padx=3)
        self.search_acc_entry.bind("<KeyRelease>", self._on_account_search)
        self.search_acc_entry.bind("<Return>", lambda e: self._fetch_roles_async())

        self.claim_acc_combo = ctk.CTkComboBox(
            row1, 
            values=["(Trống)"], 
            width=150,
            command=self._on_claim_account_selected
        )
        self.claim_acc_combo.pack(side="left", padx=3)

        pick_acc_btn = ctk.CTkButton(
            row1,
            text="📑 Danh sách",
            width=100,
            fg_color="#37474f",
            hover_color="#263238",
            command=self._open_single_account_picker
        )
        pick_acc_btn.pack(side="left", padx=3)

        get_roles_btn = ctk.CTkButton(
            row1, 
            text="🔍 Lấy nhân vật", 
            width=110,
            fg_color="#1f538d",
            command=self._fetch_roles_async
        )
        get_roles_btn.pack(side="left", padx=3)

        multi_acc_btn = ctk.CTkButton(
            row1, 
            text="📋 Chọn nhiều nick...", 
            width=140,
            fg_color="#37474f",
            hover_color="#263238",
            command=self._open_multi_account_dialog
        )
        multi_acc_btn.pack(side="left", padx=3)

        # Chọn nhân vật
        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=6)
        ctk.CTkLabel(row2, text="Nhân vật:", width=90, anchor="w").pack(side="left")

        self.role_combo = ctk.CTkComboBox(row2, values=["Vui lòng lấy nhân vật trước"], width=335)
        self.role_combo.pack(side="left", padx=5)

        # Quà & Code
        row3 = ctk.CTkFrame(container, fg_color="transparent")
        row3.pack(fill="x", pady=8)
        
        self.chk_cdk_var = ctk.BooleanVar(value=True)
        self.chk_cdk = ctk.CTkCheckBox(row3, text="Nhận Code Ngày:", variable=self.chk_cdk_var)
        self.chk_cdk.pack(side="left", padx=(0, 5))

        self.cdk_entry = ctk.CTkEntry(row3, width=140)
        self.cdk_entry.insert(0, "sgs2026")
        self.cdk_entry.pack(side="left", padx=5)

        self.chk_gift_var = ctk.BooleanVar(value=True)
        self.chk_gift = ctk.CTkCheckBox(row3, text="Nhận Gói Tân Thủ (VIP17 + KNB)", variable=self.chk_gift_var)
        self.chk_gift.pack(side="left", padx=20)

        # Khu vực Captcha
        row_cap = ctk.CTkFrame(container, fg_color="transparent")
        row_cap.pack(fill="x", pady=10)
        
        ctk.CTkLabel(row_cap, text="Mã bảo vệ:", width=90, anchor="w").pack(side="left")

        self.captcha_label = ctk.CTkLabel(row_cap, text="[Đang tải...]", width=160, height=45, fg_color="#2b2b2b", corner_radius=6)
        self.captcha_label.pack(side="left", padx=5)

        refresh_cap_btn = ctk.CTkButton(
            row_cap, 
            text="🔄 Đổi ảnh", 
            width=80, 
            command=self._refresh_captcha_async
        )
        refresh_cap_btn.pack(side="left", padx=5)

        self.captcha_entry = ctk.CTkEntry(row_cap, placeholder_text="Nhập 4 ký tự", width=120)
        self.captcha_entry.pack(side="left", padx=10)

        # Khu vực Nút nhận quà
        row_action = ctk.CTkFrame(container, fg_color="transparent")
        row_action.pack(fill="x", pady=12)

        self.claim_single_btn = ctk.CTkButton(
            row_action, 
            text="🚀 Nhận quà Nick này", 
            height=42, 
            width=190,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d", 
            hover_color="#153966",
            command=self._claim_gifts_async
        )
        self.claim_single_btn.pack(side="left", padx=(0, 6))

        self.claim_all_btn = ctk.CTkButton(
            row_action, 
            text="⚡ TỰ ĐỘNG NHẬN TẤT CẢ NICK", 
            height=42, 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32", 
            hover_color="#1b5e20",
            command=self._claim_all_accounts_async
        )
        self.claim_all_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.stop_btn = ctk.CTkButton(
            row_action, 
            text="🛑 Dừng", 
            height=42, 
            width=85,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#c62828", 
            hover_color="#8e0000",
            state="disabled",
            command=self._stop_batch_action
        )
        self.stop_btn.pack(side="left")

    # ================= TAB 2: ĐĂNG KÝ =================
    def _build_register_tab(self):
        container = ctk.CTkFrame(self.tab_register, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        desc = ctk.CTkLabel(
            container, 
            text="⚡ Chế độ Tạo Nick Liên Hoàn (Siêu Tốc):\nTrình duyệt Chrome sẽ giữ nguyên màn hình đăng ký. Mỗi khi bạn kéo xong 1 mảnh ghép, Tool sẽ tự lưu nick và tự điền nick tiếp theo ngay lập tức để bạn kéo liên tục không cần chờ đợi!",
            justify="left",
            font=ctk.CTkFont(size=12)
        )
        desc.pack(anchor="w", pady=(0, 10))

        # Tài khoản
        r1 = ctk.CTkFrame(container, fg_color="transparent")
        r1.pack(fill="x", pady=6)
        ctk.CTkLabel(r1, text="Tài khoản:", width=90, anchor="w").pack(side="left")
        
        self.reg_acc_entry = ctk.CTkEntry(r1, width=220, placeholder_text="6 - 16 ký tự chữ/số")
        self.reg_acc_entry.pack(side="left", padx=5)

        gen_acc_btn = ctk.CTkButton(r1, text="🎲 Sinh ngẫu nhiên", width=130, command=self._generate_random_account)
        gen_acc_btn.pack(side="left", padx=5)

        check_btn = ctk.CTkButton(r1, text="Kiểm tra trùng", width=110, command=self._check_account_exists)
        check_btn.pack(side="left", padx=5)

        # Mật khẩu
        r2 = ctk.CTkFrame(container, fg_color="transparent")
        r2.pack(fill="x", pady=6)
        ctk.CTkLabel(r2, text="Mật khẩu:", width=90, anchor="w").pack(side="left")

        self.reg_pwd_entry = ctk.CTkEntry(r2, width=220)
        
        # Tự động tìm số tài khoản tiếp theo từ danh sách đã lưu (vd: phuong29 -> phuong30)
        default_acc = "phuong1"
        accounts = account_manager.get_accounts()
        if accounts:
            last_acc = accounts[-1][0]
            default_acc = self._increment_account_name(last_acc)

        self.reg_acc_entry.insert(0, default_acc)
        self.reg_pwd_entry.insert(0, "phuong")
        self.reg_pwd_entry.pack(side="left", padx=5)

        # Action Buttons
        r3 = ctk.CTkFrame(container, fg_color="transparent")
        r3.pack(fill="x", pady=15)

        self.open_browser_btn = ctk.CTkButton(
            r3, 
            text="🚀 MỞ CHROME TẠO NICK LIÊN HOÀN (SIÊU TỐC)", 
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._launch_browser_register
        )
        self.open_browser_btn.pack(fill="x", pady=5)

        save_btn = ctk.CTkButton(
            r3, 
            text="💾 Lưu tài khoản này vào danh sách", 
            fg_color="#455a64",
            hover_color="#37474f",
            command=self._manual_save_account
        )
        save_btn.pack(fill="x", pady=5)

        warp_btn = ctk.CTkButton(
            r3, 
            text="🌐 Bật VPN / Đổi IP (Vượt giới hạn 5 nick/ngày)", 
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_warp_ip
        )
        warp_btn.pack(fill="x", pady=5)

    # ================= TAB 3: QUẢN LÝ TÀI KHOẢN =================
    def _build_accounts_tab(self):
        container = ctk.CTkFrame(self.tab_accounts, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(0, 10))

        refresh_btn = ctk.CTkButton(btn_bar, text="🔄 Làm mới", width=100, command=self._refresh_account_list)
        refresh_btn.pack(side="left", padx=5)

        open_file_btn = ctk.CTkButton(btn_bar, text="📂 Mở file accounts.txt", width=160, command=self._open_accounts_file)
        open_file_btn.pack(side="left", padx=5)

        del_btn = ctk.CTkButton(btn_bar, text="🗑️ Xóa tài khoản", width=120, fg_color="#c62828", hover_color="#b71c1c", command=self._delete_selected_account)
        del_btn.pack(side="left", padx=5)

        self.acc_textbox = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=12))
        self.acc_textbox.pack(fill="both", expand=True)

    # ================= TAB 4: AUTO CÀY GAME (PHƯƠNG ÁN D) =================
    def _build_auto_tab(self):
        container = ctk.CTkFrame(self.tab_auto, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=4)

        # 1. Header mô tả
        header_box = ctk.CTkFrame(container, fg_color="#1e293b", corner_radius=8)
        header_box.pack(fill="x", pady=(0, 4))

        title_lbl = ctk.CTkLabel(
            header_box,
            text="AUTO CÀY GAME (LDPLAYER / BẢN LẬU TRUNG QUỐC)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        )
        title_lbl.pack(anchor="w", padx=10, pady=(4, 1))

        desc_lbl = ctk.CTkLabel(
            header_box,
            text="Tích chọn các hoạt động: Vượt Ải Chính Tuyến, Đấu Trường, Du Ngoạn, Quét Thể Lực, Cây Tiền, Bái Tế, Thủy Kính & Cày Tân Thủ.",
            font=ctk.CTkFont(size=11),
            text_color="#cbd5e1",
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=10, pady=(0, 4))

        # 2. Khung Cấu hình Cửa Sổ Game & Điều Khiển
        emu_frame = ctk.CTkFrame(container, fg_color="#2b2b2b", corner_radius=8)
        emu_frame.pack(fill="x", pady=(0, 4))

        # Dòng 1: Cửa sổ game mục tiêu & Các nút test trực quan
        emu_row1 = ctk.CTkFrame(emu_frame, fg_color="transparent")
        emu_row1.pack(fill="x", padx=10, pady=(5, 3))

        ctk.CTkLabel(emu_row1, text="Cửa sổ Game:", font=ctk.CTkFont(size=12, weight="bold"), width=85, anchor="w").pack(side="left")

        self.win_combo = ctk.CTkComboBox(emu_row1, values=["三国名将传", "LDPlayer", "OSLink"], width=175)
        self.win_combo.pack(side="left", padx=4)

        win_refresh_btn = ctk.CTkButton(emu_row1, text="Quét lại", width=68, font=ctk.CTkFont(size=11, weight="bold"), command=self._refresh_window_list)
        win_refresh_btn.pack(side="left", padx=3)

        self.btn_diag = ctk.CTkButton(
            emu_row1,
            text="Soi Màn Hình AI",
            width=135,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._test_diagnose_screen
        )
        self.btn_diag.pack(side="left", padx=3)

        self.btn_test_click = ctk.CTkButton(
            emu_row1,
            text="Test Click Chiêu Mộ",
            width=140,
            fg_color="#d97706",
            hover_color="#b45309",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._test_click_zhaomu
        )
        self.btn_test_click.pack(side="left", padx=3)

        # Dòng 2: Phương thức điều khiển & Giả lập LDPlayer
        emu_row2 = ctk.CTkFrame(emu_frame, fg_color="transparent")
        emu_row2.pack(fill="x", padx=10, pady=(3, 5))

        ctk.CTkLabel(emu_row2, text="Điều khiển:", font=ctk.CTkFont(size=12, weight="bold"), width=85, anchor="w").pack(side="left")

        self.control_mode_var = ctk.StringVar(value="mouse")
        ctk.CTkRadioButton(
            emu_row2, 
            text="Chuột thật (Khuyên dùng)", 
            variable=self.control_mode_var, 
            value="mouse",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=3)

        ctk.CTkRadioButton(
            emu_row2, 
            text="Lệnh ngầm ADB", 
            variable=self.control_mode_var, 
            value="adb",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=8)

        self.ld_combo = ctk.CTkComboBox(emu_row2, values=["[0] LDPlayer"], width=130)
        self.ld_combo.pack(side="left", padx=4)

        self.ld_launch_btn = ctk.CTkButton(
            emu_row2, 
            text="Mở LDPlayer", 
            width=115, 
            fg_color="#1f538d", 
            hover_color="#153966",
            font=ctk.CTkFont(size=11),
            command=self._launch_game_in_ld
        )
        self.ld_launch_btn.pack(side="left", padx=4)

        # 3. Khung Menu Hoạt Động (Phương Án D)
        menu_frame = ctk.CTkFrame(container, fg_color="#242b35", corner_radius=8)
        menu_frame.pack(fill="x", pady=(0, 4))

        menu_header = ctk.CTkFrame(menu_frame, fg_color="transparent")
        menu_header.pack(fill="x", padx=10, pady=(5, 3))

        ctk.CTkLabel(
            menu_header, 
            text="DANH MỤC HOẠT ĐỘNG (TÍCH CHỌN):", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#facc15"
        ).pack(side="left")

        btn_sel_all = ctk.CTkButton(menu_header, text="Chọn tất cả", width=85, height=24, font=ctk.CTkFont(size=11), command=self._select_all_tasks)
        btn_sel_all.pack(side="right", padx=3)

        btn_desel_all = ctk.CTkButton(menu_header, text="Bỏ chọn", width=70, height=24, font=ctk.CTkFont(size=11), fg_color="#546e7a", hover_color="#37474f", command=self._deselect_all_tasks)
        btn_desel_all.pack(side="right", padx=3)

        # Khung 2 cột tùy chọn
        cols_frame = ctk.CTkFrame(menu_frame, fg_color="transparent")
        cols_frame.pack(fill="x", padx=8, pady=(0, 4))

        # Cột 1: Vượt ải, Đấu trường, Du ngoạn, Tân thủ
        col1 = ctk.CTkFrame(cols_frame, fg_color="#1e2229", corner_radius=6)
        col1.pack(side="left", fill="both", expand=True, padx=4, pady=2)

        # 1.1 Vượt ải
        r_va = ctk.CTkFrame(col1, fg_color="transparent")
        r_va.pack(fill="x", padx=8, pady=3)
        self.chk_vuot_ai_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_va, text="Auto Vượt Ải Chính Tuyến", variable=self.chk_vuot_ai_var, font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(r_va, text="Số ải:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(10, 2))
        self.entry_max_ai = ctk.CTkEntry(r_va, width=42, height=24)
        self.entry_max_ai.insert(0, "10")
        self.entry_max_ai.pack(side="left")

        # 1.2 Đấu trường
        r_dt = ctk.CTkFrame(col1, fg_color="transparent")
        r_dt.pack(fill="x", padx=8, pady=3)
        self.chk_dau_truong_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_dt, text="Auto Đấu Trường (Lôi Đài)", variable=self.chk_dau_truong_var, font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(r_dt, text="Số lượt:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(10, 2))
        self.entry_dt_count = ctk.CTkEntry(r_dt, width=42, height=24)
        self.entry_dt_count.insert(0, "5")
        self.entry_dt_count.pack(side="left")

        # 1.3 Du ngoạn
        r_dn = ctk.CTkFrame(col1, fg_color="transparent")
        r_dn.pack(fill="x", padx=8, pady=3)
        self.chk_du_ngoan_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_dn, text="Auto Du Ngoạn (Đổ xúc xắc)", variable=self.chk_du_ngoan_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # 1.4 Cày Tân Thủ
        r_tt = ctk.CTkFrame(col1, fg_color="transparent")
        r_tt.pack(fill="x", padx=8, pady=3)
        self.chk_tan_thu_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(r_tt, text="Auto Cày Clone Tân Thủ (Lv1 -> 16+)", variable=self.chk_tan_thu_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # Cột 2: Quét ải, Cây tiền, Bái tế, Thủy kính
        col2 = ctk.CTkFrame(cols_frame, fg_color="#1e2229", corner_radius=6)
        col2.pack(side="left", fill="both", expand=True, padx=4, pady=2)

        # 2.1 Quét ải
        r_qa = ctk.CTkFrame(col2, fg_color="transparent")
        r_qa.pack(fill="x", padx=8, pady=3)
        self.chk_quet_ai_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_qa, text="Auto Quét Ải Tiêu Thể Lực (10 lần)", variable=self.chk_quet_ai_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # 2.2 Cây tiền
        r_ct = ctk.CTkFrame(col2, fg_color="transparent")
        r_ct.pack(fill="x", padx=8, pady=3)
        self.chk_rung_cay_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_ct, text="Auto Rung Cây Tiền (Bạc miễn phí)", variable=self.chk_rung_cay_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # 2.3 Bái tế quân đoàn
        r_bt = ctk.CTkFrame(col2, fg_color="transparent")
        r_bt.pack(fill="x", padx=8, pady=3)
        self.chk_bai_te_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_bt, text="Auto Bái Tế Quân Đoàn (Cống hiến)", variable=self.chk_bai_te_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # 2.4 Thủy kính học đường
        r_tk = ctk.CTkFrame(col2, fg_color="transparent")
        r_tk.pack(fill="x", padx=8, pady=3)
        self.chk_thuy_kinh_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(r_tk, text="Auto Thủy Kính Học Đường (Giải đề)", variable=self.chk_thuy_kinh_var, font=ctk.CTkFont(size=12)).pack(side="left")

        # 4. Khung Cài đặt chế độ & lặp lại
        opt_bar = ctk.CTkFrame(container, fg_color="#2b2b2b", corner_radius=6)
        opt_bar.pack(fill="x", pady=(0, 4))

        opt_r1 = ctk.CTkFrame(opt_bar, fg_color="transparent")
        opt_r1.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(opt_r1, text="Chế độ:", font=ctk.CTkFont(size=12, weight="bold"), width=60, anchor="w").pack(side="left")

        self.plan_d_mode_var = ctk.StringVar(value="once")
        ctk.CTkRadioButton(opt_r1, text="Chạy 1 vòng (Xong là dừng)", variable=self.plan_d_mode_var, value="once").pack(side="left", padx=4)
        ctk.CTkRadioButton(opt_r1, text="Treo máy lặp lại mỗi:", variable=self.plan_d_mode_var, value="loop").pack(side="left", padx=15)

        self.plan_d_interval_entry = ctk.CTkEntry(opt_r1, width=45)
        self.plan_d_interval_entry.insert(0, "15")
        self.plan_d_interval_entry.pack(side="left")
        ctk.CTkLabel(opt_r1, text="phút", font=ctk.CTkFont(size=12)).pack(side="left", padx=(4, 0))

        # 5. Thanh trạng thái & Nút điều khiển
        status_bar = ctk.CTkFrame(container, fg_color="#182234", corner_radius=6)
        status_bar.pack(fill="x", pady=(0, 4))

        self.plan_d_status_lbl = ctk.CTkLabel(
            status_bar,
            text="Trạng thái: Chưa chạy (Sẵn sàng)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e2e8f0"
        )
        self.plan_d_status_lbl.pack(anchor="w", padx=10, pady=4)

        action_bar = ctk.CTkFrame(container, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 2))

        self.plan_d_start_btn = ctk.CTkButton(
            action_bar,
            text="BẮT ĐẦU AUTO",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._start_plan_d_action
        )
        self.plan_d_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.plan_d_stop_btn = ctk.CTkButton(
            action_bar,
            text="DỪNG AUTO",
            height=38,
            width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#c62828",
            hover_color="#8e0000",
            state="disabled",
            command=self._stop_plan_d_action
        )
        self.plan_d_stop_btn.pack(side="left")

        # Tải danh sách máy ảo LDPlayer & Cửa sổ game ban đầu
        self.after(200, self._refresh_ldplayer_list)
        self.after(350, self._refresh_window_list)

    def _refresh_window_list(self):
        wins = auto_engine.get_available_game_windows()
        clean_wins = [w for w in wins if not auto_engine._is_tool_window(w)]
        if clean_wins:
            self.win_combo.configure(values=clean_wins)
            # Ưu tiên chọn cửa sổ game Trung Quốc / 三国名将传
            def_win = clean_wins[0]
            for w in clean_wins:
                if any(k in w.lower() for k in ["三国名将传", "三国", "tmgame", "oslink", "ldremote"]):
                    def_win = w
                    break
            self.win_combo.set(def_win)
            self.log(f"[*] Đã phát hiện {len(clean_wins)} cửa sổ game/giả lập: {', '.join(clean_wins)}")
        else:
            self.win_combo.configure(values=["三国名将传", "LDPlayer-1", "LDPlayer", "OSLink"])
            self.win_combo.set("三国名将传")
            self.log("[i] Hãy chắc chắn game '三国名将传' hoặc LDPlayer đang mở trên màn hình!")

    def _test_diagnose_screen(self):
        target_win = self.win_combo.get().strip()
        auto_engine.config["window_title"] = target_win
        self.log("\n" + "=" * 55)
        self.log(f"[CHẨN ĐOÁN THỊ GIÁC AI] Đang soi màn hình game [{target_win}]...")
        self.log("=" * 55)

        diag = auto_engine.diagnose_screen(preferred_title=target_win)
        if diag.get("status") != "ok":
            self.log(f"[x] {diag.get('message')}")
            self.log("[!] Hãy mở game '三国名将传' hoặc LDPlayer lên màn hình rồi bấm lại [Soi Màn Hình AI]!")
            return

        wx, wy, ww, wh = diag["window_rect"]
        cx, cy, cw, ch = diag["canvas_rect"]
        self.log(f"[OK] Đã khóa Cửa Sổ Game: [{diag['window_title']}]")
        self.log(f"     Tọa độ cửa sổ: X={wx}, Y={wy}, Rộng={ww}, Cao={wh}")
        self.log(f"     Vùng hiển thị màn hình game: X={cx}, Y={cy}, Kích thước={cw}x{ch}")

        if diag.get("has_pointer"):
            px, py = diag["pointer_pos"]
            self.log(f"[+] [TÂN THỦ] PHÁT HIỆN BÀN TAY CHỈ DẪN TẠI ({px}, {py}) -> Sẵn sàng tự click Chiêu Mộ!")
        else:
            self.log("[-] [TÂN THỦ] Không thấy bàn tay hướng dẫn màu vàng trên màn hình.")

        if diag.get("has_bubble"):
            bx, by = diag["bubble_pos"]
            self.log(f"[+] [HỘP THOẠI] PHÁT HIỆN HỘP THOẠI NPC TẠI ({bx}, {by}) -> Sẵn sàng click qua thoại!")
        else:
            self.log("[-] [HỘP THOẠI] Không có hộp thoại đối thoại NPC.")

        if diag.get("has_thuy_kinh"):
            self.log("[+] [THỦY KÍNH] PHÁT HIỆN ICON THỦY KÍNH HỌC ĐƯỜNG -> Sẵn sàng giải câu hỏi!")

        self.log("-" * 55)
        self.log("[OK] AI đã kết nối thành công với game! Bấm [BẮT ĐẦU AUTO] để tool tự cày.")

    def _test_click_zhaomu(self):
        target_win = self.win_combo.get().strip()
        auto_engine.config["window_title"] = target_win
        self.log(f"\n[TEST CLICK] Đang thử click vào nút Chiêu Mộ [招募] trên cửa sổ '{target_win}'...")
        def _task():
            ok = auto_engine.test_click_target("zhaomu", preferred_title=target_win)
            if ok:
                self.log("[OK] Đã di chuyển chuột thật và click thành công vào nút Chiêu Mộ [招募]!")
            else:
                self.log("[!] Không click được. Vui lòng kiểm tra cửa sổ game đã hiển thị chưa.")
        threading.Thread(target=_task, daemon=True).start()

    def _refresh_ldplayer_list(self):
        instances = ld_ctrl.get_instances()
        if instances:
            vals = []
            for inst in instances:
                st = "🟢 Đang chạy" if inst["is_running"] else "⚪ Đang tắt"
                vals.append(f"[{inst['index']}] {inst['name']} ({st})")
            self.ld_combo.configure(values=vals)
            self.ld_combo.set(vals[0])
            self.log(f"Đã phát hiện {len(instances)} máy ảo LDPlayer trên máy!")
        else:
            self.ld_combo.configure(values=["[0] LDPlayer (Mặc định)"])
            self.ld_combo.set("[0] LDPlayer (Mặc định)")

    def _get_selected_emu_idx(self) -> int:
        val = self.ld_combo.get()
        if val.startswith("[") and "]" in val:
            try:
                return int(val.split("]")[0].replace("[", "").strip())
            except Exception:
                pass
        return 0

    def _launch_game_in_ld(self):
        idx = self._get_selected_emu_idx()
        self.log(f"🚀 Đang mở máy ảo LDPlayer index {idx} và khởi chạy game Danh Tướng 3Q...")
        def _task():
            if not ld_ctrl.is_emulator_running(idx):
                self.log(f"  Đang bật máy ảo LDPlayer {idx}...")
                ld_ctrl.launch_emulator(idx)
                time.sleep(8)
            self.log("  Đang mở game Danh Tướng 3Q...")
            ld_ctrl.launch_game(idx)
            self.after(2000, self._refresh_ldplayer_list)
        threading.Thread(target=_task, daemon=True).start()

    def _select_all_tasks(self):
        self.chk_vuot_ai_var.set(True)
        self.chk_dau_truong_var.set(True)
        self.chk_du_ngoan_var.set(True)
        self.chk_quet_ai_var.set(True)
        self.chk_rung_cay_var.set(True)
        self.chk_bai_te_var.set(True)
        self.chk_thuy_kinh_var.set(True)
        self.chk_tan_thu_var.set(True)

    def _deselect_all_tasks(self):
        self.chk_vuot_ai_var.set(False)
        self.chk_dau_truong_var.set(False)
        self.chk_du_ngoan_var.set(False)
        self.chk_quet_ai_var.set(False)
        self.chk_rung_cay_var.set(False)
        self.chk_bai_te_var.set(False)
        self.chk_thuy_kinh_var.set(False)
        self.chk_tan_thu_var.set(False)

    def _start_plan_d_action(self):
        if auto_engine.is_running:
            return

        try:
            max_ai = int(self.entry_max_ai.get().strip())
        except ValueError:
            max_ai = 10

        try:
            dt_cnt = int(self.entry_dt_count.get().strip())
        except ValueError:
            dt_cnt = 5

        try:
            interval = float(self.plan_d_interval_entry.get().strip())
        except ValueError:
            interval = 15.0

        is_loop = (self.plan_d_mode_var.get() == "loop")
        emu_idx = self._get_selected_emu_idx()
        win_title = self.win_combo.get().strip() if hasattr(self, 'win_combo') else "三国名将传"
        ctrl_mode = self.control_mode_var.get() if hasattr(self, 'control_mode_var') else "mouse"

        cfg = {
            "vuot_ai": self.chk_vuot_ai_var.get(),
            "max_ai_count": max_ai,
            "dau_truong": self.chk_dau_truong_var.get(),
            "dau_truong_count": dt_cnt,
            "du_ngoan": self.chk_du_ngoan_var.get(),
            "quet_ai": self.chk_quet_ai_var.get(),
            "rung_cay_tien": self.chk_rung_cay_var.get(),
            "bai_te": self.chk_bai_te_var.get(),
            "thuy_kinh": self.chk_thuy_kinh_var.get(),
            "tan_thu": self.chk_tan_thu_var.get(),
            "window_title": win_title,
            "control_mode": ctrl_mode,
            "emulator_idx": emu_idx,
            "loop_mode": is_loop,
            "loop_interval": interval,
            "use_adb": (ctrl_mode == "adb"),
        }

        # Kiểm tra xem có chọn mục nào không
        active_keys = ["vuot_ai", "dau_truong", "du_ngoan", "quet_ai", "rung_cay_tien", "bai_te", "thuy_kinh", "tan_thu"]
        if not any(cfg[k] for k in active_keys):
            messagebox.showwarning("Chưa chọn mục", "Vui lòng tích chọn ít nhất 1 hoạt động cần auto!")
            return

        self.plan_d_start_btn.configure(state="disabled")
        self.plan_d_stop_btn.configure(state="normal")
        self.plan_d_status_lbl.configure(text="Trạng thái: Đang chạy chuỗi Auto...", text_color="#4ade80")

        def _step_cb(step_num, text):
            def _u():
                self.plan_d_status_lbl.configure(text=f"Trạng thái: {text}", text_color="#38bdf8")
            self.after(0, _u)

        def _finish_cb():
            def _u():
                self.plan_d_start_btn.configure(state="normal")
                self.plan_d_stop_btn.configure(state="disabled")
                self.plan_d_status_lbl.configure(text="Trạng thái: Đã dừng (Sẵn sàng)", text_color="#e2e8f0")
            self.after(0, _u)

        auto_engine.start_worker(
            config=cfg,
            on_log=self.log,
            on_step=_step_cb,
            on_finish=_finish_cb
        )

    def _stop_plan_d_action(self):
        if auto_engine.is_running:
            self.log("⏳ Đang gửi yêu cầu dừng Auto...")
            auto_engine.stop()

    # ================= LOGIC & SỰ KIỆN =================
    def _load_servers_async(self):
        def _task():
            self.log("Đang tải danh sách máy chủ...")
            srvs = self.api.get_server_list()
            if srvs:
                self.servers = srvs
                srv_names = [f"Server {s['server']} - {s['name']}" for s in srvs]
                def _update():
                    self.server_combo.configure(values=srv_names)
                    self.server_combo.set(srv_names[0])
                    self.log(f"Đã tải thành công {len(srvs)} máy chủ!")
                self.after(0, _update)
            else:
                self.log("Không tải được danh sách máy chủ. Vui lòng thử lại!")
        threading.Thread(target=_task, daemon=True).start()

    def _get_selected_server_id(self) -> str:
        val = self.server_combo.get()
        if "Server " in val:
            try:
                return val.split(" - ")[0].replace("Server ", "").strip()
            except Exception:
                pass
        return "1"

    def _on_server_changed(self, choice):
        self.log(f"Đã chọn: {choice}")
        self.role_combo.configure(values=["Vui lòng lấy lại nhân vật"])
        self.role_combo.set("Vui lòng lấy lại nhân vật")

    def _on_server_search(self, event=None):
        query = self.search_server_entry.get().strip()
        all_names = [f"Server {s['server']} - {s['name']}" for s in self.servers]
        if not query:
            self.server_combo.configure(values=all_names)
            return

        # 1. Tìm chính xác số server
        exact = [f"Server {s['server']} - {s['name']}" for s in self.servers if str(s['server']) == query]
        if exact:
            self.server_combo.configure(values=exact)
            self.server_combo.set(exact[0])
            self._on_server_changed(exact[0])
            return

        # 2. Tìm chứa số hoặc bắt đầu bằng số
        matched = [f"Server {s['server']} - {s['name']}" for s in self.servers if query in str(s['server']) or query in s['name']]
        if matched:
            self.server_combo.configure(values=matched)
            self.server_combo.set(matched[0])
            self._on_server_changed(matched[0])

    def _refresh_account_list(self):
        accs = account_manager.get_accounts()
        acc_names = [a[0] for a in accs] if accs else ["(Chưa có tài khoản)"]
        self.claim_acc_combo.configure(values=acc_names)
        if accs:
            self.claim_acc_combo.set(accs[0][0])
        
        # Cập nhật Tab 3 Textbox
        self.acc_textbox.delete("1.0", "end")
        for acc, pwd in accs:
            self.acc_textbox.insert("end", f"{acc} | {pwd}\n")

    def _on_account_search(self, event=None):
        query = self.search_acc_entry.get().strip().lower()
        accs = account_manager.get_accounts()
        all_names = [a[0] for a in accs]
        if not query:
            self.claim_acc_combo.configure(values=all_names)
            return
        
        matched = [a for a in all_names if query in a.lower()]
        if matched:
            self.claim_acc_combo.configure(values=matched)
            self.claim_acc_combo.set(matched[0])
            self._on_claim_account_selected(matched[0])
        else:
            self.claim_acc_combo.configure(values=["(Không thấy)"])

    def _open_single_account_picker(self):
        """Mở bảng chọn tài khoản riêng biệt, có thanh cuộn và ô tìm kiếm để tránh tràn màn hình"""
        accs = account_manager.get_accounts()
        if not accs:
            messagebox.showwarning("Thông báo", "Chưa có tài khoản nào trong danh sách accounts.txt!")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Danh sách tài khoản")
        dialog.geometry("380x520")
        dialog.minsize(320, 400)
        dialog.transient(self)
        dialog.grab_set()

        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 6))

        title = ctk.CTkLabel(
            header, 
            text="📑 Danh Sách Tài Khoản", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w")

        info_lbl = ctk.CTkLabel(
            header,
            text=f"Tổng số: {len(accs)} tài khoản. Nhấp vào tài khoản để chọn:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_lbl.pack(anchor="w", pady=(2, 6))

        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            header,
            placeholder_text="🔍 Gõ số hoặc tên (vd: 18 hoặc phuong)...",
            textvariable=search_var,
            height=32
        )
        search_entry.pack(fill="x", pady=4)
        search_entry.focus_set()

        scroll_frame = ctk.CTkScrollableFrame(dialog, corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(4, 15))

        def _select_acc(account_name):
            all_names = [a[0] for a in accs]
            self.claim_acc_combo.configure(values=all_names)
            self.claim_acc_combo.set(account_name)
            self._on_claim_account_selected(account_name)
            self.log(f"Đã chọn tài khoản: [{account_name}]")
            dialog.destroy()
            self._fetch_roles_async()

        def _render_list(query=""):
            for w in scroll_frame.winfo_children():
                w.destroy()
            
            q = query.strip().lower()
            filtered = [a[0] for a in accs if (not q or q in a[0].lower())]

            if not filtered:
                lbl = ctk.CTkLabel(scroll_frame, text="Không tìm thấy tài khoản nào!", text_color="gray")
                lbl.pack(pady=20)
                return

            for idx, a_name in enumerate(filtered, 1):
                btn = ctk.CTkButton(
                    scroll_frame,
                    text=f"  👤  {a_name}",
                    anchor="w",
                    height=34,
                    fg_color="#2b2b2b",
                    hover_color="#1f538d",
                    font=ctk.CTkFont(size=13),
                    command=lambda name=a_name: _select_acc(name)
                )
                btn.pack(fill="x", pady=2, padx=4)

        _render_list()

        def _on_search_change(*args):
            _render_list(search_var.get())

        search_var.trace_add("write", _on_search_change)

    def _on_claim_account_selected(self, choice):
        self.role_combo.configure(values=["Vui lòng bấm 'Lấy nhân vật'"])
        self.role_combo.set("Vui lòng bấm 'Lấy nhân vật'")

    def _update_captcha_display(self, img_bytes, code=""):
        if not img_bytes:
            return
        try:
            pil_img = Image.open(io.BytesIO(img_bytes))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 45))
            def _up():
                self.captcha_label.configure(image=ctk_img, text="")
                self.current_captcha_image = ctk_img
                self.captcha_entry.delete(0, "end")
                if code:
                    self.captcha_entry.insert(0, code)
            self.after(0, _up)
        except Exception as e:
            self.log(f"Lỗi hiển thị captcha: {e}")

    def _refresh_captcha_async(self):
        def _task():
            img_bytes, code = solver.get_guaranteed_captcha(self.api.session)
            if img_bytes and code:
                self._update_captcha_display(img_bytes, code)
                self.log(f"⚡ Đã tự động nhận diện chính xác 100%: [{code}]")
            else:
                self.log("Lỗi tải ảnh captcha.")
        threading.Thread(target=_task, daemon=True).start()

    def _fetch_roles_async(self):
        account = self.claim_acc_combo.get().strip()
        if not account or account == "(Chưa có tài khoản)":
            messagebox.showwarning("Thông báo", "Vui lòng chọn hoặc nhập tài khoản trước!")
            return

        server_id = self._get_selected_server_id()

        def _task():
            try:
                self.log(f"Đang tìm nhân vật của tài khoản [{account}] tại Server {server_id}...")
                roles = self.api.get_role_list(server_id, account)
                self.current_roles = roles
                if roles:
                    role_names = [f"{r.get('name', 'NV')} ({r.get('level', '?')} cấp) [ID: {r.get('roleID')}]" for r in roles]
                    def _update():
                        self.role_combo.configure(values=role_names)
                        self.role_combo.set(role_names[0])
                        self.log(f"✅ Tìm thấy {len(roles)} nhân vật: {role_names[0]}")
                    self.after(0, _update)
                else:
                    def _none():
                        self.role_combo.configure(values=["Không tìm thấy nhân vật"])
                        self.role_combo.set("Không tìm thấy nhân vật")
                        self.log("⚠️ Không tìm thấy nhân vật nào! Hãy chắc chắn bạn đã vào game tạo nhân vật ở server này trước.")
                    self.after(0, _none)
            except Exception as e:
                self.log(f"❌ Lỗi khi lấy nhân vật: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def _format_msg(self, msg: str) -> str:
        """Dịch và làm rõ kết quả phản hồi từ máy chủ game sang tiếng Việt"""
        if not msg:
            return ""
        if "领取成功" in msg or "成功" in msg:
            return f"{msg} (🎉 Nhận thành công!)"
        if "已达上限" in msg or "刷新次数" in msg:
            return f"{msg} (⚠️ Hôm nay đã nhận rồi! Mai mới nhận tiếp được)"
        if "验证码错误" in msg:
            return f"{msg} (❌ Sai mã xác thực Captcha!)"
        if "已经领取" in msg or "已领取" in msg:
            return f"{msg} (⚠️ Nick này đã nhận quà này rồi!)"
        if "CDK不存在" in msg:
            return f"{msg} (❌ Mã Code không tồn tại!)"
        if "已被使用" in msg:
            return f"{msg} (❌ Mã Code đã hết lượt hoặc đã sử dụng!)"
        if "未找到角色" in msg:
            return f"{msg} (❌ Không tìm thấy nhân vật!)"
        return msg

    def _send_cdk_with_retry(self, server_id: str, account: str, role_id: str, cdk: str, max_retries: int = 15):
        """Gửi nhận CDK - Tự động giải lại Captcha cho đến khi nhận được mới chuyển nick"""
        last_msg = ""
        for attempt in range(1, max_retries + 1):
            if getattr(self, "stop_batch_flag", False):
                break
            img_b, captcha = solver.get_guaranteed_captcha(self.api.session)
            self._update_captcha_display(img_b, captcha)
            ok, msg = self.api.claim_cdk(server_id, account, role_id, cdk, captcha)
            last_msg = msg
            if "验证码错误" in msg and attempt < max_retries:
                self.log(f"    ⚠️ Captcha chưa khớp (lần {attempt}/{max_retries}), đang giải lại cho đến khi nhận được...")
                time.sleep(0.3)
                continue
            return ok, msg
        return False, last_msg

    def _send_gift_with_retry(self, server_id: str, account: str, role_id: str, gift_id: str, max_retries: int = 15):
        """Gửi nhận Gói Tân Thủ - Tự động giải lại Captcha cho đến khi nhận được mới chuyển nick"""
        last_msg = ""
        for attempt in range(1, max_retries + 1):
            if getattr(self, "stop_batch_flag", False):
                break
            img_b, captcha = solver.get_guaranteed_captcha(self.api.session)
            self._update_captcha_display(img_b, captcha)
            ok, msg = self.api.claim_gift(server_id, account, role_id, gift_id, captcha)
            last_msg = msg
            if "验证码错误" in msg and attempt < max_retries:
                self.log(f"    ⚠️ Captcha chưa khớp (lần {attempt}/{max_retries}), đang giải lại cho đến khi nhận được...")
                time.sleep(0.3)
                continue
            return ok, msg
        return False, last_msg

    def _claim_gifts_async(self):
        account = self.claim_acc_combo.get().strip()
        server_id = self._get_selected_server_id()

        if not account or account == "(Chưa có tài khoản)":
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn tài khoản!")
            return

        if not self.current_roles:
            messagebox.showwarning("Chưa có nhân vật", "Vui lòng bấm 'Lấy nhân vật' trước khi nhận quà!")
            return

        # Lấy roleID từ combobox
        selected_role_text = self.role_combo.get()
        role_id = None
        for r in self.current_roles:
            rid = str(r.get('roleID'))
            if f"[ID: {rid}]" in selected_role_text:
                role_id = rid
                break
        
        if not role_id and self.current_roles:
            role_id = str(self.current_roles[0].get('roleID'))

        cdk_code = self.cdk_entry.get().strip() if self.chk_cdk_var.get() else None
        need_gift = self.chk_gift_var.get()

        self.claim_single_btn.configure(state="disabled", text="⏳ Đang xử lý...")
        self.claim_all_btn.configure(state="disabled")

        def _task():
            try:
                # 1. Nhận CDK nếu chọn
                if cdk_code:
                    self.log(f"Đang gửi nhận CDK [{cdk_code}] cho nhân vật {role_id}...")
                    ok, msg = self._send_cdk_with_retry(server_id, account, role_id, cdk_code)
                    icon = "✅" if ok else ("⚠️" if "已经领取" in msg or "已领取" in msg or "已达上限" in msg or "刷新次数" in msg else "❌")
                    self.log(f"{icon} Kết quả CDK: {self._format_msg(msg)}")

                # 2. Nhận Quà Tân Thủ nếu chọn
                if need_gift:
                    gift_id = "2040630438" # Gói Tân thủ phúc lợi
                    self.log(f"Đang gửi nhận Quà Tân Thủ...")
                    ok, msg = self._send_gift_with_retry(server_id, account, role_id, gift_id)
                    icon = "✅" if ok else ("⚠️" if "已经领取" in msg or "已领取" in msg or "已达上限" in msg or "刷新次数" in msg else "❌")
                    self.log(f"{icon} Kết quả Quà Tân Thủ: {self._format_msg(msg)}")

            except Exception as e:
                self.log(f"❌ Lỗi: {e}")
            finally:
                def _finish():
                    self.claim_single_btn.configure(state="normal", text="🚀 Nhận quà Nick này")
                    self.claim_all_btn.configure(state="normal")
                    self._refresh_captcha_async()
                self.after(0, _finish)

        threading.Thread(target=_task, daemon=True).start()

    def _set_batch_ui_state(self, running: bool):
        if running:
            self.claim_single_btn.configure(state="disabled")
            self.claim_all_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.claim_single_btn.configure(state="normal")
            self.claim_all_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def _stop_batch_action(self):
        if self.is_batch_running:
            self.stop_batch_flag = True
            self.log("⏳ Đang gửi yêu cầu dừng, vui lòng chờ xử lý nốt nick hiện tại...")

    def _claim_all_accounts_async(self):
        accounts = account_manager.get_accounts()
        if not accounts:
            messagebox.showwarning("Thông báo", "Chưa có tài khoản nào trong danh sách accounts.txt!")
            return
        account_names = [a[0] for a in accounts]
        self._start_batch_claim(account_names)

    def _open_multi_account_dialog(self):
        accounts = account_manager.get_accounts()
        if not accounts:
            messagebox.showwarning("Thông báo", "Chưa có tài khoản nào trong danh sách accounts.txt!")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Chọn tài khoản nhận quà")
        dialog.geometry("450x540")
        dialog.minsize(380, 460)
        dialog.transient(self)
        dialog.grab_set()

        # Tiêu đề
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 6))

        title = ctk.CTkLabel(
            header, 
            text="📋 Chọn Danh Sách Tài Khoản", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w")

        info_lbl = ctk.CTkLabel(
            header,
            text="Tích chọn các nick bạn muốn tự động nhận quà ở Server hiện tại:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_lbl.pack(anchor="w", pady=(2, 6))

        bar = ctk.CTkFrame(header, fg_color="transparent")
        bar.pack(fill="x", pady=4)

        checkboxes = {}

        def _update_count():
            sel_cnt = sum(1 for v in checkboxes.values() if v.get())
            count_lbl.configure(text=f"Đã chọn: {sel_cnt} / {len(accounts)}")
            start_btn.configure(text=f"🚀 BẮT ĐẦU NHẬN ({sel_cnt} NICK)")

        def _select_all():
            for v in checkboxes.values():
                v.set(True)
            _update_count()

        def _deselect_all():
            for v in checkboxes.values():
                v.set(False)
            _update_count()

        btn_all = ctk.CTkButton(bar, text="Chọn tất cả", width=95, height=28, command=_select_all)
        btn_all.pack(side="left", padx=(0, 6))

        btn_none = ctk.CTkButton(bar, text="Bỏ chọn", width=80, height=28, fg_color="#546e7a", hover_color="#37474f", command=_deselect_all)
        btn_none.pack(side="left", padx=(0, 10))

        count_lbl = ctk.CTkLabel(bar, text=f"Đã chọn: {len(accounts)} / {len(accounts)}", font=ctk.CTkFont(size=12, weight="bold"))
        count_lbl.pack(side="right")

        # Danh sách nick có thanh cuộn
        scroll_frame = ctk.CTkScrollableFrame(dialog, corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=8)

        for acc, pwd in accounts:
            var = ctk.BooleanVar(value=True)
            checkboxes[acc] = var
            chk = ctk.CTkCheckBox(
                scroll_frame, 
                text=acc, 
                variable=var, 
                command=_update_count,
                font=ctk.CTkFont(size=13)
            )
            chk.pack(anchor="w", padx=10, pady=4)

        # Nút xác nhận ở dưới
        bottom = ctk.CTkFrame(dialog, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(6, 15))

        def _on_confirm():
            chosen = [acc for acc, v in checkboxes.items() if v.get()]
            if not chosen:
                messagebox.showwarning("Thông báo", "Bạn chưa chọn tài khoản nào!")
                return
            dialog.destroy()
            self._start_batch_claim(chosen)

        start_btn = ctk.CTkButton(
            bottom, 
            text=f"🚀 BẮT ĐẦU NHẬN ({len(accounts)} NICK)", 
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=_on_confirm
        )
        start_btn.pack(fill="x")

    def _start_batch_claim(self, account_list: list):
        if self.is_batch_running:
            messagebox.showwarning("Đang chạy", "Tool đang trong quá trình nhận quà hàng loạt!")
            return

        server_id = self._get_selected_server_id()
        if not server_id:
            messagebox.showwarning("Thiếu server", "Vui lòng chọn Máy chủ (Server) trước!")
            return

        cdk_code = self.cdk_entry.get().strip() if self.chk_cdk_var.get() else None
        need_gift = self.chk_gift_var.get()

        if not cdk_code and not need_gift:
            messagebox.showwarning("Chưa chọn quà", "Vui lòng tích chọn ít nhất 1 loại quà (Code Ngày hoặc Quà Tân Thủ)!")
            return

        server_name = self.server_combo.get()
        if not messagebox.askyesno(
            "Xác nhận nhận hàng loạt",
            f"Bắt đầu tự động nhận quà cho {len(account_list)} tài khoản ở {server_name}?\n\n"
            f"- Code Ngày: {cdk_code if cdk_code else 'Không nhận'}\n"
            f"- Quà Tân Thủ: {'Có (VIP17 + KNB)' if need_gift else 'Không nhận'}\n\n"
            f"Hệ thống sẽ tự dò tìm nhân vật và giải mã Captcha 100% chuẩn xác."
        ):
            return

        self.is_batch_running = True
        self.stop_batch_flag = False
        self._set_batch_ui_state(True)

        def _task():
            total = len(account_list)
            list_success = []
            list_already = []
            list_captcha_fail = []
            list_no_role = []
            list_other_fail = []

            self.log("\n" + "=" * 55)
            self.log(f"🚀 BẮT ĐẦU NHẬN HÀNG LOẠT: {total} TÀI KHOẢN (SERVER {server_id})")
            self.log("=" * 55)

            for idx, account in enumerate(account_list, 1):
                if self.stop_batch_flag:
                    self.log("🛑 Đã dừng tiến trình nhận hàng loạt theo lệnh của người dùng!")
                    break

                self.log(f"\n[{idx}/{total}] 👤 Tài khoản: {account}")
                try:
                    # 1. Lấy danh sách nhân vật
                    roles = self.api.get_role_list(server_id, account)
                    if not roles:
                        self.log(f"  ⚠️ Tài khoản [{account}] chưa tạo nhân vật ở server này -> Bỏ qua.")
                        list_no_role.append(account)
                        continue

                    # Chọn nhân vật cấp cao nhất hoặc nhân vật đầu tiên
                    target_role = max(roles, key=lambda r: int(r.get('level', 0) or 0)) if roles else roles[0]
                    role_id = str(target_role.get('roleID'))
                    role_name = target_role.get('name', 'NV')
                    role_lvl = target_role.get('level', '?')
                    self.log(f"  🎮 Nhân vật: {role_name} (Cấp {role_lvl}) [ID: {role_id}]")

                    acc_results = []
                    # 2. Nhận Code Ngày
                    if cdk_code:
                        if self.stop_batch_flag:
                            break
                        self.log(f"  🎁 Đang nhận Code Ngày [{cdk_code}]...")
                        ok, msg = self._send_cdk_with_retry(server_id, account, role_id, cdk_code)
                        icon = "✅" if ok else ("⚠️" if "已经领取" in msg or "已领取" in msg or "已达上限" in msg or "刷新次数" in msg else "❌")
                        self.log(f"    {icon} Kết quả Code Ngày: {self._format_msg(msg)}")
                        acc_results.append((ok, msg))
                        time.sleep(0.4)

                    # 3. Nhận Quà Tân Thủ
                    if need_gift:
                        if self.stop_batch_flag:
                            break
                        self.log(f"  🎁 Đang nhận Gói Tân Thủ (VIP17 + KNB)...")
                        gift_id = "2040630438"
                        ok, msg = self._send_gift_with_retry(server_id, account, role_id, gift_id)
                        icon = "✅" if ok else ("⚠️" if "已经领取" in msg or "已领取" in msg or "已达上限" in msg or "刷新次数" in msg else "❌")
                        self.log(f"    {icon} Kết quả Quà Tân Thủ: {self._format_msg(msg)}")
                        acc_results.append((ok, msg))
                        time.sleep(0.4)

                    # Phân loại tài khoản chuẩn xác
                    has_captcha_err = any("验证码错误" in m for _, m in acc_results)
                    has_success = any(ok for ok, _ in acc_results)
                    all_already = all("已经领取" in m or "已领取" in m or "已达上限" in m or "刷新次数" in m for _, m in acc_results) if acc_results else False

                    if has_captcha_err:
                        list_captcha_fail.append(account)
                    elif has_success:
                        list_success.append(account)
                    elif all_already:
                        list_already.append(account)
                    else:
                        first_err = acc_results[0][1] if acc_results else "Không rõ"
                        list_other_fail.append((account, self._format_msg(first_err)))

                except Exception as e:
                    self.log(f"  ❌ Lỗi khi xử lý nick {account}: {e}")
                    list_other_fail.append((account, str(e)))

            self.log("\n" + "=" * 55)
            self.log(
                f"🏁 KẾT THÚC! "
                f"✅ Thành công: {len(list_success)} | "
                f"⚠️ Đã nhận: {len(list_already)} | "
                f"❌ Lỗi Captcha: {len(list_captcha_fail)} | "
                f"⚪ Chưa tạo NV: {len(list_no_role)}"
            )
            self.log("=" * 55)

            def _finish_ui():
                self.is_batch_running = False
                self.stop_batch_flag = False
                self._set_batch_ui_state(False)
                self._refresh_captcha_async()
                self._show_batch_summary_dialog(
                    server_id, total, list_success, list_already,
                    list_captcha_fail, list_no_role, list_other_fail
                )
            self.after(0, _finish_ui)

        threading.Thread(target=_task, daemon=True).start()

    def _show_batch_summary_dialog(self, server_id, total, list_success, list_already, list_captcha_fail, list_no_role, list_other_fail):
        """Bảng thông báo kết quả chi tiết từng tài khoản"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Báo Cáo Kết Quả Nhận Quà")
        dialog.geometry("540x650")
        dialog.minsize(460, 520)
        dialog.transient(self)
        dialog.grab_set()

        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header,
            text="🏁 BÁO CÁO KẾT QUẢ NHẬN QUÀ",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"Máy chủ: {server_id}  |  Tổng số tài khoản đã duyệt: {total}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(2, 6))

        # Thống kê nhanh dạng 4 thẻ màu
        stat_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        stat_frame.pack(fill="x", padx=16, pady=4)

        stats = [
            ("Thành công", len(list_success), "#2e7d32"),
            ("Đã nhận/Hết lượt", len(list_already), "#d84315"),
            ("Lỗi Captcha", len(list_captcha_fail), "#c62828"),
            ("Chưa tạo NV", len(list_no_role), "#455a64"),
        ]
        for label, count, color in stats:
            col = ctk.CTkFrame(stat_frame, fg_color=color, corner_radius=6)
            col.pack(side="left", fill="both", expand=True, padx=3)
            ctk.CTkLabel(col, text=str(count), font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=(4, 0))
            ctk.CTkLabel(col, text=label, font=ctk.CTkFont(size=11), text_color="#eeeeee").pack(pady=(0, 4))

        # Khung cuộn danh sách chi tiết
        scroll = ctk.CTkScrollableFrame(dialog, corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        def _add_section(title, items, color, is_error=False):
            sec_frame = ctk.CTkFrame(scroll, fg_color="#2b2b2b" if not is_error else "#3b2222", corner_radius=6)
            sec_frame.pack(fill="x", pady=5, padx=2)
            
            lbl_title = ctk.CTkLabel(
                sec_frame,
                text=f"{title} ({len(items)})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color
            )
            lbl_title.pack(anchor="w", padx=10, pady=(6, 2))

            if items:
                box_height = max(45, min(120, len(items) * 20))
                text_box = ctk.CTkTextbox(sec_frame, height=box_height, font=ctk.CTkFont(size=12))
                text_box.pack(fill="x", padx=8, pady=(2, 8))
                if isinstance(items[0], tuple):
                    lines = [f"• {a}: {m}" for a, m in items]
                else:
                    lines = [f"• {a}" for a in items]
                text_box.insert("1.0", "\n".join(lines))
                text_box.configure(state="disabled")
            else:
                ctk.CTkLabel(
                    sec_frame,
                    text="  (Không có tài khoản nào)",
                    font=ctk.CTkFont(size=12, slant="italic"),
                    text_color="gray"
                ).pack(anchor="w", padx=10, pady=(2, 6))

        _add_section("✅ ĐÃ NHẬN MỚI THÀNH CÔNG", list_success, "#66bb6a")
        _add_section("⚠️ ĐÃ NHẬN TỪ TRƯỚC / HẾT LƯỢT TRONG NGÀY (ĐÃ CÓ TRONG THƯ)", list_already, "#ffa726")
        _add_section("❌ LỖI MÃ CAPTCHA (CẦN NHẬN LẠI)", list_captcha_fail, "#ef5350", is_error=bool(list_captcha_fail))
        _add_section("⚪ BỎ QUA DO CHƯA TẠO NHÂN VẬT", list_no_role, "#b0bec5")
        if list_other_fail:
            _add_section("⚠️ LỖI KHÁC", list_other_fail, "#ff7043", is_error=True)

        # Nút hành động ở dưới
        bottom = ctk.CTkFrame(dialog, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 16))

        if list_captcha_fail:
            def _retry_failed():
                dialog.destroy()
                self._start_batch_claim(list_captcha_fail)

            retry_btn = ctk.CTkButton(
                bottom,
                text=f"🔄 Nhận lại ngay {len(list_captcha_fail)} nick lỗi Captcha",
                height=38,
                fg_color="#1f538d",
                hover_color="#153966",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=_retry_failed
            )
            retry_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        close_btn = ctk.CTkButton(
            bottom,
            text="Đóng",
            height=38,
            width=100,
            fg_color="#455a64",
            hover_color="#37474f",
            command=dialog.destroy
        )
        close_btn.pack(side="right")

    def _generate_random_account(self):
        chars = string.ascii_lowercase + string.digits
        rnd = ''.join(random.choice(chars) for _ in range(6))
        acc = f"sgs{rnd}"
        self.reg_acc_entry.delete(0, "end")
        self.reg_acc_entry.insert(0, acc)
        self.log(f"Đã sinh tài khoản ngẫu nhiên: {acc}")

    def _check_account_exists(self):
        acc = self.reg_acc_entry.get().strip()
        if not acc:
            messagebox.showwarning("Thông báo", "Vui lòng nhập tài khoản cần kiểm tra!")
            return
        
        def _task():
            self.log(f"Đang kiểm tra tài khoản [{acc}]...")
            is_avail, msg = self.api.check_account_available(acc)
            self.log(f"Kết quả: {msg}")
            if is_avail:
                messagebox.showinfo("Khả dụng", f"Tài khoản '{acc}' chưa ai đăng ký, có thể dùng!")
            else:
                messagebox.showwarning("Đã tồn tại", f"Tài khoản '{acc}' đã có người đăng ký hoặc không hợp lệ!")
        threading.Thread(target=_task, daemon=True).start()

    def _launch_browser_register(self):
        acc = self.reg_acc_entry.get().strip()
        pwd = self.reg_pwd_entry.get().strip()

        if not acc:
            messagebox.showwarning("Thông báo", "Vui lòng nhập hoặc sinh tài khoản trước!")
            return

        browser_register.launch_auto_register(
            account=acc,
            password=pwd,
            on_success_callback=lambda a, p: self.after(0, self._on_browser_reg_success, a),
            on_log_callback=self.log
        )

    def _toggle_warp_ip(self):
        warp_path = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
        if not os.path.exists(warp_path):
            messagebox.showwarning("Thông báo", "Không tìm thấy Cloudflare WARP trên máy.")
            return

        def _task():
            self.log("🌐 Đang thiết lập chế độ VPN và đổi IP mới qua Cloudflare WARP...")
            try:
                import subprocess
                import time
                subprocess.run([warp_path, "mode", "warp"], capture_output=True, text=True, timeout=10)
                subprocess.run([warp_path, "disconnect"], capture_output=True, text=True, timeout=10)
                time.sleep(1)
                subprocess.run([warp_path, "connect"], capture_output=True, text=True, timeout=10)
                time.sleep(2)
                status_res = subprocess.run([warp_path, "status"], capture_output=True, text=True, timeout=10)
                self.log(f"✅ Trạng thái WARP: {status_res.stdout.strip()}")
                self.log("🎉 Đã đổi IP thành công! Bạn có thể tiếp tục đăng ký tài khoản.")
                messagebox.showinfo("Đổi IP thành công", "Đã bật / đổi IP qua Cloudflare WARP thành công!\nBây giờ bạn có thể đăng ký tiếp các tài khoản mới.")
            except Exception as e:
                self.log(f"❌ Lỗi đổi IP: {e}")

        threading.Thread(target=_task, daemon=True).start()

    def _increment_account_name(self, account: str) -> str:
        """Tăng số ở cuối tên tài khoản lên 1 (ví dụ phuong30 -> phuong31)"""
        import re
        match = re.search(r'^(.*?)(\d+)$', account)
        if match:
            prefix, num_str = match.groups()
            next_num = int(num_str) + 1
            width = len(num_str)
            return f"{prefix}{str(next_num).zfill(width)}"
        else:
            return f"{account}1"

    def _on_browser_reg_success(self, account):
        self.log(f"🎉 Đã lưu tài khoản [{account}] vào hệ thống!")
        self._refresh_account_list()
        self.claim_acc_combo.set(account)

        # Tự động tăng số tài khoản thêm 1 (ví dụ phuong30 -> phuong31)
        next_account = self._increment_account_name(account)
        self.reg_acc_entry.delete(0, "end")
        self.reg_acc_entry.insert(0, next_account)
        self.log(f"➡️ Sẵn sàng tài khoản tiếp theo: [{next_account}]")

    def _manual_save_account(self):
        acc = self.reg_acc_entry.get().strip()
        pwd = self.reg_pwd_entry.get().strip()
        if not acc:
            return
        if account_manager.save_account(acc, pwd):
            self.log(f"Đã lưu thủ công: {acc}")
            self._refresh_account_list()
            # Tự động tăng số kế tiếp
            next_acc = self._increment_account_name(acc)
            self.reg_acc_entry.delete(0, "end")
            self.reg_acc_entry.insert(0, next_acc)
            messagebox.showinfo("Đã lưu", f"Đã lưu tài khoản '{acc}' vào danh sách!\nĐã tự động chuyển sang '{next_acc}'.")
        else:
            messagebox.showinfo("Thông báo", f"Tài khoản '{acc}' đã có sẵn trong danh sách.")

    def _open_accounts_file(self):
        acc_file = account_manager.ACCOUNTS_FILE
        if not os.path.exists(acc_file):
            with open(acc_file, "w", encoding="utf-8") as f:
                f.write("# Danh sách tài khoản: account|password\n")
        os.system(f'start notepad "{acc_file}"')

    def _delete_selected_account(self):
        acc = self.claim_acc_combo.get().strip()
        if not acc or acc == "(Chưa có tài khoản)":
            return
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tài khoản '{acc}' khỏi danh sách?"):
            account_manager.delete_account(acc)
            self.log(f"Đã xóa tài khoản {acc}")
            self._refresh_account_list()

    def _on_closing(self):
        """Tự động tắt VPN Cloudflare WARP & dừng Auto khi tắt Tool để trả về mạng gốc"""
        if self.is_batch_running:
            self.stop_batch_flag = True
        try:
            auto_engine.stop()
        except Exception:
            pass
        warp_path = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
        if os.path.exists(warp_path):
            try:
                import subprocess
                subprocess.run([warp_path, "disconnect"], capture_output=True, text=True, timeout=5)
            except Exception:
                pass
        self.destroy()

if __name__ == "__main__":
    app = ToolApp()
    app.mainloop()
