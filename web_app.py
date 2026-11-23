"""
Web Application Tool Danh Tướng 3Q - newsgs.zce8.com
Chạy được trên cả máy tính (Localhost) và Cloud (Render / Railway / VPS / PythonAnywhere)
Hỗ trợ truy cập mượt mà trên Điện thoại (iOS / Android) và Trình duyệt máy tính!
"""

import os
import sys
import io
import time
import json
import base64
import threading
from typing import List, Dict, Tuple, Optional
from flask import Flask, render_template, request, jsonify, Response

from api_client import GameWebAPI
from captcha_solver import VerifiedCaptchaSolver
import account_manager

# Cấu hình đường dẫn thư mục
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "web_templates")
STATIC_DIR = os.path.join(BASE_DIR, "web_static")

os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.config["JSON_AS_ASCII"] = False

# Khởi tạo solver captcha
captcha_solver = VerifiedCaptchaSolver()

def format_game_msg(msg: str) -> str:
    """Dịch thông báo máy chủ game sang tiếng Việt thân thiện"""
    if not msg:
        return ""
    if "领取成功" in msg or "成功" in msg:
        return f"{msg} (🎉 Nhận thành công!)"
    if "已达上限" in msg or "刷新次数" in msg:
        return f"{msg} (⚠️ Hôm nay đã nhận rồi! Mai mới nhận tiếp được)"
    if "验证码错误" in msg:
        return f"{msg} (❌ Sai mã Captcha!)"
    if "已经领取" in msg or "已领取" in msg:
        return f"{msg} (⚠️ Nick này đã nhận quà này rồi!)"
    if "CDK不存在" in msg:
        return f"{msg} (❌ Mã Code không tồn tại!)"
    if "已被使用" in msg:
        return f"{msg} (❌ Mã Code đã hết lượt hoặc đã dùng!)"
    if "未找到角色" in msg:
        return f"{msg} (❌ Không tìm thấy nhân vật!)"
    return msg

# ================= QUẢN LÝ TIẾN TRÌNH NHẬN QUÀ HÀNG LOẠT =================

