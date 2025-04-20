import os
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import BasePermission
from backend.models import UserImage, User, UserProfile
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Cấu hình thư mục
IMAGE_FOLDER = "C:/NienLuanCSN/flickr30k_images/flickr30k_images"
INDEX_PATH = "C:/NienLuanCSN/index.faiss"
IMAGE_FILES_PATH = "C:/NienLuanCSN/image_files(1).txt"


# Chỉ cho phép SuperUser thực hiện thao tác
class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class DisableUserAndDeleteImagesView(generics.UpdateAPIView):
    queryset = User.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSuperUser]
    lookup_field = "id"

    def mark_image_as_deleted(self, image_path):
        """Thay vì xóa ngay, ta đánh dấu ảnh bị xóa trong danh sách"""
        if not os.path.exists(IMAGE_FILES_PATH):
            return

        with open(IMAGE_FILES_PATH, "r") as f:
            image_files = f.readlines()
        image_files = [line.strip() for line in image_files]

        try:
            idx = image_files.index(image_path)
            image_files[idx] = "[DELETED]"  # Đánh dấu ảnh bị xóa
        except ValueError:
            return  # Ảnh không có trong danh sách

        with open(IMAGE_FILES_PATH, "w") as f:
            f.writelines("\n".join(image_files) + "\n")

    def delete_user_images(self, user):
        """Xóa tất cả hình ảnh của người dùng khỏi thư mục và database"""
        images = UserImage.objects.filter(user=user)

        if not images.exists():  # Kiểm tra nếu không có ảnh nào
            return None

        for img in images:
            image_path = os.path.join(IMAGE_FOLDER, img.image_name)  # Nối đường dẫn

            if os.path.exists(image_path):
                os.remove(image_path)  # Xóa file ảnh

            self.mark_image_as_deleted(image_path)  # Đánh dấu ảnh bị xóa

        # Xóa toàn bộ dữ liệu hình ảnh của user khỏi database
        images.delete()

        return "Deleted user images successfully"

    def update(self, request, *args, **kwargs):
        """Xác nhận vô hiệu hóa tài khoản"""
        user = self.get_object()
        # confirm = request.data.get("confirm")
        # if not confirm == "yes":
        #   return Response({"message": "Action canceled"}, status=status.HTTP_400_BAD_REQUEST)
        name = self.delete_user_images(user)
        user.is_active = False  # Vô hiệu hóa tài khoản
        user.save()
        # Ghi log vào django_admin_log
        content_type = ContentType.objects.get_for_model(user)  # Lấy content type của model User
        LogEntry.objects.log_action(
            user_id=request.user.id,  # ID của admin thực hiện hành động
            content_type_id=content_type.pk,  # Content type của User
            object_id=user.id,  # ID của user bị vô hiệu hóa
            object_repr=str(user),  # Biểu diễn dạng chuỗi của user (thường là username hoặc email)
            action_flag=CHANGE,  # Đây là hành động sửa (vô hiệu hóa tài khoản)
            change_message="Disabled user and deleted associated images"
        )
        return Response(
            {"message": "User disabled and images marked as deleted", "name": name}, status=status.HTTP_200_OK)


class EnableUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSuperUser]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = True
        user.save()
        # Ghi log vào django_admin_log
        content_type = ContentType.objects.get_for_model(user)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=content_type.pk,
            object_id=user.id,
            object_repr=str(user),
            action_flag=CHANGE,
            change_message="Enabled user"
        )
        return Response({"message": "User enabled"}, status=status.HTTP_200_OK)


class ApproveUserVipRequest(generics.UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSuperUser]

    def put(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=self.kwargs.get('user_id'))
        user_profile.vip = UserProfile.VipStatus.CONFIRMED
        user_profile.save()

        # Ghi log vào django_admin_log
        content_type = ContentType.objects.get_for_model(user_profile)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=content_type.pk,
            object_id=user_profile.id,
            object_repr=str(user_profile),
            action_flag=CHANGE,
            change_message="Approved VIP request via API"
        )
        return Response({
            "message": "Approve VIP successfully!"
        }, status=status.HTTP_200_OK)

