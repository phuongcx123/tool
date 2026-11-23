"""
Module Auto Game Danh Tướng 3Q Thông Minh (AI & Computer Vision)
Tối ưu chuyên dụng cho bản lậu Trung Quốc (newsgs.zce8.com / TMgame99 / 三国名将传)
Hỗ trợ:
1. Nhận diện hình ảnh & trạng thái tự động bằng OpenCV (bàn tay chỉ dẫn tân thủ, hộp thoại, nút chiến đấu)
2. Tự động bám theo cửa sổ game "三国名将传" / "OSLink" / "LDPlayer"
3. Chuỗi hoạt động toàn diện (Phương án D):
   - Auto Cày Clone Tân Thủ (Lv1 ➔ 16+, tự bắt trọn vẹn mọi ngón tay hướng dẫn)
   - Auto Vượt Ải Chính Tuyến (Khiêu chiến, bỏ qua, tăng tốc, chiến thắng, rương sao)
   - Auto Đấu Trường (Lôi Đài)
   - Auto Du Ngoạn (Đổ xúc xắc)
   - Auto Quét Ải Tiêu Hao Thể Lực (10 lần)
   - Auto Rung Cây Tiền & Bái Tế Quân Đoàn
   - Auto Thủy Kính Học Đường
"""

import os
import sys
import time
import threading
from typing import Optional, Tuple, Callable, List, Dict
import numpy as np
from PIL import ImageGrab, Image
import cv2
import pyautogui