class BatchClaimManager:
    def __init__(self):
        self.is_running = False
        self.stop_flag = False
        self.current_idx = 0
        self.total = 0
        self.current_account = ""
        self.server_id = ""
        self.logs: List[Dict] = []
        self.stats = {"success": 0, "already": 0, "no_role": 0, "failed": 0}
        self.lock = threading.Lock()
        self.thread = None

    def add_log(self, text: str, log_type: str = "info"):
        """Thêm 1 dòng log: log_type: info, success, warning, error, header"""
        with self.lock:
            entry = {
                "time": time.strftime("%H:%M:%S"),
                "text": text,
                "type": log_type
            }
            self.logs.append(entry)
            # Giữ tối đa 500 dòng log gần nhất
            if len(self.logs) > 500:
                self.logs.pop(0)

    def get_status(self) -> Dict:
        with self.lock:
            percent = int((self.current_idx / max(1, self.total)) * 100) if self.total > 0 else 0
            return {
                "is_running": self.is_running,
                "current_idx": self.current_idx,
                "total": self.total,
                "percent": percent,
                "current_account": self.current_account,
                "server_id": self.server_id,
                "stats": dict(self.stats),
                "logs_count": len(self.logs)
            }

    def stop(self):
        with self.lock:
            if self.is_running:
                self.stop_flag = True
                self.add_log("🛑 Đang gửi yêu cầu dừng tiến trình...", "warning")

    def start_batch(self, server_id: str, accounts: List[str], cdk_code: Optional[str], need_gift: bool):
        if self.is_running:
            return False, "Tiến trình nhận quà đang chạy!"

        self.is_running = True
        self.stop_flag = False
        self.current_idx = 0
        self.total = len(accounts)
        self.server_id = server_id
        self.logs = []
        self.stats = {"success": 0, "already": 0, "no_role": 0, "failed": 0}

        def _worker():
            api = GameWebAPI()
            self.add_log("=" * 50, "header")
            self.add_log(f"🚀 BẮT ĐẦU NHẬN HÀNG LOẠT: {self.total} TÀI KHOẢN (SERVER {server_id})", "header")
            self.add_log(f"   - Code Ngày: {cdk_code if cdk_code else 'Không nhận'}", "info")
            self.add_log(f"   - Quà Tân Thủ: {'VIP17 + KNB' if need_gift else 'Không nhận'}", "info")
            self.add_log("=" * 50, "header")

            for idx, account in enumerate(accounts, 1):
                if self.stop_flag:
                    self.add_log("🛑 Đã dừng tiến trình nhận hàng loạt theo lệnh người dùng!", "warning")
                    break

                self.current_idx = idx
                self.current_account = account
                self.add_log(f"[{idx}/{self.total}] 👤 Đang xử lý: {account}", "info")

                try:
                    # 1. Lấy danh sách nhân vật
                    roles = api.get_role_list(server_id, account)
                    if not roles:
                        self.add_log(f"  ⚠️ Nick [{account}] chưa tạo nhân vật ở Server {server_id} -> Bỏ qua.", "warning")
                        self.stats["no_role"] += 1
                        time.sleep(0.15)
                        continue

                    # Chọn nhân vật cấp cao nhất hoặc nhân vật đầu tiên
                    target_role = max(roles, key=lambda r: int(r.get('level', 0) or 0)) if roles else roles[0]
                    role_id = str(target_role.get('roleID'))
                    role_name = target_role.get('name', 'NV')
                    role_lvl = target_role.get('level', '?')
                    self.add_log(f"  🎮 Nhân vật: {role_name} (Cấp {role_lvl}) [ID: {role_id}]", "info")

                    acc_results = []

                    # 2. Nhận Code Ngày
                    if cdk_code and not self.stop_flag:
                        self.add_log(f"  🎁 Đang nhận Code Ngày [{cdk_code}]...", "info")
                        ok, msg = self._send_cdk_with_retry(api, server_id, account, role_id, cdk_code)
                        fmsg = format_game_msg(msg)
                        l_type = "success" if ok else ("warning" if ("已经领取" in msg or "已达上限" in msg) else "error")
                        icon = "✅" if ok else ("⚠️" if l_type == "warning" else "❌")
                        self.add_log(f"    {icon} Code Ngày: {fmsg}", l_type)
                        acc_results.append((ok, msg))
                        time.sleep(0.3)

                    # 3. Nhận Quà Tân Thủ
                    if need_gift and not self.stop_flag:
                        self.add_log("  🎁 Đang nhận Gói Tân Thủ (VIP17 + KNB)...", "info")
                        gift_id = "2040630438"
                        ok, msg = self._send_gift_with_retry(api, server_id, account, role_id, gift_id)
                        fmsg = format_game_msg(msg)
                        l_type = "success" if ok else ("warning" if ("已经领取" in msg or "已达上限" in msg) else "error")
                        icon = "✅" if ok else ("⚠️" if l_type == "warning" else "❌")
                        self.add_log(f"    {icon} Quà Tân Thủ: {fmsg}", l_type)
                        acc_results.append((ok, msg))
                        time.sleep(0.3)

                    # Thống kê
                    has_success = any(ok for ok, _ in acc_results)
                    all_already = all("已经领取" in m or "已达上限" in m for _, m in acc_results) if acc_results else False
                    if has_success:
                        self.stats["success"] += 1
                    elif all_already:
                        self.stats["already"] += 1
                    else:
                        self.stats["failed"] += 1

                except Exception as e:
                    self.add_log(f"  ❌ Lỗi xử lý nick [{account}]: {e}", "error")
                    self.stats["failed"] += 1

            self.add_log("=" * 50, "header")
            self.add_log(f"🎉 HOÀN TẤT CHUỖI NHẬN QUÀ!", "header")
            self.add_log(f"   - Thành công: {self.stats['success']}", "success")
            self.add_log(f"   - Đã nhận trước đó: {self.stats['already']}", "warning")
            self.add_log(f"   - Chưa có nhân vật: {self.stats['no_role']}", "warning")
            self.add_log(f"   - Lỗi / Thất bại: {self.stats['failed']}", "error" if self.stats['failed'] > 0 else "info")
            self.add_log("=" * 50, "header")

            if not self.stop_flag:
                self.current_idx = self.total
                self.current_account = "Hoàn tất"
            self.is_running = False
            self.stop_flag = False

        self.thread = threading.Thread(target=_worker, daemon=True)
        self.thread.start()
        return True, "Đã khởi động tiến trình nhận quà!"

    def _send_cdk_with_retry(self, api: GameWebAPI, server_id: str, account: str, role_id: str, cdk: str, max_retries: int = 15):
        last_msg = ""
        for attempt in range(1, max_retries + 1):
            if self.stop_flag:
                break
            _, captcha = captcha_solver.get_guaranteed_captcha(api.session)
            ok, msg = api.claim_cdk(server_id, account, role_id, cdk, captcha)
            last_msg = msg
            if "验证码错误" in msg and attempt < max_retries:
                time.sleep(0.25)
                continue
            return ok, msg
        return False, last_msg

    def _send_gift_with_retry(self, api: GameWebAPI, server_id: str, account: str, role_id: str, gift_id: str, max_retries: int = 15):
        last_msg = ""
        for attempt in range(1, max_retries + 1):
            if self.stop_flag:
                break
            _, captcha = captcha_solver.get_guaranteed_captcha(api.session)
            ok, msg = api.claim_gift(server_id, account, role_id, gift_id, captcha)
            last_msg = msg
            if "验证码错误" in msg and attempt < max_retries:
                time.sleep(0.25)
                continue
            return ok, msg
        return False, last_msg

