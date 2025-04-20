
from sentence_transformers import SentenceTransformer
import faiss
from deep_translator import GoogleTranslator
import os
from PIL import Image
import numpy as np
import io
from django.core.files.storage import default_storage
from transformers import BlipProcessor, BlipForConditionalGeneration
import shutil
from django.conf import settings


# Cấu hình thư mục chứa ảnh
IMAGE_FOLDER = "C:/NienLuanCSN/flickr30k_images/flickr30k_images"
if not os.path.exists(IMAGE_FOLDER):
    raise FileNotFoundError(f"Không tìm thấy thư mục ảnh: {IMAGE_FOLDER}")

# Khởi tạo Google Translate
translator = GoogleTranslator(source='auto', target='en')

# Load mô hình CLIP và FAISS index
model = SentenceTransformer("clip-ViT-B-32") #encoder hình ảnh và văn bản
index_path = "C:/NienLuanCSN/index.faiss"
image_files_path = "C:/NienLuanCSN/image_files(1).txt"

#Kiểm tra file index và danh sách các ảnh
if not os.path.exists(index_path):
    raise FileNotFoundError(f"Không tìm thấy FAISS index: {index_path}")

if not os.path.exists(image_files_path):
    raise FileNotFoundError(f"Không tìm thấy danh sách ảnh: {image_files_path}")

# Load FAISS index và danh sách ảnh
index = faiss.read_index(index_path)
with open(image_files_path, "r") as f:
    image_files = [line.strip() for line in f]


def get_image(image_name: str):
    image_path = os.path.join(IMAGE_FOLDER, image_name)

    if not os.path.exists(image_path):
        raise "Image not found"

    return image_path


def filter_deleted_images(image_paths):
    """Loại bỏ những ảnh đã bị đánh dấu là [DELETED]"""
    if not os.path.exists(image_files_path):
        return image_paths  # Trả về nguyên danh sách nếu file không tồn tại

    with open(image_files_path, "r") as f:
        image_files = [line.strip() for line in f.readlines()]

    return [path for path in image_paths if path in image_files and path != "[DELETED]"]

def count_deleted_images(file_path=image_files_path):
    count = 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if "[DELETED]" in line:
                    count += 1
    except FileNotFoundError:
        print(f"File {file_path} không tồn tại.")
        return 0
    return count

def search_image(query_embedding, top_k):
    """Tìm kiếm ảnh trong FAISS và loại bỏ ảnh đã xóa"""
    if not os.path.exists(index_path):
        return []

    # Đọc FAISS index
    index = faiss.read_index(index_path)

    # Chuyển query về kiểu float32
    query_embedding = query_embedding.astype("float32").reshape(1, -1)
    cnt_delete = count_deleted_images()
    distances, indices = index.search(query_embedding, top_k + cnt_delete)  # Lấy dư để lọc
    print("top_k:", top_k)
    for i in range(len(indices[0])):
        print(f"Khoảng cách với ảnh {indices[0][i]} : {distances[0][i]}")
    # Đọc danh sách ảnh từ file
    if not os.path.exists(image_files_path):
        return []

    with open(image_files_path, "r") as f:
        image_files = [line.strip() for line in f.readlines()]

    # Debug: In danh sách chỉ mục trả về từ FAISS
    print("Chỉ mục từ FAISS:", indices[0])

    # Tạo danh sách ánh xạ từ FAISS index -> ảnh gốc
    index_to_image = {i: img for i, img in enumerate(image_files)}

    # Lọc chỉ mục hợp lệ
    retrieved_images = []
    count = 0  # Đếm số ảnh hợp lệ đã lấy

    for i in indices[0]:
        image_path = index_to_image.get(i, "[DELETED]")  # Lấy ảnh từ chỉ mục
        if image_path != "[DELETED]":
            retrieved_images.append(os.path.basename(image_path))
            count += 1
        if count >= top_k:  # Dừng khi đủ top_k ảnh hợp lệ
            break
    return retrieved_images

def search_by_image(image, top_k):
    try:
        image_query = Image.open(io.BytesIO(image.read())).convert("RGB")
        query_embedding = model.encode(image_query)
        print("Text Embedding Sample:", query_embedding[:top_k])
        return {"retrieved_images": search_image(query_embedding, top_k=top_k)}
    except Exception as e:
        raise Exception(f'Error search by image: {e}')

def search_by_text(query, top_k=5):

    try:
        translated_text = translator.translate(query, src="auto", dest="en")
        query_embedding = model.encode(translated_text)
        print("Text Embedding Sample:", query_embedding[:5])
        retrieved_images = search_image(query_embedding, top_k )
        print(f"Search Query: {query}")
        print(f"Translated Text: {translated_text}")
        print(f"Retrieved Images: {retrieved_images}")

        return {
            # "original_text": query.text,
            # "translated_text": translated_text,
            "retrieved_images": retrieved_images
            # "retrieved_images" : [f"http://localhost:8000/images/{os.path.basename(img)}" for img in retrieved_images]
        }

    except Exception as e:
        raise Exception(f'Error search by text: {e}')

# Load model BLIP
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    caption_ids = caption_model.generate(
        **inputs,
        max_length=350,
        num_beams=10,
        num_beam_groups=5,
        do_sample=False,
        temperature=0.6,
        top_p=0.9,
        diversity_penalty=1.0,
        early_stopping=True
    )
    caption = processor.batch_decode(caption_ids, skip_special_tokens=True)[0]
    return caption

def generate_caption(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    caption_ids = caption_model.generate(**inputs)
    caption = processor.batch_decode(caption_ids, skip_special_tokens=True)[0]
    return caption

def upload_image(image):
    try:
        image_path = os.path.join(IMAGE_FOLDER, image.name)
        temp_path = os.path.join(settings.MEDIA_ROOT, image.name)

        # Lưu ảnh vào thư mục tạm
        with default_storage.open(temp_path, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        shutil.move(temp_path, image_path)

        # Sinh mô tả bằng BLIP
        caption = generate_caption(image_path)

        # Mở ảnh và chuyển thành RGB
        image_pil = Image.open(image).convert("RGB")

        # Encode ảnh thành vector (chuyển thành numpy array)
        uploaded_image = np.array(model.encode(image_pil), dtype=np.float32).reshape(1, -1)

        # Xác định ID cho ảnh mới
        num_existing_vectors = index.ntotal  # Lấy số lượng vector hiện có
        image_id = np.array([num_existing_vectors], dtype=np.int64).reshape(1)  # Đảm bảo có đúng số chiều

        # Cập nhật FAISS index với ID
        index.add_with_ids(uploaded_image, image_id)
        faiss.write_index(index, index_path)

        # Cập nhật danh sách đường dẫn ảnh
        with open(image_files_path, "a") as f:
            f.write(f"{image_path}\n")

        return image.name, caption

    except Exception as e:
        raise Exception(f"Lỗi khi tải ảnh: {e}")






