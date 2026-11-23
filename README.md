# Tool Hỗ Trợ Danh Tướng 3Q (newsgs.zce8.com)

Tool chuyên dụng tự động đăng ký, quản lý tài khoản và tự động nhận Giftcode / Code ngày / Quà tân thủ cho game Danh Tướng 3Q server lậu (`https://newsgs.zce8.com/?p=10343`).

---

## 🚀 Cách khởi động Tool:
- **Cách 1:** Nhấp đúp chuột vào file `Chay_Tool.bat` trong thư mục `D:\tooldt3q`.
- **Cách 2:** Mở Terminal / PowerShell gõ:
  ```powershell
  python gui.py
  ```

---

## 🌟 Các Tính Năng Nổi Bật:

1. **Lọc Server Cực Nhanh Theo Số:**
   - Chỉ cần gõ số server vào ô **"Số SV"** (ví dụ `52`), danh sách sẽ tự lọc ngay lập tức sang `52区-52服`.

2. **Tự Động Giải Captcha 100% Chính Xác:**
   - Tool tích hợp giải thuật toán xác thực Hash Yii2 Captcha kết hợp AI OCR.
   - Hoàn toàn tự động vượt captcha khi nhận Code ngày (`sgs2026`) & Quà tân thủ, **không cần gõ tay**.

3. **Hỗ Trợ Đăng Ký Tài Khoản Nhanh:**
   - Sinh ngẫu nhiên tài khoản, kiểm tra trùng lặp trên server.
   - Mở Chrome tự động điền form đăng ký, bạn chỉ cần kéo mảnh ghép 1 giây là xong.
   - Tự động lưu tài khoản vào `accounts.txt`.

4. **Quản Lý Tài Khoản Tiện Lợi:**
   - Lưu trữ danh sách tài khoản theo định dạng `account|password`.
   - Xem nhanh, mở Notepad chỉnh sửa trực tiếp, hoặc xóa tài khoản chỉ với 1 click.

5. **Nhận Quà Hàng Loạt Siêu Tốc (Cực Tiện):**
   - **Nhận toàn bộ danh sách 1 chạm:** Bấm `⚡ TỰ ĐỘNG NHẬN TẤT CẢ NICK`, tool sẽ tự động duyệt qua tất cả tài khoản trong danh sách `accounts.txt`, tự tìm nhân vật và tự giải captcha nhận Code ngày + Quà tân thủ.
   - **Tùy chọn danh sách nick cần nhận:** Bấm nút `📋 Chọn nhiều nick...` để mở cửa sổ tích chọn những tài khoản bạn muốn nhận theo ý thích.
   - **Nút dừng khẩn cấp:** Nút `🛑 Dừng` giúp bạn chủ động dừng nhận hàng loạt bất kỳ lúc nào.

