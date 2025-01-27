from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import json
import os
from firebase import firebase
import google.generativeai as genai
from datetime import datetime, timedelta
import requests

#======python的函數庫==========
import tempfile, os
import openai
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

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.getenv('DEEPSEEK_API_KEY')


def linebot(request):
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    try:
        line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
        handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
        signature = request.headers['X-Line-Signature']
        handler.handle(body, signature)
        event = json_data['events'][0]
        tk = event['replyToken']
        user_id = event['source']['userId']
        msg_type = event['message']['type']

        fdb = firebase.FirebaseApplication(firebase_url, None)
        user_chat_path = f'chat/{user_id}'
        chat_state_path = f'state/{user_id}'
        chatgpt = fdb.get(user_chat_path, None)

        if msg_type == 'text':
            msg = event['message']['text']

            if chatgpt is None:
                messages = []
            else:
                messages = chatgpt

            if msg == '!清空':
                reply_msg = TextSendMessage(text='對話歷史紀錄已經清空！')
                fdb.delete(user_chat_path, None)
            else:
                model = genai.GenerativeModel('gemini-pro')
                messages.append({'role':'user','parts': [msg]})                
                response = model.generate_content(messages)
                messages.append({'role':'model','parts': [response.text]})                
                reply_msg = TextSendMessage(text=response.text)
                # 更新firebase中的對話紀錄
                fdb.put_async(user_chat_path, None , messages)
                
            line_bot_api.reply_message(tk, reply_msg)

        else:
            reply_msg = TextSendMessage(text='你傳的不是文字訊息呦')
            line_bot_api.reply_message(tk, reply_msg)

    except Exception as e:
        detail = e.args[0]
        print(detail)
    return 'OK'


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

birthdays = {
    "康爺": "11-02",
    "阿果": "01-06",
    "錢崴": "04-08",
    "阿信": "06-20",
    "郭所長": "08-03",
    "小八":"08-18"
}

def find_closest_birthday(birthdays):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # 清除時間部分
    current_year = today.year

    closest_person = None
    min_days_diff = float('inf')

    for person, birth_date in birthdays.items():
        # 將生日結合今年，轉換為 datetime
        birthday_this_year = datetime.strptime(f"{current_year}-{birth_date}", "%Y-%m-%d")

        # 如果生日已過，今年的生日就要考慮下一年
        if birthday_this_year < today:
            birthday_this_year = datetime.strptime(f"{current_year + 1}-{birth_date}", "%Y-%m-%d")

        # 計算距離今天的天數
        days_diff = (birthday_this_year - today).days

        # 更新最近的生日
        if days_diff < min_days_diff:
            min_days_diff = days_diff
            closest_person = person

    # 特殊處理：如果距離為 0 天，表示今天就是生日
    if min_days_diff == 0:
        return closest_person, f"生日就是今天！\n{closest_person}生日快樂!\U0001F389"
    else:
        return closest_person, f"距離今天還有 {min_days_diff} 天"

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event.message.type)
    msg = event.message.text
    if '@蘇小鳳' in msg:
        if '生日' in msg:
            closest_person, message = find_closest_birthday(birthdays)
            line_bot_api.reply_message(event.reply_token, TextSendMessage('康爺：11/2\n阿果：1/6\n錢崴：4/8\n阿信：6/20\n郭所長：8/3\n小八：8/18\n'+f'最近的生日是 {closest_person}，{message}'))

        elif '重逢' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('朋友還是老的好，情人還是舊的好'))

        elif '郭' in msg and '照' in msg and '帥' in msg:
            picmsg = ImageSendMessage(original_content_url='https://mx.nthu.edu.tw/~chwu/pictures/eight-god.jpg',preview_image_url='https://mx.nthu.edu.tw/~chwu/pictures/eight-god.jpg')
            txtmsg = TextSendMessage('帥')
            line_bot_api.reply_message(event.reply_token, [picmsg,txtmsg])

        elif '郭' in msg and '照' in msg and '心動' in msg:
            picmsg = ImageSendMessage(original_content_url='https://i.imgur.com/YeWYeph.jpeg',preview_image_url='https://i.imgur.com/YeWYeph.jpeg')
            txtmsg = TextSendMessage("\U0001F493")
            line_bot_api.reply_message(event.reply_token, [picmsg,txtmsg])
        else:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": msg}]
            }
            response = requests.post(API_URL, json=data, headers=headers)
            if response.status_code == 200:
                bot_reply = response.json()['choices'][0]['message']['content']
            else:
                bot_reply = "抱歉，我暂时无法处理你的请求。"
        
            # 将回复发送回用户
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=bot_reply)
            )

    
    elif event.source.user_id != 'U6abe720c74a3720fc837cbb1e22ca5c1':
        if '國' in msg and '機' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('國機都讓腎了，哪來的國機?'))
        elif '國' in msg and '基' in msg:
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
            line_bot_api.reply_message(event.reply_token, TextSendMessage('老實人很悶騷的，說最愛貧乳實際上最愛巨乳!'))
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
        elif '學長' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('學長有順便提醒\n別忘了鳳凰入厝的計劃嗎?'))
        elif '學姊' in msg or '學姐' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('學姊有順便提醒\n別忘了鳳凰入厝的計劃嗎?'))
        elif '屬' in msg and '什麼' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('我屬於老實人\U0001F495'))
        elif '屬' in msg and '於' in msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('我屬於老實人\U0001F495'))
    

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
