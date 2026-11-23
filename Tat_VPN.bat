@echo off
chcp 65001 >nul
echo ========================================================
echo        TẮT VPN CLOUDFLARE WARP
echo ========================================================
echo.
set "WARP_CLI=C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"

if not exist "%WARP_CLI%" (
    echo [!] Không tìm thấy Cloudflare WARP tại: %WARP_CLI%
    pause
    exit /b
)

echo Đang ngắt kết nối VPN...
"%WARP_CLI%" disconnect >nul 2>&1
timeout /t 2 >nul

echo Trạng thái hiện tại:
"%WARP_CLI%" status
echo.
echo ========================================================
echo  ĐÃ TẮT VPN! MẠNG ĐÃ TRỞ VỀ ĐỊA CHỈ IP GỐC.
echo ========================================================
echo.
pause
