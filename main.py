import os
from fastapi import FastAPI, Request, HTTPException
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, 
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

# --- ใส่รหัสที่คุณจดไว้ตรงนี้ ---
LINE_CHANNEL_SECRET = "c3cf4310bc02e00c0458d1ea7724441d"
LINE_CHANNEL_ACCESS_TOKEN = "EBjfPdJi09SK/6/CNtIxNZKRg0QZsZKkHUG6VDu4OgoBHpWdKlOTPJ/Gyav+agb2x74FV2pzMCUL2cWbfZgo2ii6wPVklscbSEeXhJTJakDycXSBNk4MeDAZ5lkbbGFWDHwnX9FAJQyYbg4acjawmQdB04t89/1O/w1cDnyilFU="
GEMINI_API_KEY = "AIzaSyDDRuJuG2MRPNN41kYWXjkmF3a651wSy0w"

# ตั้งค่า Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = FastAPI()
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_ai_answer(user_question):
    # อ่านกติกาจากไฟล์
    with open("rules.txt", "r", encoding="utf-8") as f:
        rules = f.read()
    
    prompt = f"คุณคือผู้ช่วยตอบคำถามกติกาการแข่งขัน โดยอิงจากข้อมูลนี้:\n{rules}\n\nคำถาม: {user_question}\nตอบให้สุภาพและกระชับ"
    response = model.generate_content(prompt)
    return response.text

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    msg_text = event.message.text
    
    # บอทจะตอบเมื่อถูกถาม หรือระบุคำสำคัญ (ปรับเปลี่ยนได้)
    if "ถามกติกา" in msg_text or "ช่วยบอกหน่อย" in msg_text:
        answer = get_ai_answer(msg_text)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=answer)]
                )
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
