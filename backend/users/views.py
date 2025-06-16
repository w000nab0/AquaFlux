from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from .models import CustomUser


class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


# ユーザーログインAPI
#class LoginView(ObtainAuthToken):
    #serializer_class = LoginSerializer
    #permission_classes = [AllowAny] # ログイン自体は認証なしでできるようにする

    #def post(self, request, *args, **kwargs):
        #serializer = self.serializer_class(data=request.data,
                                           #context={'request': request})
        #serializer.is_valid(raise_exception=True)
        #user = serializer.validated_data['user']
        #token, created = Token.objects.get_or_create(user=user)
        #return Response({
            #'token': token.key,
            #'user_id': user.pk,
            #'email': user.email,
            #'username': user.username
        #})


# 認証が必要なテスト用APIビュー
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated] # 認証済みユーザーのみアクセス許可

    def get(self, request):
        # 認証されたユーザーの情報を使ってレスポンスを返す
        return Response({
            "message": "このメッセージは認証済みユーザーのみ見れます！",
            "user_id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        }, status=status.HTTP_200_OK)