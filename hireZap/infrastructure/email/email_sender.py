from django.core.mail import send_mail
from core.interface.email_sender import EmailSenderPort

class EmailSender(EmailSenderPort):
    def send_email(self, to_email: str, subject: str, body:str):
        send_mail(
            subject,
            body,
            None,
            [to_email],
            fail_silently= False,
        )
