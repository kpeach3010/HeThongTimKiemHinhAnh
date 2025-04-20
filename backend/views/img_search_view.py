from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from ..ai_models.img_search import search_by_text, search_by_image, upload_image
from backend.models import UserProfile, UserImage
from backend.serializers import (
    SearchByTextSerializer, SearchByImageSerializer, UploadImageSerializer, UserImageSerializer
)
from .user_view import SEARCH_LIMITS
from django.conf import settings
import random
import os
from rest_framework.views import APIView


class SearchByTextView (generics.GenericAPIView):
    serializer_class = SearchByTextSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] # Người dùng đã đăng nhập

    def post(self, request, *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy hồ sơ người dùng!"}, status=status.HTTP_404_NOT_FOUND)
        # Reset số lần tìm kiếm nếu sang ngày mới
        user_profile.reset_search_count()

        # Kiểm tra giới hạn tìm kiếm
        max_searches = SEARCH_LIMITS[user_profile.is_vip()]
        if user_profile.search_count >= max_searches:
            return Response({"error": "Bạn đã đạt giới hạn tìm kiếm hôm nay!"}, status=status.HTTP_403_FORBIDDEN)
        text = request.data['text']
        # Xử lý top_k
        top_k = request.data.get("top_k", [32])
        if isinstance(top_k, list):
            top_k = top_k[0]
        try:
            top_k = int(top_k)
        except ValueError:
            return Response({"error": "top_k phải là số nguyên!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = search_by_text(text, top_k)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Cập nhật số lần tìm kiếm
        user_profile.search_count += 1
        user_profile.save()

        # Trả về kết quả cùng số lượt tìm kiếm còn lại
        return Response({
            "message": "Tìm kiếm thành công!",
            "remaining_searches": max_searches - user_profile.search_count,
            **result  # Kết quả tìm kiếm thực tế
        }, status=status.HTTP_200_OK)


class SearchByImageView(generics.GenericAPIView):
    serializer_class = SearchByImageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy hồ sơ người dùng!"}, status=status.HTTP_404_NOT_FOUND)

        user_profile.reset_search_count()
        max_searches = SEARCH_LIMITS.get(user_profile.is_vip(), 5)

        if user_profile.search_count >= max_searches:
            return Response({"error": "Bạn đã đạt giới hạn tìm kiếm hôm nay!"}, status=status.HTTP_403_FORBIDDEN)

        if "image" not in request.FILES:
            return Response({"error": "Vui lòng tải lên một hình ảnh!"}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES["image"]

        # Xử lý top_k
        top_k = request.data.get("top_k", [32])
        if isinstance(top_k, list):
            top_k = top_k[0]
        try:
            top_k = int(top_k)
        except ValueError:
            return Response({"error": "top_k phải là số nguyên!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = search_by_image(image, top_k)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Đảm bảo result là dictionary
        if not isinstance(result, dict):
            result = {"results": result}

        user_profile.search_count += 1
        user_profile.save()

        return Response({
            "message": "Tìm kiếm thành công!",
            "remaining_searches": max_searches - user_profile.search_count,
            **result
        }, status=status.HTTP_200_OK)


class UploadUserImageView(generics.GenericAPIView):
    serializer_class = UploadImageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "Không tìm thấy hồ sơ người dùng!"}, status=status.HTTP_404_NOT_FOUND)

        if not request.FILES.get("image"):
            return Response({"error": "Không có ảnh nào được tải lên!"}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES.get("image")

        try:
            # Gọi hàm upload_image để lưu ảnh, sinh mô tả, cập nhật FAISS
            image_name, caption = upload_image(image)

            #  Kiểm tra xem ảnh với cùng tên đã tồn tại chưa
            if UserImage.objects.filter(user=request.user, image_name=image_name).exists():
                return Response(
                    {"error": "Bạn đã tải lên ảnh với cùng tên. Vui lòng đổi tên hoặc xóa ảnh cũ trước khi tải lên."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lưu vào database nếu không trùng tên
            user_image = UserImage.objects.create(user=request.user, image_name=image_name, caption=caption)

            return Response(
                {"message": "Đã tải ảnh lên thành công!", "image_name": user_image.image_name, "caption": user_image.caption},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": f"Lỗi khi tải ảnh: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UserImageListByUserView(generics.ListAPIView):
    queryset = UserImage.objects.all()
    serializer_class = UserImageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(user=self.request.user)
        serializer = UserImageSerializer(queryset, many=True)
        data = serializer.data.copy()
        data = list(map(lambda user_img: {
            'image_name': user_img['image_name'],
            'description': user_img['caption']
        }, data))
        return Response({
            'images': data
        }, status=status.HTTP_200_OK)

class RandomImageAPIView(APIView):
    def get(self, request):
        try:
            all_images = [img for img in os.listdir(settings.MEDIA_ROOT) if img.endswith(('.jpg', '.png', '.jpeg'))]
            selected_images = random.sample(all_images, 5) if len(all_images) >= 5 else all_images

            image_urls = [request.build_absolute_uri(settings.MEDIA_URL + img) for img in selected_images]

            return Response({"images": image_urls}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)