# **PicQuest - Hệ thống tìm kiếm hình ảnh** 
## Đây là một hệ thống tìm kiếm hình ảnh dựa trên truy vấn bằng văn bản hoặc hình ảnh sử dụng mô hình Sentence Transformer (“clip-ViT-B-32”) để mã hóa hình ảnh và văn bản, tích hợp thêm thư viện FAISS của FacebookAI để tìm kiếm hình ảnh tương đồng hiệu quả trong không gian vector. Ngoài ra, hệ thống còn tích hợp BLIP để sinh mô tả ngắn gọn cho hình ảnh.
### Cài đặt hệ thống
git clone https://github.com/kpeach3010/HeThongTimKiemHinhAnh.git
cd HeThongTimKiemHinhAnh

#### Tạo môi trường ảo (tuỳ chọn)
python -m venv .venv
source .venv/bin/activate  # Trên macOS/Linux
#### hoặc
.venv\Scripts\activate  # Trên Windows

#### Cài đặt thư viện
pip install -r requirements.txt
