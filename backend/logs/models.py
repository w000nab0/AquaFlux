from django.db import models
from django.conf import settings

class LogEntry(models.Model):
    # どのユーザーのログかを示すフィールド (CustomUserと紐付け)
    # ユーザーが削除されたら、関連するログも一緒に削除されるように設定 (on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='log_entries')

    # ログを記録した日付
    log_date = models.DateField(auto_now_add=True) # 作成時に自動的に日付が入力される

    water_data = models.JSONField(default=dict)

    # 魚の種類 (オプション)
    fish_type = models.CharField(max_length=100, blank=True, null=True)

    # 水槽の種類 (淡水/海水など)
    TANK_TYPE_CHOICES = [
        ('freshwater', '淡水'),
        ('saltwater', '海水'),
    ]
    tank_type = models.CharField(
        max_length=20,
        choices=TANK_TYPE_CHOICES,
        default='freshwater'
    )

    # 自由記述のメモ
    notes = models.TextField(blank=True, null=True)

    # ログの最終更新日時
    updated_at = models.DateTimeField(auto_now=True) # 更新時に自動的に日時が更新される

    class Meta:
        # データベースでのテーブル名やソート順などを設定します
        verbose_name = '飼育ログ' # 管理サイトでの表示名
        verbose_name_plural = '飼育ログ' # 管理サイトでの複数形表示名
        ordering = ['-log_date', '-id'] # デフォルトのソート順 (新しい日付のログが上に来るように)

    def __str__(self):
        # オブジェクトが文字列として表示されるときの形式
        return f"{self.user.username} - {self.log_date} のログ"
