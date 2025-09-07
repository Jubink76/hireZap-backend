from datetime import datetime
from infrastructure.repositories.otp_repository import OtpRepository
class VerifyOtpUsecase:
    def __init__(self,otp_repo:OtpRepository):
        self.otp_repo = otp_repo

    def execute(self, email:str, code:str, action_type:str) -> bool:
        otp = self.otp_repo.get_otp(email, action_type)
        if not otp or otp.code != code or otp.expires_at < datetime.now():
            return False
        self.otp_repo.mark_verified(email, action_type)
        return True