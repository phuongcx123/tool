@echo off
chcp 65001 >nul
echo ========================================================
echo     ĐỔI IP / BẬT VPN CLOUDFLARE WARP
echo ========================================================
echo.
set "WARP_CLI=C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"

if not exist "%WARP_CLI%" (
    echo [!] Không tìm thấy Cloudflare WARP tại: %WARP_CLI%
    pause
    exit /b
)

echo [1/3] Thiết lập chế độ Full VPN Tunnel...
"%WARP_CLI%" mode warp >nul 2>&1
"%WARP_CLI%" disconnect >nul 2>&1
timeout /t 2 >nul

echo [2/3] Đang kết nối nhận IP mới...
"%WARP_CLI%" connect >nul 2>&1
timeout /t 3 >nul

echo [3/3] Trạng thái hiện tại:
"%WARP_CLI%" status
echo.
echo ========================================================
echo  ĐÃ ĐỔI IP THÀNH CÔNG! BẠN CÓ THỂ ĐĂNG KÝ TIẾP 5 NICK.
echo ========================================================
echo.
pause
