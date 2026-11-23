"""
API Client cho trang web Danh Tướng 3Q Private Server: newsgs.zce8.com
"""

import requests
import urllib3
import re
from typing import Dict, List, Optional, Tuple

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://newsgs.zce8.com"
PROXY_ID = "10343"

class GameWebAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"{BASE_URL}/?p={PROXY_ID}"
        })
        self.csrf_token = None

    def get_server_list(self) -> List[Dict[str, str]]:
        """Lấy danh sách server từ API"""
        url = f"{BASE_URL}/api/game/server-list"
        try:
            r = self.session.get(url, timeout=25)
            data = r.json()
            if data.get("state") and "data" in data:
                return data["data"]
        except Exception as e:
            print(f"Lỗi tải danh sách server: {e}")
        return []

    def check_account_available(self, account: str) -> Tuple[bool, str]:
        """Kiểm tra tài khoản đã tồn tại hay chưa"""
        url = f"{BASE_URL}/api/game/register-is"
        try:
            r = self.session.get(url, params={"account": account}, timeout=25)
            data = r.json()
            # state = True nghĩa là tài khoản chưa được đăng ký
            return data.get("state", False), data.get("data", "")
        except Exception as e:
            return False, f"Lỗi kết nối: {e}"

    def get_role_list(self, server_id: str, account: str) -> List[Dict]:
        """Lấy danh sách nhân vật đã tạo trong server"""
        url = f"{BASE_URL}/api/game/role-list"
        try:
            r = self.session.post(url, data={"serverID": server_id, "account": account}, timeout=25)
            data = r.json()
            if data.get("state") and "data" in data:
                raw = data["data"]
                if isinstance(raw, dict):
                    return list(raw.values())
                elif isinstance(raw, list):
                    return raw
        except Exception as e:
            print(f"Lỗi lấy danh sách nhân vật: {e}")
        return []

    def get_captcha_image(self) -> Tuple[Optional[bytes], str]:
        """Tải ảnh Captcha cho CDK/Gift và trả về (bytes_image, captcha_url)"""
        try:
            # Truy cập trang cdk trước để thiết lập session cookie
            self.session.get(f"{BASE_URL}/index/cdk", timeout=25)
            
            # Lấy link captcha mới
            refresh_url = f"{BASE_URL}/index/captcha?refresh=1"
            r = self.session.get(refresh_url, timeout=25)
            data = r.json()
            img_rel_url = data.get("url", "")
            
            if img_rel_url:
                img_url = f"{BASE_URL}{img_rel_url}"
                img_resp = self.session.get(img_url, timeout=25)
                if img_resp.status_code == 200:
                    return img_resp.content, img_rel_url
        except Exception as e:
            print(f"Lỗi tải captcha: {e}")
        return None, ""

    def claim_cdk(self, server_id: str, account: str, role_id: str, cdk: str, captcha: str) -> Tuple[bool, str]:
        """Gửi yêu cầu nhận CDK"""
        url = f"{BASE_URL}/api/game/cdk"
        payload = {
            "serverID": server_id,
            "account": account,
            "role": role_id,
            "cdk": cdk,
            "captcha": captcha
        }
        try:
            r = self.session.post(url, data=payload, timeout=25)
            res = r.json()
            msg = res.get("data", "")
            # Nếu message báo thành công hoặc state == 100
            success = "成功" in msg or "领取成功" in msg
            return success, msg
        except Exception as e:
            return False, f"Lỗi gửi nhận CDK: {e}"

    def claim_gift(self, server_id: str, account: str, role_id: str, gift_id: str, captcha: str) -> Tuple[bool, str]:
        """Gửi yêu cầu nhận Gói Tân Thủ Phúc Lợi"""
        url = f"{BASE_URL}/api/game/gift"
        payload = {
            "serverID": server_id,
            "account": account,
            "role": role_id,
            "giftID": gift_id,
            "captcha": captcha
        }
        try:
            r = self.session.post(url, data=payload, timeout=25)
            res = r.json()
            msg = res.get("data", "")
            success = "成功" in msg or "领取成功" in msg
            return success, msg
        except Exception as e:
            return False, f"Lỗi gửi nhận Quà: {e}"
