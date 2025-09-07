import random
from datetime import datetime, timedelta
from core.entities.otp import OtpEntity
from core.interface.otp_repository_port import OtpRepositoryPort
from infrastructure.email.email_sender import EmailSender
class RequestOtpUsecase:
    def __init__(self,otp_repo:OtpRepositoryPort,email_sender:EmailSender):
        self.otp_repo = otp_repo
        self.email_sender = email_sender

    def execute(self,email:str, action_type:str,resend:bool=False):
        if resend:
            self.otp_repo.delete_otp(email,action_type)

        code = str(random.randint(000000,999999))
        otp = OtpEntity(
            email = email,
            code = code,
            expires_at = datetime.now() + timedelta(seconds=60),
            action_type = action_type,
            verified = False
        )
        self.otp_repo.save_otp(otp)

        self.email_sender.send_email(
            to_email = email,
            subject = f"{action_type} OTP",
            body = f"Your OTP for {action_type} is {code}"
        )
        
        return {"message":f"OTP {'resent' if resend else 'sent'} for {action_type}"}