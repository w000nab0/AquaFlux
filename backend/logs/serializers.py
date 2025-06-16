from rest_framework import serializers
from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    # ユーザー名を表示するための読み取り専用フィールドを追加
    # source='user.username' で関連するユーザーオブジェクトのusernameを参照
    # read_only=True でこのフィールドがPOST/PUT時に送られてこないようにする
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LogEntry
        # APIで扱いたいフィールドを全て指定します
        fields = [
            'id', 'user', 'user_username', 'log_date',
            'water_data', 
            'fish_type', 'tank_type','notes', 'updated_at',
        ]
        read_only_fields = ['user', 'log_date', 'updated_at']
     
        
    
    
# 画像アップロード用のシリアライザー
class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField() # 画像ファイルを受け取るためのフィールド    