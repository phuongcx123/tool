"""
Hỗ trợ mở trình duyệt và tự động điền form đăng ký theo chế độ Liên Hoàn (Siêu Tốc)
"""

import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import account_manager

def increment_account_name(account: str) -> str:
    """Tăng số ở cuối tên tài khoản lên 1 (ví dụ phuong10 -> phuong11)"""
    import re
    match = re.search(r'^(.*?)(\d+)$', account)
    if match:
        prefix, num_str = match.groups()
        next_num = int(num_str) + 1
        width = len(num_str)
        return f"{prefix}{str(next_num).zfill(width)}"
    else:
        return f"{account}1"

def launch_auto_register(account: str = "", password: str = "", on_success_callback=None, on_log_callback=None, initial_account: str = ""):
    """
    Mở Chrome ở chế độ LIÊN HOÀN:
    Giữ nguyên cửa sổ Chrome, mỗi khi người dùng kéo trượt:
    - Tool TỰ ĐỘNG BẤM ĐĂNG KÝ ngay khi vừa trượt xong (không cần người dùng phải bấm nút Đăng ký!)
    - Tự lưu nick vào accounts.txt
    - Chờ 1.5s để người dùng nhìn thấy thông báo thành công
    - Tự động điền nick tiếp theo và reset thanh trượt
    - Tự động đổi IP nếu gặp lỗi 5 nick/IP
    Người dùng chỉ việc kéo thanh trượt liên tục!
    """
    def _run():
        def log(msg):
            if on_log_callback:
                on_log_callback(msg)
            print(f"[Register] {msg}")

        current_account = account or initial_account
        driver = None

        try:
            log(f"🚀 Đang mở Chrome (Chế độ tạo nick liên hoàn)...")
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=options)
            target_url = "https://newsgs.zce8.com/?p=10343"
            driver.get(target_url)

            # Chờ trang tải và click mở modal đăng ký
            wait = WebDriverWait(driver, 15)
            log("Đang mở form đăng ký...")
            
            try:
                reg_btn = wait.until(EC.element_to_be_clickable((By.ID, "openRegisterBtn")))
                driver.execute_script("arguments[0].click();", reg_btn)
            except Exception:
                driver.execute_script("if(window.jQuery) { $('#registerModal').modal('show'); }")

            time.sleep(1)

            # Điền tài khoản đầu tiên
            acc_input = wait.until(EC.presence_of_element_located((By.ID, "registerAccount")))
            acc_input.clear()
            acc_input.send_keys(current_account)

            pwd_input = driver.find_element(By.ID, "registerPassword")
            pwd_input.clear()
            pwd_input.send_keys(password)

            confirm_pwd = driver.find_element(By.ID, "registerConfirmPassword")
            confirm_pwd.clear()
            confirm_pwd.send_keys(password)

            # Xóa sạch thông báo cũ trong model-1 nếu có
            driver.execute_script("$('#model-1 .modal-body').text('');")

            log(f"👉 Sẵn sàng tài khoản: [{current_account}]")
            log("🎯 Bạn chỉ cần KÉO THANH TRƯỢT GHÉP ẢNH (Tool sẽ TỰ ĐỘNG BẤM ĐĂNG KÝ ngay khi trượt xong)!")

            created_count = 0

            # Vòng lặp liên hoàn
            while True:
                time.sleep(0.4)

                # Kiểm tra xem người dùng đã đóng Chrome chưa
                try:
                    _ = driver.current_url
                except Exception:
                    log("Trình duyệt Chrome đã đóng.")
                    break

                try:
                    # 1. TỰ ĐỘNG BẤM ĐĂNG KÝ ngay khi người dùng vừa kéo trượt xong
                    # Khi người dùng trượt đúng, window.captchaVerified sẽ là true
                    driver.execute_script("""
                        if (window.captchaVerified && window.captchaToken && !window.registerLock) {
                            if (typeof window.submitRegister === 'function') {
                                window.submitRegister();
                            } else {
                                $('#registerSubmitBtn').click();
                            }
                        }
                    """)

                    # 2. Kiểm tra popup thông báo CHỈ KHI NÓ ĐANG HIỂN THỊ TRÊN MÀN HÌNH
                    is_visible = driver.execute_script("""
                        return $('#model-1').hasClass('show') || $('#model-1').is(':visible');
                    """)

                    if is_visible:
                        modal_text = driver.execute_script("return $('#model-1 .modal-body').text();") or ""
                        modal_text = modal_text.strip()

                        if modal_text:
                            # A. Đăng ký thành công
                            if "成功" in modal_text or "thành công" in modal_text.lower():
                                created_count += 1
                                log(f"🎉 [{created_count}] ĐĂNG KÝ THÀNH CÔNG: [{current_account}]!")
                                
                                account_manager.save_account(current_account, password)
                                if on_success_callback:
                                    on_success_callback(current_account, password)

                                # Chờ 1.5 giây để người dùng nhìn thấy thông báo thành công
                                time.sleep(1.5)

                                next_acc = increment_account_name(current_account)
                                log(f"➡️ Tự động chuẩn bị nick tiếp theo: [{next_acc}]")

                                driver.execute_script("""
                                    $('#model-1').modal('hide');
                                    $('#model-1 .modal-body').text('');
                                    $('#registerModal').modal('show');
                                    $('#registerAccount').val(arguments[0]);
                                    $('#registerPassword').val(arguments[1]);
                                    $('#registerConfirmPassword').val(arguments[1]);
                                    if (typeof resetCaptchaState === 'function') {
                                        resetCaptchaState();
                                    } else if (window.captchaManager) {
                                        window.captchaManager.getCaptcha();
                                        $('#captcha_badge').hide();
                                        window.captchaVerified = false;
                                        window.captchaToken = null;
                                    }
                                """, next_acc, password)

                                current_account = next_acc
                                log(f"👉 Mời bạn kéo thanh trượt tiếp cho: [{current_account}]")
                                time.sleep(1.2)
                                continue

                            # B. Tài khoản đã tồn tại (bị trùng)
                            elif "已存在" in modal_text or "已被注册" in modal_text or "tồn tại" in modal_text.lower():
                                log(f"⚠️ Tài khoản [{current_account}] đã có người đăng ký trước! Tự động chuyển nick kế tiếp...")
                                time.sleep(1.0)
                                next_acc = increment_account_name(current_account)
                                driver.execute_script("""
                                    $('#model-1').modal('hide');
                                    $('#model-1 .modal-body').text('');
                                    $('#registerModal').modal('show');
                                    $('#registerAccount').val(arguments[0]);
                                    $('#registerPassword').val(arguments[1]);
                                    $('#registerConfirmPassword').val(arguments[1]);
                                """, next_acc, password)
                                current_account = next_acc
                                time.sleep(1.0)
                                continue

                            # C. Giới hạn 5 nick / IP
                            elif "24小时" in modal_text or "同IP" in modal_text or "5 个" in modal_text:
                                log(f"⚠️ Phát hiện giới hạn 5 nick/IP trên web!")
                                warp_path = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
                                if os.path.exists(warp_path):
                                    log("🌐 Đang tự động đổi IP mới qua Cloudflare WARP...")
                                    import subprocess
                                    subprocess.run([warp_path, "mode", "warp"], capture_output=True, text=True, timeout=10)
                                    subprocess.run([warp_path, "disconnect"], capture_output=True, text=True, timeout=10)
                                    time.sleep(1)
                                    subprocess.run([warp_path, "connect"], capture_output=True, text=True, timeout=10)
                                    time.sleep(2)
                                    log("✅ Đã đổi IP mới! Đang tải lại trang...")
                                    driver.get(target_url)
                                    time.sleep(2)
                                    driver.execute_script("if(window.jQuery) { $('#registerModal').modal('show'); }")
                                    time.sleep(1)
                                    driver.execute_script("""
                                        $('#registerAccount').val(arguments[0]);
                                        $('#registerPassword').val(arguments[1]);
                                        $('#registerConfirmPassword').val(arguments[1]);
                                    """, current_account, password)
                                    log(f"👉 Tiếp tục kéo thanh trượt cho nick: [{current_account}]")
                                    time.sleep(2)
                                else:
                                    log("⚠️ Vui lòng bấm nút 'Đổi IP' trên Tool để tiếp tục tạo tài khoản.")
                                    time.sleep(3)

                except Exception:
                    pass

            if created_count > 0:
                log(f"🏁 Đã kết thúc phiên! Tổng cộng tạo thành công: {created_count} tài khoản.")

        except Exception as e:
            log(f"Lỗi phiên trình duyệt: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
