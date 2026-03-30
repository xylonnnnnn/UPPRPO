from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

async def send_verification_email(email: EmailStr, code: str):
    html = f"""
    <html>
        <body>
            <h1>Подтверждение регистрации</h1>
            <p>Ваш код подтверждения: <b>{code}</b></p>
            <p>Код действителен 10 минут.</p>
        </body>
    </html>
    """
    message = MessageSchema(
        subject="Подтверждение регистрации",
        recipients=[email],
        body=html,
        subtype="html"
    )
    try:
        await fm.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")