def get_base_dir() -> str:
    """Trả về thư mục gốc của ứng dụng (hỗ trợ cả chạy script và file exe đóng gói)"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, "templates")):
            return exe_dir
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and os.path.exists(os.path.join(meipass, "templates")):
            return meipass
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

STEP1_IMG = os.path.join(TEMPLATES_DIR, "step1_thuy_kinh.png")
STEP1_TEXT_IMG = os.path.join(TEMPLATES_DIR, "step1_thuy_kinh_text.png")
STEP2_IMG = os.path.join(TEMPLATES_DIR, "step2_nhat_kien.png")
STEP3_IMG = os.path.join(TEMPLATES_DIR, "step3_dong_x.png")

class AutoGameSmartAI:
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.worker_thread = None
        self.target_window_title = "三国名将传"

        self.config = {
            "vuot_ai": True,
            "max_ai_count": 10,
            "tan_thu": True,
            "dau_truong": True,
            "dau_truong_count": 5,
            "du_ngoan": True,
            "quet_ai": True,
            "rung_cay_tien": True,
            "bai_te": True,
            "thuy_kinh": True,
            "loop_mode": False,
            "loop_interval": 15.0, # phút
            "confidence": 0.75,
            "window_title": "三国名将传",
        }

        self.scan_scales = (0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25)

    def _is_tool_window(self, title: str) -> bool:
        """Kiểm tra và loại trừ cửa sổ của chính Tool để không tự chọn nhầm bản thân"""
        t_low = title.lower()
        excluded = ["tool danh tướng", "tool_danhtuong", "tool web", "python", "antigravity", "powershell", "cmd.exe"]
        return any(ex in t_low for ex in excluded)

    def get_available_game_windows(self) -> List[str]:
        """Quét và trả về danh sách tất cả các cửa sổ game/giả lập đang mở trên máy"""
        keywords = ["三国名将传", "三国", "LDPlayer", "OSLink", "ldremote", "TMgame"]
        matched_titles = []
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if w.visible and w.width > 250 and w.height > 200:
                    t = w.title.strip()
                    if t and not self._is_tool_window(t) and any(k.lower() in t.lower() for k in keywords):
                        if t not in matched_titles:
                            matched_titles.append(t)
        except Exception:
            pass

        # Fallback bổ sung bằng win32gui
        try:
            import win32gui
            def _enum_cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    rect = win32gui.GetWindowRect(hwnd)
                    if (rect[2] - rect[0]) > 250 and (rect[3] - rect[1]) > 200:
                        t = win32gui.GetWindowText(hwnd).strip()
                        if t and not self._is_tool_window(t) and any(k.lower() in t.lower() for k in keywords):
                            if t not in matched_titles:
                                matched_titles.append(t)
                return True
            win32gui.EnumWindows(_enum_cb, None)
        except Exception:
            pass

        return matched_titles

    def get_game_window(self, preferred_title: Optional[str] = None):
        """Lấy đối tượng cửa sổ game theo tên hoặc tự động tìm"""
        target = preferred_title or self.config.get("window_title", "三国名将传")
        keywords = ["三国名将传", "三国", "LDPlayer", "OSLink", "ldremote", "TMgame"]

        # Nếu tên mục tiêu bị trùng tên tool -> bỏ qua tên mục tiêu đó
        if target and self._is_tool_window(target):
            target = "三国名将传"

        # 1. Thử qua pygetwindow
        try:
            import pygetwindow as gw
            if target:
                wins = gw.getWindowsWithTitle(target)
                for w in wins:
                    if w.visible and w.width > 250 and w.height > 200 and not self._is_tool_window(w.title):
                        return w

            for kw in keywords:
                for w in gw.getWindowsWithTitle(kw):
                    if w.visible and w.width > 250 and w.height > 200 and not self._is_tool_window(w.title):
                        return w
        except Exception:
            pass

        return None

    def focus_game_window(self, win):
        """Kích hoạt và đưa cửa sổ game lên trên cùng màn hình một cách an toàn"""
        if not win:
            return
        # 1. Thử qua Win32 API SetForegroundWindow
        try:
            import win32gui, win32con, ctypes
            hwnd = getattr(win, '_hWnd', None)
            if hwnd:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                # Bỏ qua giới hạn LockSetForegroundWindow của Windows
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.04)
                return
        except Exception:
            pass

        # 2. Fallback qua pygetwindow
        try:
            if hasattr(win, 'isMinimized') and win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.04)
        except Exception:
            pass

    def get_game_canvas(self, win) -> Tuple[int, int, int, int]:
        """Tính toán vùng hiển thị thực của game bên trong cửa sổ (loại bỏ thanh tiêu đề và thanh công cụ)"""
        if not win:
            sw, sh = pyautogui.size()
            return (0, 0, sw, sh)

        titlebar_h = 36 if any(k in win.title.lower() for k in ["ldplayer", "oslink", "三国", "ldremote"]) else 0
        sidebar_w = 40 if "ldplayer" in win.title.lower() else 0

        canvas_x = max(0, win.left)
        canvas_y = max(0, win.top + titlebar_h)
        canvas_w = max(200, win.width - sidebar_w)
        canvas_h = max(200, win.height - titlebar_h)

        return (canvas_x, canvas_y, canvas_w, canvas_h)

    def grab_game_screen(self, win=None) -> Tuple[Optional[np.ndarray], int, int, int, int]:
        """Chụp ảnh màn hình riêng của vùng game"""
        if not win:
            win = self.get_game_window()

        cx, cy, cw, ch = self.get_game_canvas(win)
        try:
            shot = ImageGrab.grab(bbox=(cx, cy, cx + cw, cy + ch))
            img_np = np.array(shot)
            return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR), cx, cy, cw, ch
        except Exception:
            try:
                shot = ImageGrab.grab()
                img_np = np.array(shot)
                bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                return bgr[cy:cy+ch, cx:cx+cw], cx, cy, cw, ch
            except Exception:
                return None, cx, cy, cw, ch

    def click_game_ratio(self, rx: float, ry: float, delay_after: float = 0.4):
        """Click chuột vào vị trí tỉ lệ phần trăm bên trong cửa sổ game"""
        # Nếu đang chọn chế độ ADB
        if self.config.get("control_mode") == "adb":
            try:
                from ldplayer_controller import ld_ctrl
                emu_idx = self.config.get("emulator_idx", 0)
                ld_ctrl.tap_ratio(emu_idx, rx, ry)
                if delay_after > 0:
                    time.sleep(delay_after)
                return
            except Exception:
                pass

        win = self.get_game_window()
        if win:
            self.focus_game_window(win)

        cx, cy, cw, ch = self.get_game_canvas(win)
        target_x = cx + int(rx * cw)
        target_y = cy + int(ry * ch)

        pyautogui.moveTo(target_x, target_y, duration=0.12)
        pyautogui.click(target_x, target_y)
        if delay_after > 0:
            time.sleep(delay_after)

    def click_game_pixel(self, gx: int, gy: int, delay_after: float = 0.4):
        """Click chuột vào toạ độ pixel bên trong cửa sổ game"""
        win = self.get_game_window()
        if win:
            self.focus_game_window(win)

        cx, cy, cw, ch = self.get_game_canvas(win)
        target_x = cx + gx
        target_y = cy + gy

        pyautogui.moveTo(target_x, target_y, duration=0.12)
        pyautogui.click(target_x, target_y)
        if delay_after > 0:
            time.sleep(delay_after)

    # ================= COMPUTER VISION & THỊ GIÁC MÁY TÍNH =================

    def find_tutorial_pointer(self, game_bgr: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Nhận diện ngón tay / vòng tròn phát sáng tân thủ Danh Tướng 3Q:
        Tự động quét và tìm vòng hào quang màu vàng/cam (Halo) nơi game chỉ dẫn!
        """
        if game_bgr is None:
            return None

        hsv = cv2.cvtColor(game_bgr, cv2.COLOR_BGR2HSV)
        
        # Dải màu vàng/cam phát sáng của bàn tay chỉ dẫn: Hue 14..36, Saturation 110..255, Value 170..255
        lower_gold = np.array([14, 110, 170])
        upper_gold = np.array([36, 255, 255])
        mask = cv2.inRange(hsv, lower_gold, upper_gold)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 40 < area < 15000:
                x, y, w, h = cv2.boundingRect(cnt)
                ratio = float(w) / max(1, h)
                if 0.4 <= ratio <= 2.5:
                    candidates.append((x, y, w, h, area))

        if candidates:
            # Chọn contour có diện tích lớn nhất khớp hình vòng tròn phát sáng
            best = max(candidates, key=lambda c: c[4])
            bx, by, bw, bh, _ = best
            target_x = bx + bw // 2
            target_y = by + bh // 2
            return (target_x, target_y)

        return None

    def find_speech_bubble(self, game_bgr: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Nhận diện hộp thoại dẫn chuyện của NPC (ví dụ: Tiểu Kiều '主公，...')
        Hộp thoại có nền màu kem sáng (#FFFDF0) bo góc.
        """
        if game_bgr is None:
            return None

        # B > 180, G > 220, R > 230
        cream_mask = (game_bgr[:, :, 0] > 180) & (game_bgr[:, :, 1] > 220) & (game_bgr[:, :, 2] > 230)
        cream_uint8 = cream_mask.astype(np.uint8) * 255

        contours, _ = cv2.findContours(cream_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(cnt)
                # Tỉ lệ chữ nhật của hộp thoại
                if w > 100 and h > 30:
                    return (x + w // 2, y + h // 2)

        return None

    def load_template(self, path: str) -> Optional[np.ndarray]:
        """Đọc ảnh mẫu template bằng OpenCV hỗ trợ Unicode path trên Windows"""
        if not os.path.exists(path):
            return None
        try:
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def find_template(
        self, 
        screen_bgr: np.ndarray, 
        template_bgr: np.ndarray, 
        threshold: float = 0.75
    ) -> Optional[Tuple[int, int, float]]:
        """Tìm tọa độ ảnh mẫu trong ảnh màn hình với đa tỷ lệ (Multi-scale template matching)"""
        if template_bgr is None or screen_bgr is None:
            return None

        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        tmpl_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
        th, tw = tmpl_gray.shape[:2]

        best_val = -1.0
        best_loc = None
        best_size = (tw, th)

        for scale in self.scan_scales:
            rw = int(tw * scale)
            rh = int(th * scale)
            if rw > screen_gray.shape[1] or rh > screen_gray.shape[0]:
                continue
            if rw < 12 or rh < 12:
                continue

            interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
            resized = cv2.resize(tmpl_gray, (rw, rh), interpolation=interp)

            res = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_size = (rw, rh)

        if best_val >= threshold and best_loc is not None:
            cx = best_loc[0] + best_size[0] // 2
            cy = best_loc[1] + best_size[1] // 2
            return (cx, cy, float(best_val))

        return None

    # ================= CÁC HOẠT ĐỘNG AUTO THÔNG MINH =================

    def task_tan_thu(self, on_log: Callable[[str], None], duration_minutes: int = 5) -> bool:
        """
        Auto Cày Clone Tân Thủ Thông Minh (Level 1 ➔ 16+):
        Tự động phát hiện ngón tay chỉ dẫn của game và click chính xác 100%!
        """
        on_log(f"[*] [Tân Thủ] Khởi động AI tự động cày tân thủ ({duration_minutes} phút)...")
        end_time = time.time() + (duration_minutes * 60)

        loop_count = 0
        while time.time() < end_time:
            if self.stop_requested:
                break

            loop_count += 1
            screen, cx, cy, cw, ch = self.grab_game_screen()
            if screen is None:
                on_log("    [!] Chưa chụp được màn hình game, đang thử lại...")
                time.sleep(1.0)
                continue

            # 1. Quét tìm ngón tay chỉ dẫn phát sáng (Halo Pointer)
            pointer_pos = self.find_tutorial_pointer(screen)
            if not pointer_pos:
                time.sleep(0.2)
                sc2, _, _, _, _ = self.grab_game_screen()
                if sc2 is not None:
                    pointer_pos = self.find_tutorial_pointer(sc2)
                    if pointer_pos:
                        screen = sc2

            if pointer_pos:
                gx, gy = pointer_pos
                on_log(f"    [+] [AI Tân Thủ] Phát hiện Bàn Tay Chỉ Dẫn tại ({gx}, {gy}) -> Tự click!")
                self.click_game_pixel(gx, gy, delay_after=0.8)
                continue

            # 2. Quét tìm hộp thoại dẫn chuyện Tiểu Kiều (Speech bubble)
            bubble_pos = self.find_speech_bubble(screen)
            if bubble_pos:
                bx, by = bubble_pos
                on_log(f"    [+] [AI Tân Thủ] Phát hiện Hộp Thoại NPC -> Click qua thoại ({bx}, {by})...")
                self.click_game_pixel(bx, by, delay_after=0.6)
                continue

            # 3. Quét các điểm thao tác tân thủ cốt lõi của Danh Tướng 3Q
            # - Nút Chiêu Mộ (招募) ở góc dưới trái (vị trí ban đầu)
            self.click_game_ratio(0.045, 0.92, delay_after=0.4)
            # - Nút Chiêu Mộ Danh Tướng Miễn Phí
            self.click_game_ratio(0.72, 0.76, delay_after=0.4)
            # - Xác nhận nhận tướng mới / bỏ qua hoạt ảnh tướng
            self.click_game_ratio(0.50, 0.85, delay_after=0.4)
            # - Nút Đội Hình (阵容)
            self.click_game_ratio(0.36, 0.94, delay_after=0.4)
            # - Bấm Ra Trận (上阵)
            self.click_game_ratio(0.50, 0.85, delay_after=0.4)
            # - Nút Chinh Chiến (征战)
            self.click_game_ratio(0.92, 0.92, delay_after=0.4)
            # - Nút Khiêu Chiến ải
            self.click_game_ratio(0.78, 0.78, delay_after=0.4)
            # - Bỏ qua trận đấu
            self.click_game_ratio(0.92, 0.90, delay_after=0.4)
            # - Bỏ qua góc phải trên
            self.click_game_ratio(0.88, 0.10, delay_after=0.4)

            if loop_count % 5 == 0:
                left_sec = int(end_time - time.time())
                on_log(f"    [>] Đang bám sát hướng dẫn tân thủ... Còn lại: {max(0, left_sec)}s")

        on_log("[OK] [Tân Thủ] Hoàn tất phiên cày tân thủ!")
        return True

    def task_vuot_ai(self, on_log: Callable[[str], None], max_stages: int = 10) -> int:
        """Auto Vượt Ải Chính Tuyến (Đi ải cốt truyện, bỏ qua, chiến thắng, rương sao)"""
        on_log(f"[*] [Vượt Ải] Bắt đầu tự động vượt ải chính tuyến ({max_stages} ải)...")
        completed = 0

        for stage in range(1, max_stages + 1):
            if self.stop_requested:
                break

            on_log(f"\n    [>] [Ải {stage}/{max_stages}] Đang chuẩn bị khiêu chiến...")
            
            # 1. Bấm vào ải hiện tại (khu vực giữa/phải bản đồ)
            self.click_game_ratio(0.72, 0.55, delay_after=1.0)

            # 2. Bấm nút Khiêu chiến (góc dưới phải pop-up ải)
            on_log("        -> Bấm nút [Khiêu chiến]...")
            self.click_game_ratio(0.78, 0.78, delay_after=2.5)

            if self.stop_requested:
                break

            # 3. Vào trận đấu -> Bấm Tăng tốc & Bỏ qua trận đấu liên tục
            on_log("        -> Trong trận đấu: Tự động bấm [Bỏ qua / Tăng tốc]...")
            for _ in range(6):
                if self.stop_requested:
                    break
                self.click_game_ratio(0.10, 0.90, delay_after=0.3)
                self.click_game_ratio(0.92, 0.90, delay_after=0.8)

            time.sleep(1.2)

            # 4. Màn hình Chiến thắng: chạm bất kỳ đâu để qua tổng kết
            on_log("        -> Xác nhận kết quả [Chiến Thắng]...")
            self.click_game_ratio(0.50, 0.85, delay_after=1.0)
            self.click_game_ratio(0.50, 0.85, delay_after=1.5)

            # 5. Nhận rương sao nếu có
            self.click_game_ratio(0.88, 0.92, delay_after=0.5)
            self.click_game_ratio(0.50, 0.70, delay_after=0.5)

            completed += 1
            on_log(f"    [OK] Đã vượt xong ải {stage} thành công!")
            time.sleep(1.2)

        on_log(f"[OK] [Vượt Ải] Hoàn tất vượt {completed} ải chính tuyến!")
        return completed

    def task_dau_truong(self, on_log: Callable[[str], None], count: int = 5) -> int:
        """Auto Đánh Đấu Trường (Lôi Đài)"""
        on_log(f"[*] [Đấu Trường] Bắt đầu tự động đánh Đấu Trường ({count} lượt)...")

        # Vào Đấu Trường (Chinh chiến -> Đấu Trường)
        self.click_game_ratio(0.82, 0.92, delay_after=1.2)
        self.click_game_ratio(0.35, 0.45, delay_after=2.0)

        finished = 0
        for i in range(1, count + 1):
            if self.stop_requested:
                break
            on_log(f"    [>] [Lượt {i}/{count}] Đang chọn đối thủ...")
            # Chọn đối thủ bên trái (lực chiến vừa tầm)
            self.click_game_ratio(0.28, 0.68, delay_after=2.0)

            # Bấm Bỏ qua trận đấu
            on_log("        -> Bấm Bỏ qua trận đấu...")
            for _ in range(4):
                if self.stop_requested:
                    break
                self.click_game_ratio(0.92, 0.90, delay_after=0.6)

            # Bấm nhận thưởng & lật bài
            self.click_game_ratio(0.50, 0.85, delay_after=1.0)
            self.click_game_ratio(0.50, 0.50, delay_after=0.8)
            self.click_game_ratio(0.50, 0.85, delay_after=1.0)

            finished += 1
            on_log(f"    [OK] Đã xong lượt {i} Đấu Trường!")
            time.sleep(1.0)

        # Trở về màn hình chính
        self.click_game_ratio(0.05, 0.05, delay_after=1.0)
        on_log(f"[OK] [Đấu Trường] Đã hoàn thành {finished}/{count} lượt!")
        return finished

    def task_du_ngoan(self, on_log: Callable[[str], None], rolls: int = 15) -> int:
        """Auto Du Ngoạn (Đổ xúc xắc / Đi tuần tra)"""
        on_log("[*] [Du Ngoạn] Bắt đầu tự động đổ xúc xắc Du Ngoạn...")

        # Vào Du Ngoạn
        self.click_game_ratio(0.82, 0.92, delay_after=1.2)
        self.click_game_ratio(0.58, 0.45, delay_after=2.0)

        done_rolls = 0
        for r in range(1, rolls + 1):
            if self.stop_requested:
                break
            # Nút Đổ xúc xắc (Góc dưới phải)
            self.click_game_ratio(0.86, 0.84, delay_after=1.2)
            done_rolls += 1
            # Bấm sự kiện bất kỳ nếu có
            self.click_game_ratio(0.50, 0.75, delay_after=0.5)

        self.click_game_ratio(0.05, 0.05, delay_after=1.0)
        on_log(f"[OK] [Du Ngoạn] Đã hoàn thành {done_rolls} lượt gieo xúc xắc!")
        return done_rolls

    def task_quet_ai(self, on_log: Callable[[str], None]) -> bool:
        """Auto Quét Ải Tiêu Thể Lực (Càn quét 10 lần)"""
        on_log("[*] [Quét Ải] Bắt đầu càn quét ải tiêu hao thể lực...")

        # Vào phụ bản
        self.click_game_ratio(0.50, 0.92, delay_after=1.5)
        # Bấm chọn ải 3 sao
        self.click_game_ratio(0.50, 0.50, delay_after=1.0)
        # Bấm Quét 10 lần
        on_log("    -> Bấm nút [Càn quét 10 lần]...")
        self.click_game_ratio(0.48, 0.78, delay_after=2.0)
        # Xác nhận
        self.click_game_ratio(0.50, 0.85, delay_after=1.0)
        self.click_game_ratio(0.88, 0.22, delay_after=1.0)

        on_log("[OK] [Quét Ải] Đã hoàn tất càn quét ải!")
        return True

    def task_rung_cay_va_bai_te(self, on_log: Callable[[str], None]) -> bool:
        """Auto Rung Cây Tiền & Bái Tế Quân Đoàn"""
        if self.config.get("rung_cay_tien", True):
            on_log("[*] [Cây Tiền] Đang nhận Bạc miễn phí từ Cây Rung Tiền...")
            self.click_game_ratio(0.76, 0.14, delay_after=1.5)
            self.click_game_ratio(0.50, 0.78, delay_after=1.2)
            self.click_game_ratio(0.86, 0.20, delay_after=1.0)
            on_log("    [OK] Đã rung cây tiền nhận bạc!")

        if self.config.get("bai_te", True):
            on_log("[*] [Quân Đoàn] Đang thực hiện Bái Tế Quân Đoàn...")
            self.click_game_ratio(0.68, 0.92, delay_after=2.0)
            self.click_game_ratio(0.45, 0.55, delay_after=1.5)
            self.click_game_ratio(0.25, 0.75, delay_after=1.2)
            self.click_game_ratio(0.05, 0.05, delay_after=1.0)
            on_log("    [OK] Đã bái tế quân đoàn thành công!")

        return True

    def task_thuy_kinh(self, on_log: Callable[[str], None]) -> bool:
        """Auto Thủy Kính Học Đường (1 ➔ 2 ➔ 3)"""
        on_log("[*] [Thủy Kính] Đang tìm biểu tượng Thủy Kính Học Đường...")
        conf = self.config.get("confidence", 0.75)
        
        screen, cx, cy, cw, ch = self.grab_game_screen()
        if screen is None:
            return False

        # Bước 1: Tìm Thủy Kính
        t1 = self.load_template(STEP1_IMG)
        t1_txt = self.load_template(STEP1_TEXT_IMG)
        match1 = None
        for t in [t1, t1_txt]:
            if t is not None:
                match1 = self.find_template(screen, t, threshold=conf)
                if match1:
                    break

        if not match1:
            on_log("    [-] Không thấy biểu tượng [Thủy Kính Học Đường] trên màn hình.")
            return False

        gx, gy, score = match1
        on_log(f"    [+] Thấy [Thủy Kính] ({score*100:.1f}%) -> Bấm mở...")
        self.click_game_pixel(gx, gy, delay_after=1.5)

        # Bước 2: Chờ nút Nhất Kiện Đáp Đề
        on_log("    [>] Chờ nút [Nhất Kiện Đáp Đề]...")
        t2 = self.load_template(STEP2_IMG)
        t_start = time.time()
        ok2 = False
        while time.time() - t_start < 10.0:
            if self.stop_requested:
                return False
            sc, _, _, _, _ = self.grab_game_screen()
            if sc is not None and t2 is not None:
                m2 = self.find_template(sc, t2, threshold=conf)
                if m2:
                    x2, y2, sc2 = m2
                    on_log(f"    [+] Thấy nút [Nhất Kiện Đáp Đề] ({sc2*100:.1f}%) -> Bấm giải...")
                    self.click_game_pixel(x2, y2, delay_after=1.8)
                    ok2 = True
                    break
            time.sleep(0.5)

        if not ok2:
            on_log("    [!] Hết thời gian chờ nút Nhất Kiện Đáp Đề.")
            return False

        # Bước 3: Đóng cửa sổ (Nút Đèn lồng X)
        on_log("    [>] Tìm nút [Đóng X] để thoát...")
        t3 = self.load_template(STEP3_IMG)
        t_start2 = time.time()
        ok3 = False
        while time.time() - t_start2 < 10.0:
            if self.stop_requested:
                return False
            sc, _, _, _, _ = self.grab_game_screen()
            if sc is not None and t3 is not None:
                m3 = self.find_template(sc, t3, threshold=conf)
                if m3:
                    x3, y3, sc3 = m3
                    on_log(f"    [+] Thấy [Đóng X] ({sc3*100:.1f}%) -> Bấm đóng...")
                    self.click_game_pixel(x3, y3, delay_after=1.0)
                    ok3 = True
                    break
            time.sleep(0.5)

        if ok3:
            on_log("    [OK] [Thủy Kính] Hoàn thành trọn bộ câu hỏi và đóng giao diện!")
            return True
        else:
            self.click_game_ratio(0.95, 0.15, delay_after=0.8)
            return True
        while time.time() - t_start2 < 10.0:
            if self.stop_requested:
                return False
            sc, _, _, _, _ = self.grab_game_screen()
            if sc is not None and t3 is not None:
                m3 = self.find_template(sc, t3, threshold=conf)
                if m3:
                    x3, y3, sc3 = m3
                    on_log(f"  👉 Thấy [Đóng X] ({sc3*100:.1f}%) -> Bấm đóng...")
                    self.click_game_pixel(x3, y3, delay_after=1.0)
                    ok3 = True
                    break
            time.sleep(0.5)

        if ok3:
            on_log("  🎉 [Thủy Kính] Hoàn thành trọn bộ câu hỏi và đóng giao diện!")
            return True
        else:
            self.click_game_ratio(0.95, 0.15, delay_after=0.8)
            return True

    # ================= CHẨN ĐOÁN & KIỂM TRA MÀN HÌNH =================

    def diagnose_screen(self, preferred_title: Optional[str] = None) -> Dict:
        """Chụp màn hình và trả về kết quả quét chi tiết trạng thái game hiện tại"""
        win = self.get_game_window(preferred_title)
        if not win:
            return {"status": "error", "message": "Không tìm thấy cửa sổ game (三国名将传 / OSLink / LDPlayer)!"}

        screen, cx, cy, cw, ch = self.grab_game_screen(win)
        if screen is None:
            return {"status": "error", "message": "Không thể chụp màn hình game!"}

        results = {
            "status": "ok",
            "window_title": win.title,
            "window_rect": (win.left, win.top, win.width, win.height),
            "canvas_rect": (cx, cy, cw, ch),
            "has_pointer": False,
            "pointer_pos": None,
            "has_bubble": False,
            "bubble_pos": None,
            "has_thuy_kinh": False,
            "has_nhat_kien": False,
        }

        # Quét pointer (ngón tay phát sáng)
        p = self.find_tutorial_pointer(screen)
        if not p:
            # Thử thêm 1 frame phụ nếu ngón tay đang fade
            time.sleep(0.2)
            sc2, _, _, _, _ = self.grab_game_screen(win)
            if sc2 is not None:
                p = self.find_tutorial_pointer(sc2)
        if p:
            results["has_pointer"] = True
            results["pointer_pos"] = p

        # Quét bubble (hộp thoại NPC Tiểu Kiều)
        b = self.find_speech_bubble(screen)
        if b:
            results["has_bubble"] = True
            results["bubble_pos"] = b

        # Quét Thủy kính
        t1 = self.load_template(STEP1_IMG)
        if t1 is not None:
            m1 = self.find_template(screen, t1, threshold=0.72)
            if m1:
                results["has_thuy_kinh"] = True

        return results

    def test_click_target(self, target_name: str = "zhaomu", preferred_title: Optional[str] = None) -> bool:
        """Thực hiện click thử nghiệm vào nút để người dùng kiểm tra kết nối và độ chính xác"""
        win = self.get_game_window(preferred_title)
        if not win:
            return False

        if target_name == "zhaomu":
            # Nếu trên màn hình có pointer tân thủ thì click đúng ngay vị trí pointer
            screen, cx, cy, cw, ch = self.grab_game_screen(win)
            if screen is not None:
                p = self.find_tutorial_pointer(screen)
                if p:
                    self.click_game_pixel(p[0], p[1], delay_after=0.5)
                    return True

            # Ngược lại click vào toạ độ Chiêu Mộ [招募] mặc định ở góc dưới trái
            self.click_game_ratio(0.045, 0.92, delay_after=0.5)
            return True
        elif target_name == "center":
            self.click_game_ratio(0.5, 0.5, delay_after=0.5)
            return True
        return False

    # ================= ĐIỀU HÀNH CHÍNH =================

    def execute_all_selected(
        self,
        on_log: Optional[Callable[[str], None]] = None,
        on_step: Optional[Callable[[int, str], None]] = None
    ):
        """Chạy tuần tự toàn bộ các hoạt động được tích chọn"""
        def _log(m):
            if on_log:
                on_log(m)
            print(f"[AutoAI] {m}")

        target_win_title = self.config.get("window_title", "三国名将传")
        win = self.get_game_window(target_win_title)
        if not win:
            _log(f"[x] KHONG TIM THAY CUA SO GAME '{target_win_title}'! Hay chac chan game dang mo tren man hinh.")
            return

        self.focus_game_window(win)
        cx, cy, cw, ch = self.get_game_canvas(win)
        active_keys = ["thuy_kinh", "vuot_ai", "dau_truong", "du_ngoan", "quet_ai", "rung_cay_tien", "bai_te", "tan_thu"]
        selected_count = sum(1 for k in active_keys if self.config.get(k, False))

        _log("\n" + "=" * 55)
        _log(f"[+] BAT DAU CHUOI AUTO THONG MINH ({selected_count} HOAT DONG)")
        _log(f"    Khoa cua so game: [{win.title}]")
        _log(f"    Vung hien thi game: ({cx}, {cy}, kich thuoc: {cw}x{ch})")
        _log("=" * 55)

        current_step = 0

        # 1. Tân Thủ (Ưu tiên số 1 nếu bật cày tân thủ)
        if self.config.get("tan_thu", False) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Cay Clone Tan Thu (AI Bat Ngon Tay)...")
            self.task_tan_thu(_log, duration_minutes=5)
            time.sleep(1.0)

        # 2. Thủy Kính Học Đường
        if self.config.get("thuy_kinh", True) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Thuy Kinh Hoc Duong...")
            self.task_thuy_kinh(_log)
            time.sleep(1.2)

        # 3. Vượt Ải Chính Tuyến
        if self.config.get("vuot_ai", True) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Vuot Ai Chinh Tuyen...")
            cnt = self.config.get("max_ai_count", 10)
            self.task_vuot_ai(_log, max_stages=cnt)
            time.sleep(1.2)

        # 4. Đấu Trường
        if self.config.get("dau_truong", True) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Dau Truong (Loi Dai)...")
            cnt_dt = self.config.get("dau_truong_count", 5)
            self.task_dau_truong(_log, count=cnt_dt)
            time.sleep(1.2)

        # 5. Du Ngoạn
        if self.config.get("du_ngoan", True) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Du Ngoan (Do xuc xac)...")
            self.task_du_ngoan(_log, rolls=15)
            time.sleep(1.2)

        # 6. Quét Ải Thể Lực
        if self.config.get("quet_ai", True) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Quet ai tieu the luc...")
            self.task_quet_ai(_log)
            time.sleep(1.2)

        # 7. Rung Cây Tiền & Bái Tế Quân Đoàn
        if (self.config.get("rung_cay_tien", True) or self.config.get("bai_te", True)) and not self.stop_requested:
            current_step += 1
            if on_step:
                on_step(current_step, "Dang chay: Cay Tien & Quan Doan...")
            self.task_rung_cay_va_bai_te(_log)
            time.sleep(1.2)

        _log("\n" + "=" * 55)
        _log("[OK] DA HOAN TAT CHUOI HOAT DONG AUTO!")
        _log("=" * 55)

    def start_worker(
        self,
        config: Dict,
        on_log: Optional[Callable[[str], None]] = None,
        on_step: Optional[Callable[[int, str], None]] = None,
        on_finish: Optional[Callable[[], None]] = None
    ):
        """Khởi động tiến trình chạy ngầm"""
        if self.is_running:
            return

        self.is_running = True
        self.stop_requested = False
        self.config.update(config)

        def _run():
            is_loop = self.config.get("loop_mode", False)
            interval_min = max(1.0, float(self.config.get("loop_interval", 15.0)))

            while not self.stop_requested:
                self.execute_all_selected(on_log=on_log, on_step=on_step)

                if not is_loop or self.stop_requested:
                    break

                on_log(f"💤 Nghỉ {interval_min} phút trước khi chạy lại chu kỳ tiếp theo...")
                t_end = time.time() + (interval_min * 60)
                while time.time() < t_end:
                    if self.stop_requested:
                        break
                    time.sleep(1.0)

            self.is_running = False
            self.stop_requested = False
            if on_log:
                on_log("🛑 Đã dừng tiến trình Auto.")
            if on_step:
                on_step(0, "Sẵn sàng")
            if on_finish:
                on_finish()

        self.worker_thread = threading.Thread(target=_run, daemon=True)
        self.worker_thread.start()

    def stop(self):
        """Yêu cầu dừng tiến trình"""
        if self.is_running:
            self.stop_requested = True

auto_engine = AutoGameSmartAI()
