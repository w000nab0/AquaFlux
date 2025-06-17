# AQUAFLUX/backend/logs/views.py

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .models import LogEntry
from .serializers import LogEntrySerializer, ImageUploadSerializer
from PIL import Image
import io
import google.generativeai as genai
import os
import json
import time


# 飼育ログの一覧表示と新規作成
class LogEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = LogEntrySerializer
    permission_classes = [IsAuthenticated] # 認証済みユーザーのみアクセス許可

    def get_queryset(self):
        # リクエストしているユーザーが作成したログのみを返す
        return LogEntry.objects.filter(user=self.request.user).order_by('-log_date', '-id')

    def perform_create(self, serializer):
        # ログ作成時に、リクエストしているユーザーを自動的に設定する

        serializer.save(user=self.request.user)
         


# 飼育ログの詳細表示、更新、削除
class LogEntryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LogEntrySerializer
    permission_classes = [IsAuthenticated] # 認証済みユーザーのみアクセス許可
    queryset = LogEntry.objects.all() # 全てのログから対象を見つける

    def get_queryset(self):
        # リクエストしているユーザーが所有するログのみを対象とする
        return LogEntry.objects.filter(user=self.request.user)
    



# 画像アップロード・解析API (Gemini Vision)
class ImageAnalyzeView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ImageUploadSerializer

    DEFAULT_RETRIES = 3  # デフォルトの再試行回数
    RETRY_DELAY_SECONDS = 2  # 再試行間の遅延時間（秒）

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        image_file = serializer.validated_data['image']
        
        try:
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_api_key:
                return Response(
                    {"error": "Gemini APIキーが設定されていません。"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')

            image_file.seek(0)
            img_data = image_file.read()

            extraction_prompt = (
                "これは水質試験紙の画像です。写真から、pH、KH、GH、NO2、NO3、Cl2の値を検出してJSON形式で出力してください。"
                "例: {\"ph\": 7.0, \"kh\": 6, \"gh\": 8, \"no2\": 0.1, \"no3\": 10.0, \"cl2\": 0.0}"
                "値が検出できない場合は、その項目をJSONに含めないでください。"
            )
            
            
            for attempt in range(self.DEFAULT_RETRIES):
                try:
                    response_gemini = model.generate_content(
                        [
                            extraction_prompt,
                            {"mime_type": image_file.content_type, "data": img_data}
                        ],
                        request_options={'timeout': 120} # タイムアウト時間を設定
                    )
                    response_gemini.resolve()

                    extracted_data = {}
                    raw_text_response = response_gemini.text.strip()
                    
                    # Geminiからの応答が '```json' と '```' で囲まれている場合を考慮
                    if raw_text_response.startswith('```json') and raw_text_response.endswith('```'):
                        # '```json' と '```' を取り除き、その間のJSON文字列を抽出
                        raw_text_response = raw_text_response[7:-3].strip()
                    
                    # ★JSONパースエラーのハンドリングを強化
                    try:
                        extracted_data = json.loads(raw_text_response)
                        # JSONが正常にパースされたらループを抜ける
                        break 
                    except json.JSONDecodeError as e:
                        # JSON形式が不正だった場合
                        print(f"Attempt {attempt + 1}: Geminiからの応答が有効なJSONではありませんでした: {e}")
                        print(f"Raw Gemini response: {raw_text_response}")
                        if attempt < self.DEFAULT_RETRIES - 1:
                            # 最後の試行でなければ再試行のために待機
                            time.sleep(self.RETRY_DELAY_SECONDS) 
                        else:
                            # 全ての試行が失敗したらエラーを返す
                            return Response(
                                {"error": "Geminiが有効な水質データをJSON形式で抽出できませんでした。", "details": str(e), "raw_gemini_response": raw_text_response},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                except Exception as e:
                    # Gemini API呼び出し自体に問題があった場合（ネットワークエラー、タイムアウトなど）
                    print(f"Attempt {attempt + 1}: Gemini API呼び出し中にエラーが発生しました: {e}")
                    if attempt < self.DEFAULT_RETRIES - 1:
                        # 最後の試行でなければ再試行のために待機
                        time.sleep(self.RETRY_DELAY_SECONDS)
                    else:
                        # 全ての試行が失敗したらエラーを返す
                        return Response(
                            {"error": "Gemini APIとの通信中に問題が発生しました。時間をおいて再試行してください。", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
      

            # 全ての試行が失敗した場合（return文が呼ばれない場合）は、ここには到達しないが念のため
            if not extracted_data:
                return Response(
                    {"error": "すべての試行が失敗しました。水質データを抽出できませんでした。"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                "message": "画像から水質データを抽出しました。",
                "water_data": extracted_data,
                "image_filename": image_file.name,
                "image_size": image_file.size,
            }, status=status.HTTP_200_OK)


        except Exception as e:
            print(f"画像解析API処理中にエラーが発生しました: {e}")
            return Response(
                {"error": "画像解析API処理中にエラーが発生しました。", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# AIアドバイス生成API
class AdviceGenerateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        water_data = request.data.get('water_data', {}) 
        notes = request.data.get('notes', '')
        fish_type = request.data.get('fish_type', '一般的な熱帯魚')
        tank_type = request.data.get('tank_type', '淡水') # 淡水/海水など

        # ユーザーの過去の飼育ログを取得（最新5件）
        recent_logs = LogEntry.objects.filter(user=request.user).order_by('-log_date')[:5]
        
        try:
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_api_key:
                return Response(
                    {"error": "Gemini APIキーが設定されていません。"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            genai.configure(api_key=gemini_api_key)
            # テキストを扱うモデル 'gemini-2.0-flash-lite' を使う
            model = genai.GenerativeModel('gemini-2.0-flash-lite')

            # ★★★ プロンプトテンプレートの構築 (f-stringを利用) ★★★
            water_data_str_parts = []
            if water_data: 
                for key, value in water_data.items():
                    if value is not None:
                        water_data_str_parts.append(f"{key}: {value}")
            
            water_data_for_prompt = ", ".join(water_data_str_parts) if water_data_str_parts else "（データなし）"

            # 過去のログ情報をプロンプトに追加
            log_history_text = ""
            if recent_logs.exists():
                log_history_text = "\n\n【参考：過去の飼育ログ履歴】\n"
                for i, log in enumerate(recent_logs, 1):
                    log_data_parts = []
                    if log.water_data:
                        for key, value in log.water_data.items():
                            if value is not None:
                                log_data_parts.append(f"{key}: {value}")
                    log_data_str = ", ".join(log_data_parts) if log_data_parts else "データなし"
                    log_history_text += f"{i}. {log.log_date} - 水質: {log_data_str}"
                    if log.notes:
                        log_history_text += f" (メモ: {log.notes[:50]}{'...' if len(log.notes) > 50 else ''})"
                    log_history_text += "\n"
                log_history_text += "\n上記の過去データも踏まえて、水質の変化傾向や改善点があれば言及してください。"
            
            prompt_template = (
                f"あなたは水槽の専門家です。以下の水槽のデータに基づいて、具体的で分かりやすいアドバイスをしてください。\n\n"
                f"【現在の状況】\n"
                f"水槽の種類: {tank_type}\n"
                f"主な魚の種類: {fish_type}\n"
                f"水質データ: {water_data_for_prompt}\n"
                f"その他メモ: {notes}"
                f"{log_history_text}\n\n"
                f"診断結果と、魚が快適に過ごせるように、具体的にどうすれば良いか教えてください。改善策は箇条書きで、専門用語は避け、初心者にも理解できるように説明してください。"
                f"現在の水質が良い場合は、それを維持するためのアドバイスをしてください。"
                f"過去のデータがある場合は、変化の傾向についてもコメントしてください。"
            )
            
            # Geminiにプロンプトを送信
            response_gemini = model.generate_content(prompt_template)
            # テキストモデルなので resolve() は必須ではないが、安全のため付けておく
            response_gemini.resolve() 

            advice_text = response_gemini.text

            return Response({
                "message": "AIによるアドバイスを生成しました。",
                "advice": advice_text,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"AIアドバイス生成API処理中にエラーが発生しました: {e}")
            return Response(
                {"error": "AIアドバイス生成API処理中にエラーが発生しました。", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
