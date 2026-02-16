import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_whatsapp_alert(area_name: str, confidence: float):

    message_body = f"""
🚨 DEFORESTATION ALERT 🚨

📍 Area: {area_name}
📊 Confidence: {confidence}%

Forest loss detected.
Immediate inspection required.
"""

    message = client.messages.create(
        body=message_body,
        from_=TWILIO_NUMBER,
        to="whatsapp:+918468092435"  # replace with real number
    )

    return message.sid
