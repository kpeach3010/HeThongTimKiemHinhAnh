from django.utils.timezone import now
from django.db import models
from .user_model import User


class UserProfile(models.Model):

    class VipStatus(models.TextChoices):
        NONE = "none"
        PENDING = "pending"
        CONFIRMED = "confirmed"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    vip = models.CharField(
        max_length=10,
        choices=VipStatus.choices,
        default=VipStatus.NONE
    )
    search_count = models.IntegerField(default=0)  # Số lần tìm kiếm đã dùng
    last_search_date = models.DateField(default=now)  # Ngày tìm kiếm gần nhất

    def is_vip(self):
        return self.vip == "confirmed"

    def reset_search_count(self):
        """Đặt lại số lần tìm kiếm khi qua ngày mới"""
        if self.last_search_date != now().date():
            self.search_count = 0
            self.last_search_date = now().date()
            self.save()