batch_manager = BatchClaimManager()

# ================= CÁC API ENDPOINTS =================

@app.route("/")
def index():
    """Giao diện chính của Web Tool"""
    return render_template("index.html")

@app.route("/api/servers")
def get_servers():
    """Lấy danh sách server game"""
    api = GameWebAPI()
    srvs = api.get_server_list()
    return jsonify({"success": True, "data": srvs})

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    """Lấy danh sách tài khoản hiện tại"""
    accs = account_manager.get_accounts()
    data = [{"account": a[0], "password": a[1]} for a in accs]
    return jsonify({"success": True, "data": data, "count": len(data)})

@app.route("/api/accounts", methods=["POST"])
def add_account():
    """Thêm 1 tài khoản mới"""
    body = request.get_json(silent=True) or {}
    acc = body.get("account", "").strip()
    pwd = body.get("password", "").strip()
    if not acc:
        return jsonify({"success": False, "message": "Vui lòng nhập tên tài khoản!"}), 400

    saved = account_manager.save_account(acc, pwd)
    if saved:
        return jsonify({"success": True, "message": f"Đã lưu tài khoản [{acc}] thành công!"})
    else:
        return jsonify({"success": False, "message": f"Tài khoản [{acc}] đã tồn tại trong danh sách!"})

@app.route("/api/accounts/bulk", methods=["POST"])
def bulk_save_accounts():
    """Lưu nhiều tài khoản từ văn bản (mỗi dòng 1 nick hoặc nick|pass)"""
    body = request.get_json(silent=True) or {}
    raw_text = body.get("text", "")
    lines = raw_text.strip().splitlines()

    new_list = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            parts = line.split("|", 1)
            new_list.append((parts[0].strip(), parts[1].strip()))
        else:
            new_list.append((line, ""))

    # Ghi đè vào file accounts.txt
    accounts_file = account_manager.ACCOUNTS_FILE
    with open(accounts_file, "w", encoding="utf-8") as f:
        for a, p in new_list:
            f.write(f"{a}|{p}\n")

    return jsonify({"success": True, "message": f"Đã cập nhật thành công {len(new_list)} tài khoản!", "count": len(new_list)})

@app.route("/api/accounts/<account>", methods=["DELETE"])
def delete_account(account):
    """Xóa 1 tài khoản"""
    deleted = account_manager.delete_account(account)
    if deleted:
        return jsonify({"success": True, "message": f"Đã xóa tài khoản [{account}]!"})
    return jsonify({"success": False, "message": "Không tìm thấy tài khoản để xóa!"}), 404

@app.route("/api/roles", methods=["POST"])
def get_roles():
    """Tra cứu nhân vật trong server"""
    body = request.get_json(silent=True) or {}
    server_id = str(body.get("server_id", "")).strip()
    account = str(body.get("account", "")).strip()

    if not server_id or not account:
        return jsonify({"success": False, "message": "Thiếu Server ID hoặc Tên tài khoản!"}), 400

    api = GameWebAPI()
    roles = api.get_role_list(server_id, account)
    return jsonify({"success": True, "data": roles, "count": len(roles)})

