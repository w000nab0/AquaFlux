from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # ここに、デフォルトのユーザーモデルに追加したいフィールドを定義します
    # 例: ニックネーム、生年月日など
    # 現時点では何も追加しなくても大丈夫です
    # user_type = models.CharField(max_length=50, default='customer')

    def __str__(self):
        return self.username
# Create your models here.
