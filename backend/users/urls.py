from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,    # ユーザー名とパスワードからトークンを取得するビュー（ログイン用）
    TokenRefreshView,       # リフレッシュトークンを使ってアクセストークンを更新するビュー
)
from .views import UserRegisterView, ProtectedView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('protected/', ProtectedView.as_view(), name='protected_test'),
]