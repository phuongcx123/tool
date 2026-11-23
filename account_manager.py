"""
Quản lý lưu trữ và đọc danh sách tài khoản
"""

import sys
import os
from typing import List, Tuple

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.txt")

def get_accounts() -> List[Tuple[str, str]]:
    """Trả về danh sách (account, password)"""
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    
    accounts = []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                parts = line.split("|", 1)
                accounts.append((parts[0].strip(), parts[1].strip()))
            else:
                accounts.append((line, ""))
    return accounts

def save_account(account: str, password: str = "") -> bool:
    """Lưu 1 tài khoản vào accounts.txt nếu chưa có"""
    existing = [acc[0] for acc in get_accounts()]
    if account in existing:
        return False
    
    with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{account}|{password}\n")
    return True

def delete_account(account: str) -> bool:
    """Xóa 1 tài khoản khỏi danh sách"""
    accs = get_accounts()
    new_accs = [acc for acc in accs if acc[0] != account]
    if len(new_accs) == len(accs):
        return False
    
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        for acc, pwd in new_accs:
            f.write(f"{acc}|{pwd}\n")
    return True
