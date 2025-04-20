from django.urls import path

from .ai_models.img_search import search_image
from .views.user_view import RegisterView, LoginView, LogoutView, UserView, DeleteUserImageView
from .views.img_search_view import (
    SearchByTextView,
    SearchByImageView,
    UploadUserImageView,
    RandomImageAPIView,
    UserImageListByUserView
)
from .views.user_view import (
    csrf_token_view,
    UserListViewWithAllImageUploaded,
    UserVipRequestView
)
from .views.admin_view import DisableUserAndDeleteImagesView, EnableUserView, ApproveUserVipRequest

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('search-by-text/', SearchByTextView.as_view(), name='search-by-text'),
    path('search-by-image/', SearchByImageView.as_view(), name='search-by-image'),
    path('csrf/', csrf_token_view, name='csrf_token'),
    path("my-images/", UserImageListByUserView.as_view(), name="my-images"),
    path("upload-image/", UploadUserImageView.as_view(), name="upload-image"),
    path("user-images/", UserListViewWithAllImageUploaded.as_view(), name="user-images"),
    path("disable-user/<int:id>/", DisableUserAndDeleteImagesView.as_view(), name="disable-user"),
    path("enable-user/<int:id>/", EnableUserView.as_view(), name="enable-user"),
    path('random-images/', RandomImageAPIView.as_view(), name='random-images'),
    path('user/', UserView.as_view(), name='user'),
    path('user-vip-request/', UserVipRequestView.as_view(), name='user-vip-request'),
    path('user-vip-approve/<int:user_id>/', ApproveUserVipRequest.as_view(), name='user-vip-approve'),
    path('delete-image/', DeleteUserImageView.as_view(), name='delete-image'),
]

