from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event.message.type)
    msg = event.message.text
    if '@蘇小鳳' in msg:
        if '生日' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('康爺：11/2\n錢崴：4/8\n阿信：6/20\n郭所長：8/3\n小八：8/18'))

        elif '重逢' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('朋友還是老的好，情人還是舊的好'))

        elif '郭' in msg and '照片' in msg:
            picmsg = ImageSendMessage(original_content_url='https://mx.nthu.edu.tw/~chwu/pictures/eight-god.jpg',preview_image_url='https://mx.nthu.edu.tw/~chwu/pictures/eight-god.jpg')
            txtmsg = TextSendMessage('帥')
            line_bot_api.reply_message(event.reply_token, [picmsg,txtmsg])
    elif event.source.user_id != 'U6abe720c74a3720fc837cbb1e22ca5c1':
        if '國' in msg and '機' in msg and '基' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('國機都讓腎了，哪來的國機?'))
        elif '陷阱' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('只有不肯工作的糞便製造機，才會吃飽沒事幹設陷阱陷害人吧?'))
        elif '老實' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('老實人都不老實啊~'))
        elif '愛情' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('愛情很美好，但愛情公寓千萬別碰~'))
        elif '計畫' in msg or '計劃' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('國中時老實人和我說好的鳳凰入厝計畫呢?'))
        elif '貧乳' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('老實人很悶騷的,說最愛貧乳實際上最愛巨乳!    '))
        elif '結婚' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('原本以為會跟老實人結婚的呢~~誰知道...唉~'))
        elif '挖' in msg:
            line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=446, sticker_id=2011))
        elif '免費' in msg or '不用錢' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('免費的最貴~~~'))
        elif 'http' in msg.lower():
            line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=446, sticker_id=2011))
        elif '甲崩' in msg or '呷崩' in msg or '甲奔' in msg or '謝'== msg:
            line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=6362, sticker_id=11087922))
        elif '感冒' in msg or '生病' in msg:
            line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=1070, sticker_id=17876))
        elif '忘' in msg:
            line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=11538, sticker_id=51626515))
        elif '離婚' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('揮別錯的糞便製造機，才能和對的重逢喔~~~'))

    elif msg == '挖':
        line_bot_api.reply_message(event.reply_token, StickerSendMessage(package_id=446, sticker_id=2011))
            

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
