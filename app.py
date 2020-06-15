# ------------------------------------------------------------------------------
# モジュールのインポート
# ------------------------------------------------------------------------------
# 標準モジュール
import os
import re
import json
import logging

# サードパーティ製モジュール
import boto3
from chalice import Chalice, Response
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
from linebot.exceptions import InvalidSignatureError

# ------------------------------------------------------------------------------
# 前処理
# ------------------------------------------------------------------------------
# boto3 Settings.
rekognition = boto3.client('rekognition')

# Chalice Settings.
app = Chalice(app_name='line-bot-rekognition-python')

# LINE Settings.
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

# Enable DEBUG logs.
app.log.setLevel(logging.DEBUG)

# ------------------------------------------------------------------------------
# 関数
# ------------------------------------------------------------------------------
def get_rekognition_sorce_file(image_file_path):

    # rekognitionに画像を送信し結果を得る
    with open(image_file_path, 'rb') as f:
        response = rekognition.detect_faces(
            Image={'Bytes': f.read()},
            Attributes=['ALL']
        )
    app.log.info('detect_faces: %s', response)

    # emotions配列解析用関数
    def _get_emotions(e_type, items):
        con = [j['Confidence'] for j in items if j['Type'] == e_type]
        return con[0] if con else None


    text_list = []
    text = ''
    for i in response['FaceDetails']:
        # 区切り行
        text_list.append('-------------')

        # 推定年齢
        age_lange_low = i['AgeRange']['Low']
        age_lange_high = i['AgeRange']['High']
        text_list.append('推定年齢:{}〜{}歳'.format(age_lange_low, age_lange_high))

        # スマイル
        smile_title = i['Smile']['Value']
        smile_con = i['Smile']['Confidence']
        text_list.append\
          ('スマイル率:{}%'.format(round(smile_con if smile_title else 100 - smile_con), 2))

        # 感情値
        emotions = i['Emotions']
        happy_con = round(_get_emotions('HAPPY', emotions), 2)
        text_list.append('喜び率:{}%'.format(happy_con))
        angry_con = round(_get_emotions('ANGRY', emotions), 2)
        text_list.append('怒り率:{}%'.format(angry_con))
        sad_con = round(_get_emotions('SAD', emotions), 2)
        text_list.append('悲しみ率:{}%'.format(sad_con))
        calm_con = round(_get_emotions('CALM', emotions), 2)
        text_list.append('安らぎ率:{}%'.format(calm_con))
        confused_con = round(_get_emotions('CONFUSED', emotions), 2)
        text_list.append('混乱率:{}%'.format(confused_con))
        fear_con = round(_get_emotions('FEAR', emotions), 2)
        text_list.append('恐怖率:{}%'.format(fear_con))
        disgusted_con = round(_get_emotions('DISGUSTED', emotions), 2)
        text_list.append('嫌悪率:{}%'.format(disgusted_con))
        surprised_con = round(_get_emotions('SURPRISED', emotions), 2)
        text_list.append('驚き率:{}%'.format(surprised_con))

    # リストの内容を一つの変数にまとめる
    for k in text_list:
        text = '{}\n{}'.format(text, k)
    return text.strip()

# ------------------------------------------------------------------------------
# 主処理
# ------------------------------------------------------------------------------
@app.route('/callback', methods=['POST'])
def callback():
    signature = app.current_request.headers['X-Line-Signature']
    app.log.info(f'{signature=}')
    body = app.current_request.raw_body.decode('utf-8')
    app.log.info(f'{body=}')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as error:
        return Response(
            body=json.dumps({'error': error.message}),
            headers={'content-Type': 'application/json'},
            status_code=400
        )
    return Response(
        body=json.dumps({'ok': True}),
        headers={'content-Type': 'application/json'},
        status_code=200
    )

def _valid_reply_token(event):
    '''
    Webhook のテスト時には reply token が 0 のみで構成されているので、
    その時に False を返します
    '''
    return not re.match('^0+$', event.reply_token)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    app.log.info('TextMessageEvent: %s', event)
    # Webhookテスト用
    if not _valid_reply_token(event):
        return

#    # オウム返し機能
#    line_bot_api.reply_message(
#        event.reply_token,
#        TextSendMessage(text='Reply: {}'.format(event.message.text))
#    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    app.log.info('ImageMessageEvnet: %s', event)
    message_id = event.message.id
    app.log.info('message_id: %s', message_id)

    # message_idから画像のバイナリデータを取得
    message_content = line_bot_api.get_message_content(message_id)
    app.log.info('message_content: %s', message_content)
    image_file_path = f'/tmp/{message_id}.jpg'

    # 画像データをファイルとして保存
    with open(image_file_path, "wb") as f:
        # バイナリを1024バイトずつ書き込む
        for chunk in message_content.iter_content():
            f.write(chunk)

    # 画像ファイルを解析
    response = get_rekognition_sorce_file(image_file_path)

    # 画像ファイルを削除
    os.remove(image_file_path)

    # 解析結果をLINEに送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )
