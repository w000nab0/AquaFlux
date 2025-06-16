# AQUAFLUX/backend/users/serializers.py

from rest_framework import serializers 
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}} # パスワードは読み取り専用にし、書き込み時のみ有効にする

    def create(self, validated_data):
        # ユーザー作成時にパスワードをハッシュ化して保存する
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
