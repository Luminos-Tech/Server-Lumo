# server-CSDL
# USE CASE HỆ THỐNG QUẢN LÝ NÚT BẤM VÀ DỮ LIỆU NGƯỜI DÙNG

## 1. Tên hệ thống
Hệ thống quản lý thiết bị nút bấm, người dùng và dữ liệu sự kiện.

---

## 2. Mục tiêu hệ thống
Hệ thống cho phép:
- Quản lý thông tin người dùng
- Quản lý thiết bị/nút bấm
- Ghi nhận trạng thái hoặc sự kiện khi nút được nhấn
- Lưu trữ dữ liệu liên quan để phục vụ theo dõi, thống kê và xử lý

---

## 3. Tác nhân (Actors)

### 3.1. User
Người sử dụng hệ thống, có thể:
- Đăng nhập
- Xem thông tin thiết bị
- Xem lịch sử nút bấm
- Quản lý dữ liệu cá nhân

### 3.2. Admin
Quản trị viên hệ thống, có thể:
- Quản lý user
- Quản lý thiết bị/nút bấm
- Xem toàn bộ dữ liệu
- Xóa/sửa dữ liệu khi cần

### 3.3. Thiết bị ESP32 / Nút bấm
Thiết bị vật lý gửi dữ liệu trạng thái hoặc sự kiện nhấn nút lên hệ thống.

### 3.4. Database
Nơi lưu trữ:
- Thông tin user
- Thông tin nút bấm / thiết bị
- Dữ liệu sự kiện
- Nhật ký hệ thống

---

## 4. Danh sách Use Case

### UC01 - Đăng ký tài khoản
**Mô tả:** User tạo tài khoản mới để sử dụng hệ thống.

**Tác nhân chính:** User  
**Tiền điều kiện:** Chưa có tài khoản  
**Hậu điều kiện:** Tài khoản mới được lưu vào cơ sở dữ liệu

**Luồng chính:**
1. User nhập tên, email, mật khẩu
2. Hệ thống kiểm tra dữ liệu hợp lệ
3. Hệ thống tạo tài khoản mới
4. Dữ liệu user được lưu vào database

**Luồng thay thế:**
- Nếu email đã tồn tại, hệ thống báo lỗi
- Nếu thiếu thông tin, hệ thống yêu cầu nhập lại

---

### UC02 - Đăng nhập
**Mô tả:** User đăng nhập vào hệ thống.

**Tác nhân chính:** User  
**Tiền điều kiện:** Đã có tài khoản  
**Hậu điều kiện:** User truy cập được hệ thống

**Luồng chính:**
1. User nhập email và mật khẩu
2. Hệ thống kiểm tra thông tin
3. Nếu đúng, hệ thống cho đăng nhập
4. Ghi log thời gian đăng nhập

**Luồng thay thế:**
- Sai email/mật khẩu -> báo lỗi

---

### UC03 - Thêm thiết bị / nút bấm
**Mô tả:** Admin thêm một thiết bị nút bấm mới vào hệ thống.

**Tác nhân chính:** Admin  
**Tiền điều kiện:** Admin đã đăng nhập  
**Hậu điều kiện:** Thiết bị mới được lưu vào database

**Luồng chính:**
1. Admin nhập mã thiết bị, tên thiết bị, vị trí, trạng thái
2. Hệ thống kiểm tra mã thiết bị có trùng không
3. Hệ thống lưu thiết bị vào database

**Luồng thay thế:**
- Nếu mã thiết bị đã tồn tại -> báo lỗi

---

### UC04 - Gán thiết bị cho user
**Mô tả:** Hệ thống liên kết thiết bị nút bấm với một user.

**Tác nhân chính:** Admin  
**Tiền điều kiện:** Đã có user và đã có thiết bị  
**Hậu điều kiện:** Quan hệ user - thiết bị được lưu

**Luồng chính:**
1. Admin chọn user
2. Admin chọn thiết bị
3. Hệ thống lưu thông tin gán thiết bị

---

### UC05 - Gửi dữ liệu nhấn nút
**Mô tả:** Khi nút bấm được nhấn, thiết bị gửi dữ liệu về server.

**Tác nhân chính:** Thiết bị ESP32 / Nút bấm  
**Tiền điều kiện:** Thiết bị đã đăng ký trong hệ thống  
**Hậu điều kiện:** Sự kiện nhấn nút được lưu vào database

**Luồng chính:**
1. Người dùng nhấn nút trên thiết bị
2. Thiết bị đọc trạng thái nút
3. Thiết bị gửi dữ liệu gồm:
   - Mã thiết bị
   - Thời gian nhấn
   - Trạng thái nút
   - Giá trị dữ liệu nếu có
