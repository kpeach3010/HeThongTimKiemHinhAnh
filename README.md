# **PicQuest - Hệ thống tìm kiếm hình ảnh** 
## Giới thiệu
Đây là một hệ thống tìm kiếm hình ảnh bằng văn bản hoặc hình ảnh sử dụng mô hình Sentence Transformer (“clip-ViT-B-32”) để mã hóa hình ảnh và văn bản, tích hợp thêm thư viện FAISS của FacebookAI để tìm kiếm hình ảnh tương đồng hiệu quả trong không gian vector. Ngoài ra, hệ thống còn tích hợp BLIP để sinh mô tả ngắn gọn cho hình ảnh.

## Tính năng của hệ thống
- Tìm kiếm bằng mô tả đa ngôn ngữ.
- Tìm kiếm bằng hình ảnh.
- Sinh mô tả cho ảnh người dùng tải lên hệ thống.
- Lưu trữ hình ảnh.
- Quản lý người dùng.
- Phân quyền tài khoản.

## Công nghệ sử dụng
- Frontend: HTML, CSS, JavaScript.
- Backend: Python, SQLite.

## Tập dữ liệu ảnh 
Flickr Image dataset: 31,783 ảnh
https://www.kaggle.com/datasets/hsankesara/flickr-image-dataset

## Cài đặt hệ thống
```bash
python -m venv .venv
source .venv/bin/activate        # Trên macOS/Linux
.venv\Scripts\activate         # Trên Windows

# Cài thư viện
pip install -r requirements.txt

# Chạy migrations
python manage.py migrate

# Chạy server
python manage.py runserver
```

---
## Ghi chủ
Cần tải tập dữ liệu ảnh trong đường link trên và sửa đổi đường dẫn trong file backend. 
