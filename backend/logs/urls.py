# AQUAFLUX/backend/logs/urls.py

from django.urls import path
from .views import (
    LogEntryListCreateView,
    LogEntryRetrieveUpdateDestroyView,
    ImageAnalyzeView,
    AdviceGenerateView
)


urlpatterns = [
    # 飼育ログの一覧と新規作成 (POST /api/logs/)
    path('', LogEntryListCreateView.as_view(), name='logentry-list-create'),
    # 特定の飼育ログの詳細、更新、削除 (GET/PUT/PATCH/DELETE /api/logs/1/)
    path('<int:pk>/', LogEntryRetrieveUpdateDestroyView.as_view(), name='logentry-detail'),
    # 画像分析用のAPIエンドポイント
    path('analyze-image/', ImageAnalyzeView.as_view(), name='analyze-image'),
    path('advice/', AdviceGenerateView.as_view(), name='advice-generate'),
]