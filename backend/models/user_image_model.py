from django.db import models
from .user_model import User


class UserImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    image_name = models.CharField(max_length=50, default=None)
    caption = models.TextField(blank=True, null=True)  # Mô tả tự động sinh ra từ BLIP
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Lưu thời gian tải lên

    class Meta:
        unique_together = ('user', 'image_name')

    def __str__(self):
        return f"{self.user} - {self.image_name}"