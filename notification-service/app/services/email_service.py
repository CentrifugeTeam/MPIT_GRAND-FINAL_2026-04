import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Отправить email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email

            # Добавляем тело письма
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)

            # Отправляем письмо
            text = msg.as_string()
            server.sendmail(self.smtp_username, to_email, text)
            server.quit()

            return True
        except Exception as e:
            return False

    def send_registration_email(self, to_email: str, user_name: str = None) -> bool:
        """Отправить email подтверждения регистрации"""
        subject = "Добро пожаловать!"
        body = f"""
        <html>
        <body>
            <h2>Добро пожаловать!</h2>
            <p>Спасибо за регистрацию в нашем сервисе.</p>
            <p>Ваш аккаунт успешно создан.</p>
            <br>
            <p>С уважением,<br>Команда сервиса</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, body, is_html=True)

    def send_system_notification(self, to_email: str, title: str, message: str) -> bool:
        """Отправить системное уведомление"""
        subject = f"Уведомление: {title}"
        body = f"""
        <html>
        <body>
            <h2>{title}</h2>
            <p>{message}</p>
            <br>
            <p>С уважением,<br>Команда сервиса</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, body, is_html=True)

# Создаем экземпляр сервиса
email_service = EmailService()
