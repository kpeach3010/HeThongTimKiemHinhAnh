from backend.models import User, UserImage
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from backend.serializers import UserSerializer, UserProfileSerializer
from backend.models import UserProfile
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import BasePermission
import os


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser

def csrf_token_view(request):
    return JsonResponse({'csrftoken': get_token(request)})


SEARCH_LIMITS ={
    True: 10,
    False: 5
}

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            user_profile_data = {'user': user.id}
            user_profile_serializer = UserProfileSerializer(data=user_profile_data)
            if user_profile_serializer.is_valid():
                user_profile_serializer.save()
                return Response({
                    'user': user_serializer.data,
                }, status=status.HTTP_201_CREATED)
            return Response({
                'error': user_profile_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'error': user_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({'success': False, 'message': 'Email does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({'success': False, 'message': 'Account is not active'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'success': False, 'message': 'Password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        user_data['nums_image'] = UserImage.objects.filter(user=user.id).count()

        return Response({
            "message": "Login success",
            "token": token.key,
            "user": user_data,
        }, status=status.HTTP_200_OK)


# User API to logout user
class LogoutView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        try:
            token = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

        token.delete()
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "user": UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)


class UserListViewWithAllImageUploaded(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        users_serializer = UserSerializer(queryset, many=True)
        users_data = users_serializer.data.copy()

        for user in users_data:
            user_images = UserImage.objects.filter(user=user['id'])
            images_names = list(map(lambda user_image: user_image.image_name, user_images))
            user['image_names'] = images_names

        return Response({
            'success': True,
            'message': 'All users have been listed successfully',
            'users': users_data
        }, status=status.HTTP_200_OK)


class UserVipRequestView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.vip = UserProfile.VipStatus.PENDING
        user_profile.save()
        return Response({
            "message": "Send VIP request successfully!",
            "vip": user_profile.vip
        }, status=status.HTTP_200_OK)


class DeleteUserImageView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        image_name = request.query_params.get('image_name')

        if not image_name:
            return Response({"error": "Image name is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Lấy ảnh của người dùng hiện tại với tên ảnh được cung cấp
            image = UserImage.objects.get(user=request.user, image_name=image_name)

            # Xóa file ảnh vật lý trong thư mục
            image_path = os.path.join("C:/NienLuanCSN/flickr30k_images/flickr30k_images", image_name)
            if os.path.exists(image_path):
                os.remove(image_path)

            # Cập nhật file image_files.txt
            self.mark_image_as_deleted(image_path)

            # Xóa bản ghi trong database
            image.delete()

            return Response({"message": "Deleted selected image successfully"}, status=status.HTTP_200_OK)

        except UserImage.DoesNotExist:
            return Response({"error": "Image not found or you don't have permission to delete this image"},
                            status=status.HTTP_404_NOT_FOUND)

    def mark_image_as_deleted(self, image_path):
        """Đánh dấu ảnh là đã bị xóa trong image_files.txt"""
        image_files_path = "C:/NienLuanCSN/image_files(1).txt"

        with open(image_files_path, "r") as f:
            lines = f.readlines()

        with open(image_files_path, "w") as f:
            for line in lines:
                if line.strip() != image_path:  # Giữ lại những ảnh không bị xóa
                    f.write(line)



