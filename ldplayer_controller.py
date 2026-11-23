"""
Module quản lý và điều khiển giả lập LDPlayer cho Tool Danh Tướng 3Q.
Hỗ trợ phát hiện LDPlayer (v4, v5, v9), lấy danh sách máy ảo,
khởi động máy ảo, chạy game Danh Tướng 3Q, và gửi thao tác ADB/Click.
"""

import os
import subprocess
import time
from typing import List, Dict, Optional, Tuple

GAME_PACKAGE = "com.sanguosha.mjz.dv"

COMMON_LD_PATHS = [
    r"D:\LDPlayer4.0\LDPlayer\ldconsole.exe",
    r"D:\LDPlayer\LDPlayer9\ldconsole.exe",
    r"D:\LDPlayer\LDPlayer4\ldconsole.exe",
    r"C:\LDPlayer\LDPlayer9\ldconsole.exe",
    r"C:\LDPlayer\LDPlayer4.0\LDPlayer\ldconsole.exe",
]

class LDPlayerController:
    def __init__(self):
        self.ldconsole_path = self._detect_ldconsole()

    def _detect_ldconsole(self) -> Optional[str]:
        """Tự động tìm kiếm file ldconsole.exe trên máy tính"""
        for p in COMMON_LD_PATHS:
            if os.path.exists(p):
                return p
        return None

    def set_custom_path(self, path: str) -> bool:
        """Đặt đường dẫn tùy chỉnh ldconsole.exe"""
        if os.path.exists(path):
            self.ldconsole_path = path
            return True
        return False

    def is_available(self) -> bool:
        return bool(self.ldconsole_path and os.path.exists(self.ldconsole_path))

    def run_ld_cmd(self, args: List[str], timeout: int = 15) -> str:
        """Chạy lệnh ldconsole.exe và trả về kết quả dạng text"""
        if not self.is_available():
            return ""
        try:
            cmd = [self.ldconsole_path] + args
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors='ignore')
            return res.stdout.strip()
        except Exception as e:
            print(f"[LDPlayer] Lỗi gọi lệnh: {e}")
            return ""

    def get_instances(self) -> List[Dict]:
        """
        Lấy danh sách tất cả các máy ảo LDPlayer trên máy.
        Định dạng trả về từ ldconsole list2:
        index,name,top_handle,bind_handle,is_in_android,pid,pid2,width,height,dpi
        """
        raw = self.run_ld_cmd(["list2"])
        instances = []
        if not raw:
            return instances

        for line in raw.splitlines():
            parts = line.strip().split(",")
            if len(parts) >= 7:
                try:
                    idx = int(parts[0])
                    name = parts[1]
                    top_hwnd = int(parts[2])
                    bind_hwnd = int(parts[3])
                    is_running = (parts[4] == "1")
                    width = int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else 1280
                    height = int(parts[8]) if len(parts) > 8 and parts[8].isdigit() else 720
                    instances.append({
                        "index": idx,
                        "name": name,
                        "top_hwnd": top_hwnd,
                        "bind_hwnd": bind_hwnd,
                        "is_running": is_running,
                        "width": width,
                        "height": height
                    })
                except Exception:
                    continue
        return instances

    def launch_emulator(self, index: int) -> bool:
        """Mở máy ảo LDPlayer theo số thứ tự (index)"""
        if not self.is_available():
            return False
        self.run_ld_cmd(["launch", "--index", str(index)])
        return True

    def is_emulator_running(self, index: int) -> bool:
        """Kiểm tra máy ảo có đang chạy hay không"""
        status = self.run_ld_cmd(["isrunning", "--index", str(index)])
        return "running" in status.lower()

    def launch_game(self, index: int) -> bool:
        """Mở game Danh Tướng 3Q trong máy ảo"""
        if not self.is_available():
            return False
        self.run_ld_cmd(["runapp", "--index", str(index), "--packagename", GAME_PACKAGE])
        return True

    def close_game(self, index: int) -> bool:
        """Tắt game Danh Tướng 3Q trong máy ảo"""
        if not self.is_available():
            return False
        self.run_ld_cmd(["killapp", "--index", str(index), "--packagename", GAME_PACKAGE])
        return True

    def tap(self, index: int, x: int, y: int) -> bool:
        """Chạm vào toạ độ (x, y) trong máy ảo qua ADB"""
        res = self.run_ld_cmd(["adb", "--index", str(index), "--command", f"shell input tap {x} {y}"])
        return True

    def tap_ratio(self, index: int, rx: float, ry: float, base_w: int = 1280, base_h: int = 720) -> bool:
        """Chạm theo tỷ lệ phần trăm màn hình (rx: 0.0 -> 1.0, ry: 0.0 -> 1.0)"""
        x = int(rx * base_w)
        y = int(ry * base_h)
        return self.tap(index, x, y)

    def swipe(self, index: int, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Vuốt màn hình từ (x1, y1) đến (x2, y2)"""
        self.run_ld_cmd(["adb", "--index", str(index), "--command", f"shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"])
        return True

    def press_back(self, index: int) -> bool:
        """Bấm phím Back (Trở về) trong Android"""
        self.run_ld_cmd(["adb", "--index", str(index), "--command", "shell input keyevent 4"])
        return True

    def press_home(self, index: int) -> bool:
        """Bấm phím Home trong Android"""
        self.run_ld_cmd(["adb", "--index", str(index), "--command", "shell input keyevent 3"])
        return True

ld_ctrl = LDPlayerController()