6. **Tự Động Quản Lý VPN / Đổi IP (Vượt giới hạn 5 nick/ngày):**
   - Tích hợp sẵn tính năng đổi IP bằng Cloudflare WARP khi web báo lỗi 5 tài khoản/ngày.
   - **Tự động ngắt VPN khi tắt Tool**: Khi bạn đóng cửa sổ Tool, VPN sẽ tự động ngắt kết nối để trả máy tính về mạng gốc bình thường.
   - Có thêm file [Tat_VPN.bat](file:///d:/tooldt3q/Tat_VPN.bat) và [Doi_IP_WARP.bat](file:///d:/tooldt3q/Doi_IP_WARP.bat) để bạn chủ động bật/tắt bên ngoài.

7. **🎮 Auto Cày Game Toàn Diện (Phương Án D - Giả Lập LDPlayer):**
   - **Tích hợp sẵn danh mục hoạt động đa năng (chọn theo ý muốn):**
     1. ⚔️ **Auto Vượt Ải Chính Tuyến:** Tự động khiêu chiến, tự bấm bỏ qua/tăng tốc trận đấu, tự xác nhận chiến thắng, tự động lặp lại vượt ải liên tục.
     2. 🥊 **Auto Đấu Trường (Lôi Đài):** Tự động chọn đối thủ vừa tầm, khiêu chiến, bỏ qua và nhận quà lật bài (tùy chỉnh số lượt).
     3. 🎲 **Auto Du Ngoạn:** Tự động gieo xúc xắc / đi tuần tra nhận bạc, ngọc bích và tài nguyên.
     4. 👶 **Auto Cày Clone Tân Thủ (Level 1 ➔ 16+):** Tự động click bỏ qua đối thoại cốt truyện, đánh các ải đầu mở khóa nút Bỏ Qua và nhận thưởng thăng cấp.
     5. ⚡ **Auto Quét Ải Thể Lực:** Tự động càn quét 10 lần các ải 3 sao để tiêu hao thể lực hàng ngày.
     6. 🌳 **Auto Cây Tiền & Bái Tế:** Nhận Bạc miễn phí từ Cây Rung Tiền và cống hiến Quân Đoàn.
     7. 📖 **Auto Thủy Kính Học Đường:** Tự nhận diện và giải trọn bộ câu hỏi nhận thưởng.
   - **Hỗ trợ điều khiển qua ADB:** Chạy ngầm trong máy ảo LDPlayer, không chiếm chuột máy tính.
   - **Hỗ trợ 2 chế độ:** Chạy 1 vòng (xong là dừng) hoặc Treo máy lặp lại mỗi X phút.

---

## 📖 Hướng Dẫn Sử Dụng Chi Tiết:

### 1. Đăng ký tài khoản mới (Tab "👤 Đăng Ký Tài Khoản"):
1. Bấm nút **"🚀 MỞ CHROME TẠO NICK LIÊN HOÀN (SIÊU TỐC)"**:
   - Trình duyệt Chrome sẽ tự động mở lên và điền sẵn nick đầu tiên (ví dụ `phuongg11`).
   - Bạn chỉ cần **kéo thanh trượt 1 giây** là tạo xong 1 nick.
2. **Cơ chế Liên Hoàn (Siêu Nhanh):**
   - Bạn **không cần đóng Chrome hay quay lại Tool**!
   - Ngay khi trượt xong, Tool tự động lưu nick và tự điền nick tiếp theo (`phuongg12`), tự làm mới thanh trượt.
   - Bạn chỉ việc kéo trượt tiếp: *Trượt -> Xong -> Trượt -> Xong* (Tạo 10 nick chỉ mất khoảng 20 giây!).
3. **Tự động đổi IP thông minh:**
   - Khi tạo đủ 5 nick và web báo giới hạn IP, Tool sẽ tự động kết nối lại Cloudflare WARP trong 2 giây, tải lại trang và tiếp tục cho bạn trượt tiếp mà không cần làm gì thủ công!
4. Khi tạo đủ số nick bạn muốn, chỉ việc đóng cửa sổ Chrome lại.

### 2. Vào game tạo nhân vật:
- Mở giả lập LDPlayer, đăng nhập tài khoản vừa tạo.
- Chọn Server muốn chơi và vào game tạo tên nhân vật.

### 3. Nhận Code Ngày & Phúc Lợi (Tab "🎁 Nhận Code Ngày & Phúc Lợi"):
1. Nhập số server vào ô **"Số SV"** (ví dụ `52`).
2. Tích chọn các phần quà muốn nhận:
   - **Nhận Code Ngày:** Mã `sgs2026` (Code nhận 30 Mảnh Cửu Tiêu, 50k KNB, 1 vạn Ngọc Bích).
   - **Nhận Gói Tân Thủ:** Quý tộc 17, 666,666 KNB, 588,888 Ngọc Bích, 16 Rương tướng Kim, 300 Chiêu Hiền Bảng...
3. Lựa chọn chế độ nhận:
   - **Cách 1 - Nhận tất cả:** Bấm nút to màu xanh lá **"⚡ TỰ ĐỘNG NHẬN TẤT CẢ NICK"**, tool sẽ tự động chạy qua toàn bộ tài khoản trong danh sách.
   - **Cách 2 - Chọn lọc nhiều nick:** Bấm **"📋 Chọn nhiều nick..."** để tích chọn những tài khoản bạn muốn rồi bấm bắt đầu nhận.
   - **Cách 3 - Nhận 1 nick:** Chọn tài khoản trong danh sách thả xuống $\rightarrow$ Bấm **"🔍 Lấy nhân vật"** $\rightarrow$ Bấm **"🚀 Nhận quà Nick này"**.
4. Quà sẽ lập tức được gửi thẳng vào Hộp Thư trong game của từng nhân vật!

### 4. Auto Cày Game Toàn Diện (Tab "🎮 Auto Cày Game (LDPlayer / Bản Lậu)"):
1. Mở Tool $\rightarrow$ Mặc định Tool tự động mở sẵn tab **"🎮 Auto Cày Game (LDPlayer)"**.
2. **Khóa Cửa Sổ Game:**
   - Tại mục **"🎯 Cửa sổ Game"**, Tool tự động phát hiện cửa sổ game **"三国名将传"** (hoặc `LDPlayer` / `OSLink`).
   - Bấm nút **"📸 Soi Màn Hình / Test AI"**: Tool sẽ chụp màn hình và báo ngay lập tức:
     * Đã khóa được cửa sổ game hay chưa.
     * AI có phát hiện ngón tay chỉ dẫn vàng (`👉 Bàn tay chỉ dẫn tân thủ`) và hộp thoại NPC (`💬 Hộp thoại Tiểu Kiều`) hay không.
   - Bấm nút **"🎯 Test Click Chiêu Mộ"**: Tool sẽ di chuyển chuột thật vào đúng nút **Chiêu Mộ [招募]** trong game và click thử để bạn tận mắt nhìn thấy chuột bấm chuẩn xác 100%!
3. **Phương Thức Điều Khiển:**
   - **🖱️ Chuột Thật (PyAutoGUI - Khuyên dùng):** Hoạt động hoàn hảo 100% với game bản lậu Trung Quốc, OSLink từ xa, và mọi giả lập LDPlayer!
   - **🔌 Lệnh ngầm ADB:** Chỉ bật khi bạn chạy giả lập LDPlayer gốc trực tiếp trên máy và muốn chạy ngầm không chiếm chuột.
4. **Tích Chọn Các Hoạt Động Cần Chạy:**
   - *👶 Auto Cày Clone Tân Thủ (Lv1 ➔ 16+, skip thoại):* AI tự động bám theo mọi ngón tay hướng dẫn, bỏ qua đối thoại, chiêu mộ tướng, lên trận và đánh các ải đầu tiên.
   - *⚔️ Auto Vượt Ải Chính Tuyến:* Tự động chọn ải, bấm khiêu chiến, tăng tốc, bỏ qua trận đấu, nhận thưởng sao.
   - *🥊 Auto Đấu Trường (Lôi Đài):* Tự động chọn đối thủ yếu, khiêu chiến, lật bài nhận thưởng.
   - *🎲 Auto Du Ngoạn:* Đổ xúc xắc đi dạo, tự động giải quyết các sự kiện kỳ ngộ.
   - *⚡ Auto Quét Ải Tiêu Thể Lực (10 lần).*
   - *🌳 Auto Rung Cây Tiền & 🛡️ Bái Tế Quân Đoàn.*
   - *📖 Auto Thủy Kính Học Đường:* Nhận diện câu hỏi và tự động bấm Nhất Kiện Đáp Đề.
5. **Chế Độ Chạy:**
   - **Chạy 1 vòng:** Hoàn thành các mục đã chọn rồi dừng.
   - **Treo máy lặp lại:** Cứ mỗi X phút (ví dụ 15 phút) tự động lặp lại một vòng.
6. Bấm **"🚀 BẮT ĐẦU AUTO"**: Tool sẽ đưa cửa sổ game lên trên và tự động thao tác trọn gói!
7. Bấm **"🛑 DỪNG AUTO"** bất kỳ lúc nào nếu muốn ngắt tiến trình.
