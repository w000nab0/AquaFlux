# AQUAFLUX/backend/logs/tests.py

# ★変更: TestCase ではなく APITestCase をインポート
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
import io # ioモジュールは引き続き必要
from django.urls import reverse
import json
from unittest.mock import patch, MagicMock
import time

from .views import ImageAnalyzeView

import os
os.environ['GEMINI_API_KEY'] = 'dummy_api_key_for_test'


# ★変更: TestCase ではなく APITestCase を継承
class ImageAnalyzeViewTest(APITestCase):
    def setUp(self):
        # APITestCase は client 属性を自動的に提供するため、factory は不要
        # self.factory = APIRequestFactory() 
        
        # SimpleUploadedFile の内容を、より「本物」に近いGIFデータにする
        gif_data = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        self.image_file = SimpleUploadedFile(
            name='test_water_strip.gif',
            content=gif_data,
            content_type='image/gif'
        )
        self.url = reverse('analyze-image') 

    # --- 成功ケースのテスト ---
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_image_analyze_success(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.text = '```json\n{"ph": 7.5, "nitrate": 10.0}\n```'
        mock_response.resolve.return_value = None
        mock_generate_content.return_value = mock_response

        # ★変更: self.client.post を使用
        # APITestCase の client は format='multipart' を自動的に処理します
        response = self.client.post(
            self.url,
            {'image': self.image_file}, # 'image' はシリアライザーのフィールド名
            format='multipart' # 明示的に指定しても問題ないですが、clientが自動で処理するはず
        )

        # デバッグのためにレスポンスをプリントしてみる
        # print(f"test_image_analyze_success Response Status: {response.status_code}")
        # print(f"test_image_analyze_success Response Data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('water_data', response.data)
        self.assertEqual(response.data['water_data']['ph'], 7.5)
        self.assertEqual(response.data['water_data']['nitrate'], 10.0)
        mock_generate_content.assert_called_once()


    # --- JSONパースエラーからの再試行テスト (成功するケース) ---
    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('time.sleep', return_value=None)
    def test_image_analyze_json_parse_error_with_retries(self, mock_sleep, mock_generate_content):
        mock_response_invalid = MagicMock()
        mock_response_invalid.text = 'This is not JSON.'
        mock_response_invalid.resolve.return_value = None

        mock_response_valid = MagicMock()
        mock_response_valid.text = '```json\n{"ph": 6.8, "nitrite": 0.05}\n```'
        mock_response_valid.resolve.return_value = None

        mock_generate_content.side_effect = [
            mock_response_invalid, # 1回目
            mock_response_invalid, # 2回目
            mock_response_valid    # 3回目 (成功)
        ]

        # ★変更: self.client.post を使用
        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('water_data', response.data)
        self.assertEqual(response.data['water_data']['ph'], 6.8)
        self.assertEqual(response.data['water_data']['nitrite'], 0.05)
        self.assertEqual(mock_generate_content.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


    # --- JSONパースエラーが連続して失敗するテスト ---
    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('time.sleep', return_value=None)
    def test_image_analyze_json_parse_error_all_retries_fail(self, mock_sleep, mock_generate_content):
        mock_response_invalid = MagicMock()
        mock_response_invalid.text = 'Always invalid JSON.'
        mock_response_invalid.resolve.return_value = None
        mock_generate_content.return_value = mock_response_invalid

        # ★変更: self.client.post を使用
        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        # ここはまだ FAIL または ERROR になる可能性があります（views.py側のステータスコードとメッセージ構造による）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # print(f"test_image_analyze_json_parse_error_all_retries_fail Response Data: {response.data}")
        self.assertIn('error', response.data)
        self.assertIn('Geminiが有効な水質データをJSON形式で抽出できませんでした。', response.data['error'])
        self.assertEqual(mock_generate_content.call_count, ImageAnalyzeView.DEFAULT_RETRIES)
        self.assertEqual(mock_sleep.call_count, ImageAnalyzeView.DEFAULT_RETRIES - 1)


    # --- API通信エラーからの再試行テスト ---
    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('time.sleep', return_value=None)
    def test_image_analyze_api_error_with_retries(self, mock_sleep, mock_generate_content):
        mock_response_valid = MagicMock()
        mock_response_valid.text = '{"gh": 7.0, "kh": 5.0}'
        mock_response_valid.resolve.return_value = None

        mock_generate_content.side_effect = [
            Exception("API temporary unavailable"),
            Exception("Network timeout"),
            mock_response_valid
        ]

        # ★変更: self.client.post を使用
        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('water_data', response.data)
        self.assertEqual(response.data['water_data']['gh'], 7.0)
        self.assertEqual(response.data['water_data']['kh'], 5.0)
        self.assertEqual(mock_generate_content.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)


    # --- API通信エラーが連続して失敗するテスト ---
    @patch('google.generativeai.GenerativeModel.generate_content')
    @patch('time.sleep', return_value=None)
    def test_image_analyze_api_error_all_retries_fail(self, mock_sleep, mock_generate_content):
        mock_generate_content.side_effect = Exception("API consistently failing")

        # ★変更: self.client.post を使用
        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        # ここはまだ FAIL になる可能性があります（views.py側のステータスコードとメッセージ構造による）
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # print(f"test_image_analyze_api_error_all_retries_fail Response Data: {response.data}")
        self.assertIn('error', response.data)
        self.assertIn('Gemini APIとの通信中に問題が発生しました。時間をおいて再試行してください。', response.data['error'])
        self.assertEqual(mock_generate_content.call_count, ImageAnalyzeView.DEFAULT_RETRIES)
        self.assertEqual(mock_sleep.call_count, ImageAnalyzeView.DEFAULT_RETRIES - 1)

    # --- APIキーがない場合のテスト ---
    @patch('os.environ.get', return_value=None)
    def test_image_analyze_no_api_key(self, mock_environ_get):
        # ★変更: self.client.post を使用
        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        # ここはまだ FAIL になる可能性があります（views.py側のステータスコードとメッセージ構造による）
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # print(f"test_image_analyze_no_api_key Response Data: {response.data}")
        self.assertIn('error', response.data)
        self.assertIn('Gemini APIキーが設定されていません。', response.data['error'])