from nicegui import ui, app
import requests
import os
import json # water_data の表示のために追加
import functools

# DjangoバックエンドのAPIベースURL
DJANGO_API_BASE_URL = os.environ.get("DJANGO_API_BASE_URL", "http://web:8000/api")

def auth_protected(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # ユーザーがログインしているか確認
        if not app.storage.user.get('access_token'):
            ui.notify('ログインしてください。', type='negative')
            ui.navigate.to('/login')
            return
        return await func(*args, **kwargs)
    return wrapper

# UIの基盤となるレイアウト（ヘッダーやフッターなど、共通部分）を作成します
def create_common_layout():
    # ui.header() のコンテキスト内で is_logged_in を評価することで、
    # ページがロードされるたびに現在のログイン状態を反映
    is_logged_in = 'access_token' in app.storage.user

    with ui.header().classes('items-center justify-between bg-primary text-white q-pa-md'):
        ui.label('AQUAFLUX').classes('text-h6 text-weight-bold')
        with ui.row().classes('items-center'):
            ui.link('飼育ログ', '/logs').classes('text-white q-px-sm')
            ui.link('AIアドバイス', '/advice').classes('text-white q-px-sm')
            
            if is_logged_in:
                # ユーザー名表示を追加 (あれば)
                ui.label(f"ようこそ, {app.storage.user.get('username', 'ユーザー')}")
                ui.button('ログアウト', on_click=logout).props('flat color=white').classes('q-ml-md')
            else:
                ui.button('ログイン', on_click=lambda: ui.navigate.to('/login')).props('flat color=white').classes('q-ml-md')
                ui.button('登録', on_click=lambda: ui.navigate.to('/register')).props('flat color=white')

    with ui.left_drawer().classes('bg-blue-100') as left_drawer:
        ui.label('メニュー').classes('text-h6 q-pa-md')
        ui.separator()
        ui.link('ホーム', '/').classes('q-pa-md block')
        ui.link('飼育ログ', '/logs').classes('q-pa-md block')
        ui.link('AIアドバイス', '/advice').classes('q-pa-md block')
        if not is_logged_in:
            ui.link('ログイン', '/login').classes('q-pa-md block')
            ui.link('登録', '/register').classes('q-pa-md block')

    with ui.footer().classes('bg-grey-8 text-white q-pa-sm text-center'):
        ui.label('© 2025 AQUAFLUX. All rights reserved.').classes('text-caption')

# ログイン処理
async def login_user(username, password):
    try:
        response = requests.post(f"{DJANGO_API_BASE_URL}/users/token/", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            app.storage.user['access_token'] = data['access']
            app.storage.user['refresh_token'] = data['refresh']
            app.storage.user['username'] = username
            ui.notify('ログインしました！', type='positive')
            ui.navigate.to('/')
        else:
            error_detail = response.json().get('detail', '不明なエラー')
            ui.notify(f'ログイン失敗: {error_detail}', type='negative')
    except requests.exceptions.ConnectionError:
        ui.notify('APIサーバーに接続できません。', type='negative')
    except Exception as e:
        ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')

# ログアウト処理
async def logout():
    if 'access_token' in app.storage.user:
        del app.storage.user['access_token']
    if 'refresh_token' in app.storage.user:
        del app.storage.user['refresh_token']
    if 'username' in app.storage.user:
        del app.storage.user['username']
    ui.notify('ログアウトしました。', type='info')
    ui.navigate.to('/login')

# ユーザー登録処理
async def register_user(username, password, password_confirm, email):
    if password != password_confirm:
        ui.notify('パスワードとパスワード（確認）が一致しません。', type='negative')
        return

    try:
        response = requests.post(f"{DJANGO_API_BASE_URL}/users/register/", json={
            "username": username,
            "password": password,
            "email": email
        })
        if response.status_code == 201:
            ui.notify('ユーザー登録が完了しました！ログインしてください。', type='positive')
            ui.navigate.to('/login')
        else:
            error_detail = response.json()
            # Djangoからのエラー詳細をより分かりやすく表示
            error_messages = []
            for field, errors in error_detail.items():
                if isinstance(errors, list):
                    error_messages.append(f"{field}: {', '.join(errors)}")
                else:
                    error_messages.append(f"{field}: {errors}")
            ui.notify(f'登録失敗: {"; ".join(error_messages)}', type='negative')
    except requests.exceptions.ConnectionError:
        ui.notify('APIサーバーに接続できません。', type='negative')
    except Exception as e:
        ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')

# ホームページ
@ui.page('/')
async def index_page():
    create_common_layout() # 共通レイアウトを適用

    with ui.column().classes('absolute-center items-center'):
        if app.storage.user.get('access_token'):
            ui.label(f'ようこそ、{app.storage.user.get("username")}さん！').classes('text-2xl font-bold mb-4')
            ui.button('飼育ログを見る', on_click=lambda: ui.navigate.to('/logs')).classes('mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700')
            ui.button('ログアウト', on_click=logout).classes('mt-2 px-6 py-3 bg-red-600 text-white rounded-lg shadow-md hover:bg-red-700')
        else:
            ui.label('AQUAFLUXへようこそ！').classes('text-2xl font-bold mb-4')
            ui.label('ログインまたは新規登録して、飼育ログを開始しましょう。').classes('mb-4')
            ui.button('ログイン', on_click=lambda: ui.navigate.to('/login')).classes('px-6 py-3 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-700 mr-2')
            ui.button('新規登録', on_click=lambda: ui.navigate.to('/register')).classes('px-6 py-3 bg-indigo-600 text-white rounded-lg shadow-md hover:bg-indigo-700')

# 飼育ログ一覧ページ
@ui.page('/logs')
async def logs_page():
    create_common_layout() # 共通レイアウトを適用
    
    # 認証チェック
    if not app.storage.user.get('access_token'):
        ui.notify('ログインしてください。', type='negative')
        ui.navigate.to('/login')
        return

    ui.add_head_html('<title>飼育ログ一覧 - AquaFlux</title>')
    ui.label('飼育ログ一覧').classes('text-3xl font-bold mb-6 text-center w-full')

    # 新規ログ作成ボタン (これは /logs/new ページに遷移)
    ui.button('新しい飼育ログを作成', on_click=lambda: ui.navigate.to('/logs/new')).classes('px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700 mb-6')

    log_data_container = ui.column().classes('w-full items-center')

    async def fetch_logs():
        # ローディングスピナー表示
        with log_data_container:
            ui.spinner(size='lg').classes('absolute-center')
            ui.label('ログデータをロード中...').classes('text-lg text-gray-500 mt-4')

        log_data_container.clear() # 既存の内容をクリア

        access_token = app.storage.user.get('access_token')
        if not access_token:
            ui.notify('ログインしていません。', type='negative')
            ui.navigate.to('/login')
            return

        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get(f"{DJANGO_API_BASE_URL}/logs/", headers=headers)
            response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる

            logs = response.json()

            if not logs:
                with log_data_container:
                    ui.label('まだ飼育ログがありません。新しいログを作成しましょう！').classes('text-lg text-gray-600 mt-8')
                return

            # テーブルでログを表示
            columns = [
                {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                {'name': 'log_date', 'label': '日付', 'field': 'log_date', 'sortable': True},
                {'name': 'fish_type', 'label': '魚の種類', 'field': 'fish_type', 'sortable': True},
                {'name': 'tank_type', 'label': '水槽の種類', 'field': 'tank_type', 'sortable': True},
                {'name': 'water_data', 'label': '水質データ', 'field': 'water_data'},
                {'name': 'notes', 'label': 'メモ', 'field': 'notes'},
            ]
            rows = []
            for log in logs:
                # water_data をより見やすく整形
                water_data_str = "未記録"
                if log['water_data']:
                    data_parts = []
                    for k, v in log['water_data'].items():
                        if k == 'ph' and v is not None:
                            data_parts.append(f"pH: {v:.1f}")
                        elif v is not None:
                            data_parts.append(f"{k.upper()}: {int(v)}")
                    water_data_str = ", ".join(data_parts) if data_parts else "未記録"

                row = {
                    'id': log['id'],
                    'log_date': log['log_date'],
                    'fish_type': log['fish_type'] if log['fish_type'] else '未設定',
                    'tank_type': log['tank_type'],
                    'water_data': water_data_str,
                    'notes': (log['notes'][:50] + '...') if log['notes'] and len(log['notes']) > 50 else (log['notes'] if log['notes'] else 'なし'),
                }
                rows.append(row)

            with log_data_container:
                def handle_row_click(e):
                    row = e.args[1]  # The row upon which user has clicked/tapped
                    ui.navigate.to(f"/logs/{row['id']}")
                
                log_table = ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='id'
                ).classes('w-full shadow-lg rounded-lg')
                log_table.on('rowClick', handle_row_click)

        except requests.exceptions.RequestException as e:
            if response.status_code == 401:
                ui.notify('認証エラー: ログインし直してください。', type='negative')
                ui.navigate.to('/login')
            else:
                ui.notify(f'飼育ログの取得に失敗しました: {e}', type='negative')
            print(f"Error details: {str(e)}")  # エラーの詳細をコンソールに出力
        except ValueError as e:
            ui.notify(f'JSONパースエラー: {e}', type='negative')
        except Exception as e:
            ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')
            print(f"Error details: {str(e)}")  # エラーの詳細をコンソールに出力

    ui.timer(0.1, fetch_logs, once=True) # ページ表示後に非同期でロード
    
    # ログアウトボタン（ナビゲーションバーとは別にページ内にも設置）
    ui.button('ログアウト', on_click=logout).classes('mt-8 px-6 py-3 bg-red-600 text-white rounded-lg shadow-md hover:bg-red-700')


# 飼育ログ新規作成ページ
@ui.page('/logs/new')
@auth_protected
async def new_log_entry_page():
    access_token = app.storage.user.get('access_token')
    if not access_token:
        ui.notify('ログインしていません。', type='negative')
        ui.navigate.to('/login')
        return

    with ui.header().classes('items-center justify-between text-white bg-blue-600 p-4'):
        ui.label('新しい飼育ログ').classes('text-2xl font-bold')
        with ui.row():
            ui.button('ホームへ', on_click=lambda: ui.navigate.to('/')).props('flat color=white icon=home')
            ui.button('ログ一覧', on_click=lambda: ui.navigate.to('/logs')).props('flat color=white icon=list')
            ui.button('ログアウト', on_click=logout).props('flat color=white icon=logout')

    with ui.card().classes('w-full max-w-2xl mx-auto my-8 p-6 shadow-xl rounded-lg'):
        # UI入力コンポーネントの定義 (ph_input, kh_inputなどがここで定義されている前提)
        # 既存のコードをそのまま使用してください

        with ui.grid(columns=2).classes('w-full gap-4'):
            ph_input = ui.number('pH', value=7.0, format='%.1f').props('step=0.1 min=0 max=14').classes('w-full')
            kh_input = ui.number('KH (炭酸塩硬度)', value=4, format='%.0f').props('min=0 max=20').classes('w-full')
            gh_input = ui.number('GH (総硬度)', value=6, format='%.0f').props('min=0 max=30').classes('w-full')
            no2_input = ui.number('NO2 (亜硝酸塩)', value=0.0, format='%.1f').props('step=0.1 min=0 max=10').classes('w-full')
            no3_input = ui.number('NO3 (硝酸塩)', value=5, format='%.0f').props('min=0 max=100').classes('w-full')
            cl2_input = ui.number('Cl2 (塩素)', value=0.0, format='%.1f').props('step=0.1 min=0 max=5').classes('w-full')
        
        notes_input = ui.textarea('メモ').classes('w-full mt-4').props('rows=3')
        fish_type_input = ui.input('魚種 (例: ネオンテトラ)').classes('w-full mt-4')
        
        tank_type_options_map = {
            'freshwater': '淡水',
            'saltwater': '海水',
        }
        tank_type_input = ui.select(options=tank_type_options_map, value='freshwater', label='水槽の種類').classes('w-full mt-4')

        # ここに generate_ai_advice 関数を定義
        async def generate_ai_advice():
            # シンプルなローディング通知
            ui.notify('🧠 AI分析中... お待ちください', type='ongoing')
            
            access_token = app.storage.user.get('access_token')
            if not access_token:
                ui.notify('ログインしていません。', type='negative')
                ui.navigate.to('/login')
                return

            water_data = {
                "ph": ph_input.value,
                "kh": kh_input.value,
                "gh": gh_input.value,
                "no2": no2_input.value,
                "no3": no3_input.value,
                "cl2": cl2_input.value,
            }
            advice_data = {
                "water_data": water_data,
                "notes": notes_input.value,
                "fish_type": fish_type_input.value,
                "tank_type": tank_type_input.value,
            }

            try:
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                # 非同期でAPIリクエストを実行（Connection lost対策）
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(f"{DJANGO_API_BASE_URL}/generate-advice/", headers=headers, json=advice_data, timeout=60)
                )
                response.raise_for_status()

                advice_result = response.json()
                advice_text = advice_result.get('advice', 'アドバイスを生成できませんでした。')
                
                # アドバイス完了通知
                ui.notify('✅ AIアドバイス生成完了！', type='positive')

                with ui.dialog() as advice_dialog:
                    with ui.card().classes('w-full max-w-2xl q-pa-md'):
                        ui.label('AIアドバイス').classes('text-h6 text-primary mb-4')
                        ui.markdown(advice_text).classes('whitespace-pre-wrap q-mb-md')
                        ui.button('閉じる', on_click=advice_dialog.close).classes('w-full')
                advice_dialog.open()

            except requests.exceptions.RequestException as e:
                error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                ui.notify(f'❌ AIアドバイス生成失敗: {error_message}', type='negative')
            except Exception as e:
                ui.notify(f'❌ 予期せぬエラーが発生しました: {e}', type='negative')

        ui.label('水質試験紙をアップロードして自動入力').classes('text-md font-semibold mt-4 mb-2')
        
        # ここに handle_image_upload 関数を定義
        async def handle_image_upload(e):
            print("=== 画像アップロード開始 ===")
            print(f"Event object: {e}")
            print(f"Event attributes: {dir(e)}")
            print(f"File name: {e.name if hasattr(e, 'name') else 'No name attribute'}")
            print(f"File type: {e.type if hasattr(e, 'type') else 'No type attribute'}")
            
            access_token = app.storage.user.get('access_token')
            print(f"Access token exists: {bool(access_token)}")
            
            if not access_token:
                ui.notify('ログインしていません。', type='negative')
                ui.navigate.to('/login')
                return

            if not hasattr(e, 'name') or not e.name:
                print("No file name found in upload event")
                ui.notify('ファイルが選択されていません。', type='negative')
                return

            print(f"Uploaded file: {e.name}, type: {getattr(e, 'type', 'unknown')}")
            
            dialog = ui.dialog().props('persistent')
            with dialog:
                with ui.card().classes('items-center'):
                    ui.spinner(size='xl', thickness=10).classes('text-blue-500')
                    ui.label('画像を解析中...').classes('text-lg mt-4')
            dialog.open()

            try:
                print("=== 画像データ読み込み開始 ===")
                image_bytes = e.content.read() 
                print(f"Image bytes length: {len(image_bytes)}")
                
                files = {'image': (e.name, image_bytes, getattr(e, 'type', 'image/jpeg'))}
                headers = {'Authorization': f'Bearer {access_token}'}
                api_url = f"{DJANGO_API_BASE_URL}/analyze-image/"
                
                print(f"API URL: {api_url}")
                print(f"Headers: {headers}")
                print("=== APIリクエスト送信 ===")
                
                response = requests.post(api_url, headers=headers, files=files)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Raw response content: {response.text[:500]}...")
                
                response.raise_for_status()

                analysis_result = response.json()
                water_data_from_image = analysis_result.get('water_data', {})
                
                # デバッグ情報をコンソールに出力
                print(f"Analysis result: {analysis_result}")
                print(f"Water data from image: {water_data_from_image}")

                # フォームフィールドを更新（複数の手法を試す）
                updated_fields = []
                if 'ph' in water_data_from_image and water_data_from_image['ph'] is not None:
                    value = float(water_data_from_image['ph'])
                    ph_input.value = value
                    ph_input.set_value(value)
                    ph_input.update()
                    updated_fields.append(f"pH: {value}")
                if 'kh' in water_data_from_image and water_data_from_image['kh'] is not None:
                    value = float(water_data_from_image['kh'])
                    kh_input.value = value
                    kh_input.set_value(value)
                    kh_input.update()
                    updated_fields.append(f"KH: {value}")
                if 'gh' in water_data_from_image and water_data_from_image['gh'] is not None:
                    value = float(water_data_from_image['gh'])
                    gh_input.value = value
                    gh_input.set_value(value)
                    gh_input.update()
                    updated_fields.append(f"GH: {value}")
                if 'no2' in water_data_from_image and water_data_from_image['no2'] is not None:
                    value = float(water_data_from_image['no2'])
                    no2_input.value = value
                    no2_input.set_value(value)
                    no2_input.update()
                    updated_fields.append(f"NO2: {value}")
                if 'no3' in water_data_from_image and water_data_from_image['no3'] is not None:
                    value = float(water_data_from_image['no3'])
                    no3_input.value = value
                    no3_input.set_value(value)
                    no3_input.update()
                    updated_fields.append(f"NO3: {value}")
                if 'cl2' in water_data_from_image and water_data_from_image['cl2'] is not None:
                    value = float(water_data_from_image['cl2'])
                    cl2_input.value = value
                    cl2_input.set_value(value)
                    cl2_input.update()
                    updated_fields.append(f"Cl2: {value}")
                
                # 強制的にフォームを再描画
                ui.run_javascript('document.querySelectorAll("input").forEach(input => input.dispatchEvent(new Event("input")))')
                
                if updated_fields:
                    ui.notify(f'更新されたフィールド: {", ".join(updated_fields)}', type='info')
                    ui.notify('画像から水質データを自動入力しました！', type='positive')
                else:
                    ui.notify('画像から水質データを抽出できませんでした', type='warning')

                ui.notify('画像から水質データを自動入力しました！', type='positive')

            except requests.exceptions.RequestException as e:
                print(f"=== APIリクエストエラー ===")
                print(f"Request exception: {e}")
                if 'response' in locals():
                    print(f"Response status: {response.status_code}")
                    print(f"Response text: {response.text}")
                dialog.close()
                error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                ui.notify(f'画像解析失敗: {error_message}', type='negative')
                print(f"Error message shown: {error_message}")
            except Exception as e:
                print(f"=== 予期せぬエラー ===")
                print(f"Exception: {e}")
                print(f"Exception type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')
            finally:
                dialog.close()
                print("=== 画像アップロード処理終了 ===")
                print("--- --- --- --- --- --- ---")

        ui.upload(label='画像をアップロード', on_upload=handle_image_upload, auto_upload=True, max_file_size=5_000_000, max_files=1).classes('w-full')
        ui.label('推奨: JPEG/PNG形式, 最大5MB').classes('text-sm text-gray-500')

        ui.separator().classes('my-6')

        
        # 保存ボタン
        async def save_log_entry():
            # 入力されたデータを集める
            water_data = {
                "ph": ph_input.value,
                "kh": kh_input.value,
                "gh": gh_input.value,
                "no2": no2_input.value,
                "no3": no3_input.value,
                "cl2": cl2_input.value,
            }
            log_data = {
                "water_data": water_data,
                "fish_type": fish_type_input.value,
                "tank_type": tank_type_input.value,
                "notes": notes_input.value,
            }

            access_token = app.storage.user.get('access_token')
            if not access_token:
                ui.notify('ログインしていません。', type='negative')
                ui.navigate.to('/login')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(f"{DJANGO_API_BASE_URL}/logs/", headers=headers, json=log_data)
                response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる

                ui.notify('飼育ログが正常に保存されました！', type='positive')
                ui.navigate.to('/logs') # ログ一覧ページに戻る
            except requests.exceptions.RequestException as e:
                error_response = response.json() if hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                # tank_type のバリデーションエラーを抽出して表示
                if 'tank_type' in error_response:
                    error_message = f"水槽の種類エラー: {error_response['tank_type'][0]}"
                ui.notify(f'飼育ログの保存に失敗しました: {error_message}', type='negative')
            except Exception as e:
                ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')


        ai_advice_button = ui.button('AIアドバイスを生成', icon='psychology', on_click=generate_ai_advice).classes('px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700 w-full mb-4')
        
        ui.button('飼育ログを保存', icon='save', on_click=save_log_entry).classes('px-6 py-3 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-700 w-full mb-4')
        
        ui.button('キャンセル', on_click=lambda: ui.navigate.to('/logs')).props('flat color=grey').classes('w-full mt-4')


# 水質解析ページ (placeholder) - 後で統合
@ui.page('/analyze')
def analyze_page():
    create_common_layout()
    with ui.column().classes('q-pa-md w-full'):
        ui.label('水質解析').classes('text-h5 text-primary q-mb-md')
        ui.label('この機能は飼育ログの新規作成・編集ページに統合されます。').classes('text-grey-6')
        ui.label('直接アクセスすることはあまりありません。').classes('text-grey-6')


# 飼育ログ削除機能
async def delete_log_entry(log_id: int):
    # 削除確認のダイアログを表示
    if not await ui.run_javascript(f'confirm("ID: {log_id} の飼育ログを本当に削除しますか？");', timeout=None):
        return # ユーザーがキャンセルした場合

    access_token = app.storage.user.get('access_token')
    if not access_token:
        ui.notify('ログインしていません。', type='negative')
        ui.navigate.to('/login')
        return

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.delete(f"{DJANGO_API_BASE_URL}/logs/{log_id}/", headers=headers)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる

        ui.notify(f'飼育ログ (ID: {log_id}) を削除しました！', type='positive')
        ui.navigate.to('/logs') # 削除後、一覧ページを再読み込み
    except requests.exceptions.RequestException as e:
        error_detail = response.json() if hasattr(response, 'json') else str(e)
        ui.notify(f'飼育ログの削除に失敗しました: {error_detail}', type='negative')
    except Exception as e:
        ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')



# AIアドバイスページ - 最新ログによるアドバイス表示
@ui.page('/advice')
async def advice_page():
    create_common_layout()
    
    # 認証チェック
    if not app.storage.user.get('access_token'):
        ui.notify('ログインしてください。', type='negative')
        ui.navigate.to('/login')
        return

    ui.add_head_html('<title>AIアドバイス - AquaFlux</title>')
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-6'):
        ui.label('🤖 AIアドバイス').classes('text-3xl font-bold mb-6 text-center w-full text-primary')
        ui.label('最新の飼育ログデータに基づいてAIがアドバイスを提供します').classes('text-lg text-center mb-8 text-gray-600')
        
        advice_container = ui.column().classes('w-full')

        async def fetch_latest_log_and_advice():
            with advice_container:
                ui.spinner(size='lg').classes('mx-auto')
                ui.label('最新の飼育ログを確認中...').classes('text-lg text-gray-500 mt-4 text-center')

            advice_container.clear()

            access_token = app.storage.user.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}

            try:
                # 最新のログを取得
                response = requests.get(f"{DJANGO_API_BASE_URL}/logs/", headers=headers)
                response.raise_for_status()
                logs = response.json()

                if not logs:
                    # ログがない場合のメッセージ
                    with advice_container:
                        with ui.card().classes('w-full p-8 text-center bg-gray-50'):
                            ui.icon('info', size='3rem').classes('text-blue-500 mb-4')
                            ui.label('飼育ログがまだありません').classes('text-2xl font-bold mb-4')
                            ui.label('AIアドバイスを受けるには、まず飼育ログを作成してください。').classes('text-lg mb-6 text-gray-600')
                            ui.button('飼育ログを作成', icon='add', on_click=lambda: ui.navigate.to('/logs/new')).classes('px-8 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700')
                    return

                # 最新ログでAIアドバイスを生成
                latest_log = logs[0]
                advice_data = {
                    "water_data": latest_log.get('water_data', {}),
                    "notes": latest_log.get('notes', ''),
                    "fish_type": latest_log.get('fish_type', ''),
                    "tank_type": latest_log.get('tank_type', 'freshwater'),
                }

                with advice_container:
                    # 最新ログ情報表示
                    with ui.card().classes('w-full p-6 mb-6 bg-blue-50'):
                        ui.label('📊 参照している飼育ログ').classes('text-xl font-bold mb-4 text-blue-800')
                        ui.label(f'日付: {latest_log.get("log_date", "N/A")}').classes('text-lg mb-2')
                        ui.label(f'魚種: {latest_log.get("fish_type", "未設定")}').classes('text-lg mb-2')
                        ui.label(f'水槽: {latest_log.get("tank_type", "淡水")}').classes('text-lg mb-2')
                        
                        water_data = latest_log.get('water_data', {})
                        if water_data:
                            water_info = []
                            for key, value in water_data.items():
                                if value is not None:
                                    water_info.append(f"{key.upper()}: {value}")
                            if water_info:
                                ui.label(f'水質: {", ".join(water_info)}').classes('text-lg')

                    # AIアドバイス生成中表示
                    with ui.card().classes('w-full p-6 text-center') as advice_card:
                        ui.spinner(size='xl', thickness=10).classes('text-purple-500 mb-4')
                        ui.label('🧠 AI が分析中...').classes('text-xl font-bold mb-2')
                        ui.label('水質データと過去の履歴を分析してアドバイスを生成しています').classes('text-gray-600')

                # AIアドバイス生成
                try:
                    response = requests.post(f"{DJANGO_API_BASE_URL}/generate-advice/", headers=headers, json=advice_data)
                    response.raise_for_status()

                    advice_result = response.json()
                    advice_text = advice_result.get('advice', 'アドバイスを生成できませんでした。')
                    
                    # アドバイス表示に切り替え
                    advice_card.clear()
                    with advice_card:
                        ui.label('🤖 AIアドバイス').classes('text-2xl font-bold mb-4 text-purple-700')
                        ui.markdown(advice_text).classes('text-lg whitespace-pre-wrap mb-6')
                        
                        with ui.row().classes('justify-center gap-4'):
                            ui.button('新しいログを作成', icon='add', on_click=lambda: ui.navigate.to('/logs/new')).classes('px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700')
                            ui.button('ログ一覧を見る', icon='list', on_click=lambda: ui.navigate.to('/logs')).classes('px-6 py-3 bg-gray-600 text-white rounded-lg shadow-md hover:bg-gray-700')

                except requests.exceptions.RequestException as e:
                    advice_card.clear()
                    with advice_card:
                        ui.icon('error', size='3rem').classes('text-red-500 mb-4')
                        ui.label('アドバイス生成に失敗しました').classes('text-xl font-bold mb-4 text-red-600')
                        error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                        error_message = error_response.get('detail', str(e))
                        ui.label(f'エラー: {error_message}').classes('text-gray-600 mb-4')
                        ui.button('再試行', icon='refresh', on_click=fetch_latest_log_and_advice).classes('px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700')

            except requests.exceptions.RequestException as e:
                advice_container.clear()
                with advice_container:
                    with ui.card().classes('w-full p-6 text-center'):
                        ui.icon('error', size='3rem').classes('text-red-500 mb-4')
                        ui.label('データの取得に失敗しました').classes('text-xl font-bold mb-4 text-red-600')
                        ui.label(f'エラー: {e}').classes('text-gray-600 mb-4')
                        ui.button('再試行', icon='refresh', on_click=fetch_latest_log_and_advice).classes('px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700')

        ui.timer(0.1, fetch_latest_log_and_advice, once=True)


# 飼育ログ詳細ページ
@ui.page('/logs/{log_id}') # パスパラメータとしてログIDを受け取る
async def log_detail_page(log_id: int):
    create_common_layout()

    # 認証チェック
    if not app.storage.user.get('access_token'):
        ui.notify('ログインしてください。', type='negative')
        ui.navigate.to('/login')
        return

    ui.add_head_html(f'<title>飼育ログ詳細 (ID: {log_id}) - AquaFlux</title>')
    ui.label(f'飼育ログ詳細 (ID: {log_id})').classes('text-3xl font-bold mb-6 text-center w-full')

    # 詳細情報を表示するコンテナ
    detail_container = ui.column().classes('w-3/4 max-w-2xl mx-auto p-6 shadow-xl rounded-lg bg-white')

    async def fetch_log_detail():
        with detail_container:
            ui.spinner(size='lg').classes('absolute-center')
            ui.label('ログ詳細をロード中...').classes('text-lg text-gray-500 mt-4')

        detail_container.clear() # 既存の内容をクリア

        access_token = app.storage.user.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get(f"{DJANGO_API_BASE_URL}/logs/{log_id}/", headers=headers)
            response.raise_for_status() 

            log_data = response.json()

            with detail_container:
                ui.label(f'日付: {log_data.get("log_date", "N/A")}').classes('text-lg font-semibold')
                ui.label(f'魚の種類: {log_data.get("fish_type", "N/A")}').classes('text-lg')
                ui.label(f'水槽の種類: {log_data.get("tank_type", "N/A")}').classes('text-lg')

                ui.separator().classes('my-4')
                ui.label('水質データ').classes('text-xl font-bold text-primary mb-2')
                water_data = log_data.get('water_data', {})
                if water_data:
                    ui.label(f'pH: {water_data.get("ph", "N/A")}').classes('text-md')
                    ui.label(f'KH: {water_data.get("kh", "N/A")}').classes('text-md')
                    ui.label(f'GH: {water_data.get("gh", "N/A")}').classes('text-md')
                    ui.label(f'NO2 (亜硝酸): {water_data.get("no2", "N/A")}').classes('text-md')
                    ui.label(f'NO3 (硝酸): {water_data.get("no3", "N/A")}').classes('text-md')
                    ui.label(f'Cl2 (塩素): {water_data.get("cl2", "N/A")}').classes('text-md')
                else:
                    ui.label('水質データはありません。').classes('text-md text-gray-500')

                ui.separator().classes('my-4')
                ui.label('メモ').classes('text-xl font-bold text-primary mb-2')
                ui.label(log_data.get('notes', 'なし')).classes('text-md whitespace-pre-wrap') # 改行を保持

                ui.separator().classes('my-6')
                
                # AIアドバイス機能
                ui.label('このデータのAIアドバイス').classes('text-xl font-bold text-primary mb-2')
                
                async def generate_ai_advice_detail():
                    ui.notify('AIアドバイス生成を開始します', type='info')
                    
                    access_token = app.storage.user.get('access_token')
                    if not access_token:
                        ui.notify('ログインしていません。', type='negative')
                        ui.navigate.to('/login')
                        return

                    # ログデータからアドバイス生成データを作成
                    advice_data = {
                        "water_data": water_data,
                        "notes": log_data.get('notes', ''),
                        "fish_type": log_data.get('fish_type', ''),
                        "tank_type": log_data.get('tank_type', 'freshwater'),
                    }

                    # ローディング表示
                    dialog = ui.dialog().props('persistent')
                    with dialog:
                        with ui.card().classes('items-center'):
                            ui.spinner(size='xl', thickness=10).classes('text-blue-500')
                            ui.label('AIアドバイスを生成中...').classes('text-lg mt-4')
                    dialog.open()

                    try:
                        headers = {
                            'Authorization': f'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }
                        response = requests.post(f"{DJANGO_API_BASE_URL}/generate-advice/", headers=headers, json=advice_data)
                        response.raise_for_status()

                        advice_result = response.json()
                        advice_text = advice_result.get('advice', 'アドバイスを生成できませんでした。')
                        
                        dialog.close()

                        # 新しいダイアログでアドバイスを表示
                        with ui.dialog() as advice_dialog:
                            with ui.card().classes('w-full max-w-2xl q-pa-md'):
                                ui.label('AIアドバイス').classes('text-h6 text-primary mb-4')
                                ui.markdown(advice_text).classes('whitespace-pre-wrap q-mb-md')
                                ui.button('閉じる', on_click=advice_dialog.close).classes('w-full')
                        advice_dialog.open()

                    except requests.exceptions.RequestException as e:
                        dialog.close()
                        error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                        error_message = error_response.get('detail', str(e))
                        ui.notify(f'AIアドバイス生成失敗: {error_message}', type='negative')
                        if "API key" in error_message or "API_KEY" in error_message:
                            ui.notify("Gemini APIキーが正しく設定されているか確認してください。", type='negative', timeout=5000)
                    except Exception as e:
                        dialog.close()
                        ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')

                ui.button('AIアドバイスを生成', icon='psychology', on_click=generate_ai_advice_detail).classes('px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700 w-full mb-4')
                
                ui.separator().classes('my-6')
                
                with ui.row().classes('w-full justify-center gap-4'):
                    ui.button('編集', icon='edit', on_click=lambda: ui.navigate.to(f'/logs/{log_id}/edit')).classes('px-6 py-3 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700')
                    ui.button('削除', icon='delete', on_click=lambda: delete_log_entry(log_id)).classes('px-6 py-3 bg-red-600 text-white rounded-lg shadow-md hover:bg-red-700')
                    ui.button('一覧に戻る', on_click=lambda: ui.navigate.to('/logs')).props('flat color=grey').classes('q-ml-md')

        except requests.exceptions.RequestException as e:
            ui.notify(f'飼育ログ詳細の取得に失敗しました: {e}', type='negative')
            with detail_container:
                detail_container.clear()
                ui.label('ログ詳細の読み込み中にエラーが発生しました。').classes('text-negative text-lg')
        except Exception as e:
            ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')
            with detail_container:
                detail_container.clear()
                ui.label('予期せぬエラーが発生しました。').classes('text-negative text-lg')

    ui.timer(0.1, fetch_log_detail, once=True) # ページ表示後に非同期でロード



# ログインページ
@ui.page('/login')
def login_page():
    create_common_layout()
    with ui.column().classes('absolute-center items-center q-pa-md login-card'):
        ui.label('ログイン').classes('text-h5 text-primary q-mb-lg')
        
        username_input = ui.input('ユーザー名', placeholder='ユーザー名を入力').props('outlined').classes('w-64 q-mb-sm')
        password_input = ui.input('パスワード', placeholder='パスワードを入力', password=True, password_toggle_button=True).props('outlined').classes('w-64 q-mb-lg')
        
        ui.button('ログイン', on_click=lambda: login_user(username_input.value, password_input.value)).classes('bg-primary text-white w-64 q-py-sm')
        ui.label('アカウントをお持ちでないですか？').classes('text-caption q-mt-md')
        ui.link('新規登録はこちら', '/register')

# ユーザー登録ページ
@ui.page('/register')
def register_page():
    create_common_layout()
    with ui.column().classes('absolute-center items-center q-pa-md register-card'):
        ui.label('新規ユーザー登録').classes('text-h5 text-primary q-mb-lg')
        
        username_input = ui.input('ユーザー名', placeholder='ユーザー名を入力').props('outlined').classes('w-64 q-mb-sm')
        email_input = ui.input('メールアドレス', placeholder='メールアドレスを入力', validation={'メールアドレスは必須です': lambda v: bool(v)}).props('outlined').classes('w-64 q-mb-sm')
        password_input = ui.input('パスワード', placeholder='パスワードを入力', password=True, password_toggle_button=True).props('outlined').classes('w-64 q-mb-sm')
        password_confirm_input = ui.input('パスワード（確認）', placeholder='パスワードを再入力', password=True, password_toggle_button=True).props('outlined').classes('w-64 q-mb-lg')
        
        ui.button('登録', on_click=lambda: register_user(
            username_input.value,
            password_input.value,
            password_confirm_input.value,
            email_input.value
        )).classes('bg-primary text-white w-64 q-py-sm')
        
        ui.label('すでにアカウントをお持ちですか？').classes('text-caption q-mt-md')
        ui.link('ログインはこちら', '/login')


# 飼育ログ編集ページ
@ui.page('/logs/{log_id}/edit')
@auth_protected
async def edit_log_entry_page(log_id: int):
    create_common_layout()

    access_token = app.storage.user.get('access_token')
    if not access_token:
        ui.notify('ログインしていません。', type='negative')
        ui.navigate.to('/login')
        return

    with ui.header().classes('items-center justify-between text-white bg-blue-600 p-4'):
        ui.label(f'飼育ログ編集 (ID: {log_id})').classes('text-2xl font-bold')
        with ui.row():
            ui.button('ホームへ', on_click=lambda: ui.navigate.to('/')).props('flat color=white icon=home')
            ui.button('ログ一覧', on_click=lambda: ui.navigate.to('/logs')).props('flat color=white icon=list')
            ui.button('ログ詳細', on_click=lambda: ui.navigate.to(f'/logs/{log_id}')).props('flat color=white icon=info')
            ui.button('ログアウト', on_click=logout).props('flat color=white icon=logout')

    with ui.card().classes('w-full max-w-2xl mx-auto my-8 p-6 shadow-xl rounded-lg'):
        # UI入力コンポーネントの定義
        with ui.grid(columns=2).classes('w-full gap-4'):
            ph_input = ui.number('pH').props('step=0.1 min=0 max=14').classes('w-full')
            kh_input = ui.number('KH (炭酸塩硬度)').props('min=0 max=20').classes('w-full')
            gh_input = ui.number('GH (総硬度)').props('min=0 max=30').classes('w-full')
            no2_input = ui.number('NO2 (亜硝酸塩)').props('step=0.1 min=0 max=10').classes('w-full')
            no3_input = ui.number('NO3 (硝酸塩)').props('min=0 max=100').classes('w-full')
            cl2_input = ui.number('Cl2 (塩素)').props('step=0.1 min=0 max=5').classes('w-full')
        
        notes_input = ui.textarea('メモ').classes('w-full mt-4').props('rows=3')
        fish_type_input = ui.input('魚種 (例: ネオンテトラ)').classes('w-full mt-4')
        
        tank_type_options_map = {
            'freshwater': '淡水',
            'saltwater': '海水',
        }
        tank_type_input = ui.select(options=tank_type_options_map, label='水槽の種類').classes('w-full mt-4')

        # ログデータのロード
        async def load_log_data():
            try:
                headers = {'Authorization': f'Bearer {access_token}'}
                response = requests.get(f"{DJANGO_API_BASE_URL}/logs/{log_id}/", headers=headers)
                response.raise_for_status()
                log_data = response.json()

                # フォームにデータを設定
                water_data = log_data.get('water_data', {})
                ph_input.value = water_data.get('ph')
                kh_input.value = water_data.get('kh')
                gh_input.value = water_data.get('gh')
                no2_input.value = water_data.get('no2')
                no3_input.value = water_data.get('no3')
                cl2_input.value = water_data.get('cl2')
                notes_input.value = log_data.get('notes')
                fish_type_input.value = log_data.get('fish_type')
                tank_type_input.value = log_data.get('tank_type')

            except requests.exceptions.RequestException as e:
                ui.notify(f'ログデータのロードに失敗しました: {e}', type='negative')
                ui.navigate.to('/logs')
            except Exception as e:
                ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')
                ui.navigate.to('/logs')

        await load_log_data()

        # 画像アップロード機能
        ui.label('水質試験紙をアップロードして自動入力').classes('text-md font-semibold mt-4 mb-2')
        
        async def handle_image_upload(e):
            print("=== 画像アップロード開始 ===")
            print(f"Event object: {e}")
            print(f"Event attributes: {dir(e)}")
            print(f"File name: {e.name if hasattr(e, 'name') else 'No name attribute'}")
            print(f"File type: {e.type if hasattr(e, 'type') else 'No type attribute'}")
            
            access_token = app.storage.user.get('access_token')
            print(f"Access token exists: {bool(access_token)}")
            
            if not access_token:
                ui.notify('ログインしていません。', type='negative')
                ui.navigate.to('/login')
                return

            if not hasattr(e, 'name') or not e.name:
                print("No file name found in upload event")
                ui.notify('ファイルが選択されていません。', type='negative')
                return

            print(f"Uploaded file: {e.name}, type: {getattr(e, 'type', 'unknown')}")
            
            dialog = ui.dialog().props('persistent')
            with dialog:
                with ui.card().classes('items-center'):
                    ui.spinner(size='xl', thickness=10).classes('text-blue-500')
                    ui.label('画像を解析中...').classes('text-lg mt-4')
            dialog.open()

            try:
                print("=== 画像データ読み込み開始 ===")
                image_bytes = e.content.read() 
                print(f"Image bytes length: {len(image_bytes)}")
                
                files = {'image': (e.name, image_bytes, getattr(e, 'type', 'image/jpeg'))}
                headers = {'Authorization': f'Bearer {access_token}'}
                api_url = f"{DJANGO_API_BASE_URL}/analyze-image/"
                
                print(f"API URL: {api_url}")
                print(f"Headers: {headers}")
                print("=== APIリクエスト送信 ===")
                
                response = requests.post(api_url, headers=headers, files=files)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Raw response content: {response.text[:500]}...")
                
                response.raise_for_status()

                analysis_result = response.json()
                water_data_from_image = analysis_result.get('water_data', {})
                
                # デバッグ情報をコンソールに出力
                print(f"Analysis result: {analysis_result}")
                print(f"Water data from image: {water_data_from_image}")

                # フォームフィールドを更新（複数の手法を試す）
                updated_fields = []
                if 'ph' in water_data_from_image and water_data_from_image['ph'] is not None:
                    value = float(water_data_from_image['ph'])
                    ph_input.value = value
                    ph_input.set_value(value)
                    ph_input.update()
                    updated_fields.append(f"pH: {value}")
                if 'kh' in water_data_from_image and water_data_from_image['kh'] is not None:
                    value = float(water_data_from_image['kh'])
                    kh_input.value = value
                    kh_input.set_value(value)
                    kh_input.update()
                    updated_fields.append(f"KH: {value}")
                if 'gh' in water_data_from_image and water_data_from_image['gh'] is not None:
                    value = float(water_data_from_image['gh'])
                    gh_input.value = value
                    gh_input.set_value(value)
                    gh_input.update()
                    updated_fields.append(f"GH: {value}")
                if 'no2' in water_data_from_image and water_data_from_image['no2'] is not None:
                    value = float(water_data_from_image['no2'])
                    no2_input.value = value
                    no2_input.set_value(value)
                    no2_input.update()
                    updated_fields.append(f"NO2: {value}")
                if 'no3' in water_data_from_image and water_data_from_image['no3'] is not None:
                    value = float(water_data_from_image['no3'])
                    no3_input.value = value
                    no3_input.set_value(value)
                    no3_input.update()
                    updated_fields.append(f"NO3: {value}")
                if 'cl2' in water_data_from_image and water_data_from_image['cl2'] is not None:
                    value = float(water_data_from_image['cl2'])
                    cl2_input.value = value
                    cl2_input.set_value(value)
                    cl2_input.update()
                    updated_fields.append(f"Cl2: {value}")
                
                # 強制的にフォームを再描画
                ui.run_javascript('document.querySelectorAll("input").forEach(input => input.dispatchEvent(new Event("input")))')
                
                if updated_fields:
                    ui.notify(f'更新されたフィールド: {", ".join(updated_fields)}', type='info')
                    ui.notify('画像から水質データを自動入力しました！', type='positive')
                else:
                    ui.notify('画像から水質データを抽出できませんでした', type='warning')

                ui.notify('画像から水質データを自動入力しました！', type='positive')

            except requests.exceptions.RequestException as e:
                print(f"=== APIリクエストエラー ===")
                print(f"Request exception: {e}")
                if 'response' in locals():
                    print(f"Response status: {response.status_code}")
                    print(f"Response text: {response.text}")
                dialog.close()
                error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                ui.notify(f'画像解析失敗: {error_message}', type='negative')
                print(f"Error message shown: {error_message}")
            except Exception as e:
                print(f"=== 予期せぬエラー ===")
                print(f"Exception: {e}")
                print(f"Exception type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')
            finally:
                dialog.close()
                print("=== 画像アップロード処理終了 ===")
                print("--- --- --- --- --- --- ---")

        ui.upload(label='画像をアップロード', on_upload=handle_image_upload, auto_upload=True, max_file_size=5_000_000, max_files=1).classes('w-full')
        ui.label('推奨: JPEG/PNG形式, 最大5MB').classes('text-sm text-gray-500')

        ui.separator().classes('my-6')

        # AIアドバイス機能
        ui.label('AIアドバイス').classes('text-lg font-semibold mb-4 text-primary')
        
        async def generate_ai_advice_edit():
            ui.notify('AIアドバイス生成を開始します', type='info')
            
            access_token = app.storage.user.get('access_token')
            if not access_token:
                ui.notify('ログインしていません。', type='negative')
                ui.navigate.to('/login')
                return

            # AIアドバイス生成に必要なデータをフォームから収集
            water_data = {
                "ph": ph_input.value,
                "kh": kh_input.value,
                "gh": gh_input.value,
                "no2": no2_input.value,
                "no3": no3_input.value,
                "cl2": cl2_input.value,
            }
            advice_data = {
                "water_data": water_data,
                "notes": notes_input.value,
                "fish_type": fish_type_input.value,
                "tank_type": tank_type_input.value,
            }

            # AI思考中のローディング表示（強化版）
            dialog = ui.dialog().props('persistent no-backdrop-dismiss')
            with dialog:
                with ui.card().classes('items-center p-8 min-w-96 text-center'):
                    ui.spinner(size='xl', thickness=10).classes('text-purple-500 mb-6')
                    ui.label('🧠 AI が深く分析中...').classes('text-2xl font-bold mb-3 text-purple-700')
                    ui.label('水質データと過去の履歴を総合的に分析しています').classes('text-lg text-gray-600 mb-2')
                    ui.label('しばらくお待ちください...').classes('text-sm text-gray-500')
                    ui.linear_progress().classes('w-full mt-4').props('indeterminate color=purple')
            dialog.open()

            try:
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                # 非同期でAPIリクエストを実行（Connection lost対策）
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(f"{DJANGO_API_BASE_URL}/generate-advice/", headers=headers, json=advice_data, timeout=60)
                )
                response.raise_for_status()

                advice_result = response.json()
                advice_text = advice_result.get('advice', 'アドバイスを生成できませんでした。')
                
                # アドバイス完了通知
                ui.notify('✅ AIアドバイス生成完了！', type='positive')

                # 新しいダイアログでアドバイスを表示
                with ui.dialog() as advice_dialog:
                    with ui.card().classes('w-full max-w-2xl q-pa-md'):
                        ui.label('AIアドバイス').classes('text-h6 text-primary mb-4')
                        ui.markdown(advice_text).classes('whitespace-pre-wrap q-mb-md')
                        ui.button('閉じる', on_click=advice_dialog.close).classes('w-full')
                advice_dialog.open()

            except requests.exceptions.RequestException as e:
                error_response = response.json() if 'response' in locals() and hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                ui.notify(f'❌ AIアドバイス生成失敗: {error_message}', type='negative')
                if "API key" in error_message or "API_KEY" in error_message:
                    ui.notify("Gemini APIキーが正しく設定されているか確認してください。", type='negative', timeout=5000)
            except Exception as e:
                ui.notify(f'❌ 予期せぬエラーが発生しました: {e}', type='negative')

        ui.button('AIアドバイスを生成', icon='psychology', on_click=generate_ai_advice_edit).classes('px-6 py-3 bg-purple-600 text-white rounded-lg shadow-md hover:bg-purple-700 w-full mb-4')

        ui.separator().classes('my-6')

        # 更新ボタン
        async def update_log_entry():
            water_data = {
                "ph": ph_input.value,
                "kh": kh_input.value,
                "gh": gh_input.value,
                "no2": no2_input.value,
                "no3": no3_input.value,
                "cl2": cl2_input.value,
            }
            updated_log_data = {
                "water_data": water_data,
                "fish_type": fish_type_input.value,
                "tank_type": tank_type_input.value,
                "notes": notes_input.value,
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            try:
                response = requests.put(f"{DJANGO_API_BASE_URL}/logs/{log_id}/", headers=headers, json=updated_log_data)
                response.raise_for_status()

                ui.notify('飼育ログを更新しました！', type='positive')
                ui.navigate.to(f'/logs/{log_id}')
            except requests.exceptions.RequestException as e:
                error_response = response.json() if hasattr(response, 'json') else {}
                error_message = error_response.get('detail', str(e))
                if 'tank_type' in error_response:
                    error_message = f"水槽の種類エラー: {error_response['tank_type'][0]}"
                ui.notify(f'飼育ログの更新に失敗しました: {error_message}', type='negative')
            except Exception as e:
                ui.notify(f'予期せぬエラーが発生しました: {e}', type='negative')

        ui.button('飼育ログを更新', icon='update', on_click=update_log_entry).classes('px-6 py-3 bg-green-600 text-white rounded-lg shadow-md hover:bg-green-700 w-full mb-4')
        ui.button('キャンセル', on_click=lambda: ui.navigate.to(f'/logs/{log_id}')).props('flat color=grey').classes('w-full mt-4')


# アプリケーションの実行設定
if __name__ in {"__main__", "__mp_main__"}:
    ui.colors.primary = '#42A5F5'
    ui.colors.secondary = '#29B6F6'
    ui.colors.accent = '#26C6DA'
    ui.colors.positive = '#66BB6A'
    ui.colors.negative = '#EF5350'
    ui.colors.info = '#2196F3'
    ui.colors.warning = '#FFCA28'

    ui.run(
        title='AQUAFLUX',
        port=8001,
        dark=False,
        reload=True,
        tailwind=True,
        storage_secret=os.environ.get("NICEGUI_STORAGE_SECRET", "super_secret_key_for_nicegui"),
    )