@app.route("/api/claim/single", methods=["POST"])
def claim_single():
    """Nhận quà cho 1 nick cụ thể"""
    body = request.get_json(silent=True) or {}
    server_id = str(body.get("server_id", "")).strip()
    account = str(body.get("account", "")).strip()
    role_id = str(body.get("role_id", "")).strip()
    cdk_code = body.get("cdk_code")
    need_gift = body.get("need_gift", False)

    if not server_id or not account:
        return jsonify({"success": False, "message": "Thiếu thông tin Server hoặc Tài khoản!"}), 400

    api = GameWebAPI()
    # Nếu chưa có role_id, tự tìm
    if not role_id:
        roles = api.get_role_list(server_id, account)
        if not roles:
            return jsonify({"success": False, "message": f"Tài khoản [{account}] chưa tạo nhân vật ở Server {server_id}!"}), 400
        target = max(roles, key=lambda r: int(r.get('level', 0) or 0)) if roles else roles[0]
        role_id = str(target.get("roleID"))

    results = []

    # 1. Nhận CDK
    if cdk_code:
        ok, msg = batch_manager._send_cdk_with_retry(api, server_id, account, role_id, cdk_code)
        results.append({
            "type": "cdk",
            "code": cdk_code,
            "success": ok,
            "raw_msg": msg,
            "msg": format_game_msg(msg)
        })

    # 2. Nhận Quà Tân Thủ
    if need_gift:
        gift_id = "2040630438"
        ok, msg = batch_manager._send_gift_with_retry(api, server_id, account, role_id, gift_id)
        results.append({
            "type": "gift",
            "success": ok,
            "raw_msg": msg,
            "msg": format_game_msg(msg)
        })

    return jsonify({"success": True, "results": results})

@app.route("/api/claim/batch", methods=["POST"])
def start_batch_claim():
    """Bắt đầu tiến trình nhận quà hàng loạt"""
    body = request.get_json(silent=True) or {}
    server_id = str(body.get("server_id", "")).strip()
    cdk_code = body.get("cdk_code")
    need_gift = body.get("need_gift", True)
    accounts = body.get("accounts", [])

    if not server_id:
        return jsonify({"success": False, "message": "Vui lòng chọn Máy chủ (Server)!"}), 400

    # Nếu không truyền accounts cụ thể -> lấy toàn bộ trong danh sách
    if not accounts:
        accounts = [a[0] for a in account_manager.get_accounts()]

    if not accounts:
        return jsonify({"success": False, "message": "Danh sách tài khoản trống!"}), 400

    if not cdk_code and not need_gift:
        return jsonify({"success": False, "message": "Vui lòng chọn ít nhất 1 loại quà (Code Ngày hoặc Quà Tân Thủ)!"}), 400

    ok, msg = batch_manager.start_batch(server_id, accounts, cdk_code, need_gift)
    return jsonify({"success": ok, "message": msg})

@app.route("/api/claim/stop", methods=["POST"])
def stop_batch_claim():
    """Dừng tiến trình nhận quà hàng loạt"""
    batch_manager.stop()
    return jsonify({"success": True, "message": "Đã gửi tín hiệu dừng!"})

@app.route("/api/claim/status")
def claim_status():
    """Lấy trạng thái và log mới nhất của tiến trình nhận quà"""
    status = batch_manager.get_status()
    # Lấy các dòng log gần nhất
    with batch_manager.lock:
        status["logs"] = batch_manager.logs[-80:]
    return jsonify({"success": True, "data": status})

@app.route("/api/check-account")
def check_account():
    """Kiểm tra tên tài khoản đã đăng ký hay chưa"""
    account = request.args.get("account", "").strip()
    if not account:
        return jsonify({"success": False, "message": "Thiếu tên tài khoản!"}), 400
    api = GameWebAPI()
    is_available, msg = api.check_account_available(account)
    return jsonify({"success": True, "is_available": is_available, "message": msg})

if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5000))
    
    # Lấy địa chỉ IP nội bộ để người dùng có thể mở bằng điện thoại cùng mạng Wifi
    hostname = socket.gethostname()
    local_ip = "127.0.0.1"
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        pass

    print("\n" + "=" * 65)
    print("🚀 TOOL WEB DANH TƯỚNG 3Q ĐANG KHỞI CHẠY!")
    print(f"👉 Máy tính mở tại: http://localhost:{port}")
    print(f"📱 Điện thoại cùng Wifi mở tại: http://{local_ip}:{port}")
    print("=" * 65 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False)