4. Server nhận dữ liệu
5. Hệ thống lưu vào bảng lịch sử sự kiện

**Luồng thay thế:**
- Nếu thiết bị không hợp lệ -> từ chối lưu
- Nếu mất mạng -> thiết bị lưu tạm và gửi lại sau

---

### UC06 - Xem lịch sử nút bấm
**Mô tả:** User hoặc Admin xem danh sách các lần nhấn nút.

**Tác nhân chính:** User, Admin  
**Tiền điều kiện:** Đã đăng nhập  
**Hậu điều kiện:** Hiển thị dữ liệu lịch sử

**Luồng chính:**
1. Người dùng chọn chức năng xem lịch sử
2. Hệ thống truy vấn database
3. Hiển thị:
   - Mã thiết bị
   - User liên quan
   - Thời gian nhấn
   - Loại sự kiện
   - Trạng thái

---

### UC07 - Xem thông tin user
**Mô tả:** Xem thông tin cá nhân hoặc danh sách user.

**Tác nhân chính:** User, Admin  
**Tiền điều kiện:** Đã đăng nhập  
**Hậu điều kiện:** Thông tin user được hiển thị

**Luồng chính:**
1. User/Admin chọn mục thông tin user
2. Hệ thống truy vấn database
3. Hiển thị thông tin

---

### UC08 - Cập nhật thông tin user
**Mô tả:** User hoặc Admin chỉnh sửa dữ liệu người dùng.

**Tác nhân chính:** User, Admin  
**Tiền điều kiện:** Đã đăng nhập  
**Hậu điều kiện:** Dữ liệu mới được cập nhật

**Luồng chính:**
1. Chọn user cần sửa
2. Nhập thông tin mới
3. Hệ thống kiểm tra hợp lệ
4. Lưu cập nhật vào database

---

### UC09 - Xóa thiết bị hoặc vô hiệu hóa nút bấm
**Mô tả:** Admin xóa hoặc khóa thiết bị.

**Tác nhân chính:** Admin  
**Tiền điều kiện:** Đã có thiết bị trong hệ thống  
**Hậu điều kiện:** Thiết bị bị xóa hoặc chuyển sang trạng thái inactive

**Luồng chính:**
1. Admin chọn thiết bị
2. Chọn xóa hoặc vô hiệu hóa
3. Hệ thống cập nhật database

---

### UC10 - Thống kê dữ liệu
**Mô tả:** Admin xem thống kê số lần nhấn nút, tần suất hoạt động, user sử dụng.

**Tác nhân chính:** Admin  
**Tiền điều kiện:** Có dữ liệu trong hệ thống  
**Hậu điều kiện:** Báo cáo thống kê được hiển thị

**Luồng chính:**
1. Admin chọn khoảng thời gian
2. Hệ thống tổng hợp dữ liệu
3. Hiển thị báo cáo:
   - Số lần nhấn theo thiết bị
   - Số lần nhấn theo user
   - Thiết bị hoạt động nhiều nhất
   - Thời gian hoạt động gần nhất

---

## 5. Use Case tổng quát theo nhóm chức năng

### Nhóm quản lý user
- Đăng ký tài khoản
- Đăng nhập
- Xem thông tin user
- Cập nhật thông tin user

### Nhóm quản lý thiết bị / nút bấm
- Thêm thiết bị
- Gán thiết bị cho user
- Xóa / vô hiệu hóa thiết bị

### Nhóm quản lý dữ liệu
- Gửi dữ liệu nhấn nút
- Xem lịch sử dữ liệu
- Thống kê dữ liệu

---

## 6. Mô hình dữ liệu gợi ý

### Bảng `users`
- user_id
- full_name
- email
- password
- role
- created_at

### Bảng `devices`
- device_id
- device_name
- device_code
- location
- status
- created_at
- device_variant: standard/pro

### Bảng `user_devices`
- id
- user_id
- device_id
- assigned_at

### Bảng `button_events`
- event_id
- device_id
- user_id
- button_state
- event_type
- event_value
- created_at

### Bảng `logs_button`
- log_id
- action
- actor
- description
- created_at

---

## 7. Quan hệ giữa các đối tượng
- Một **user** có thể sở hữu nhiều **thiết bị**
- Một **thiết bị** có thể phát sinh nhiều **button_events**
- Mỗi **button_event** thuộc về một **thiết bị**
- Admin có quyền quản lý toàn bộ user, thiết bị và dữ liệu

---

## 8. Kết luận
Hệ thống này giúp quản lý đầy đủ:
- Người dùng
- Nút bấm / thiết bị
- Dữ liệu phát sinh từ thiết bị
- Lịch sử và thống kê hoạt động

