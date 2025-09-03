from core.interface.otp_repository_port import OtpRepositoryPort
from core.entities.otp import OtpEntity
from accounts.models import OtpModel


class OtpRepository(OtpRepositoryPort):
    
    def save_otp(self, otp:OtpEntity):
        OtpModel.objects.create(
            email = otp.email,
            code = otp.code,
            expires_at = otp.expires_at,
            action_type = otp.action_type,
            verified = otp.verified,
        )

    def get_otp(self, email, action_type):
        obj = OtpModel.objects.filter(email = email , action_type = action_type).last()
        if not obj:
            return None
        return OtpEntity(
            email = obj.email,
            code = obj.code,
            expires_at = obj.expires_at,
            action_type = obj.action_type,
            verified = obj.verified
        )
    
    def mark_verified(self, email, action_type):
        obj = OtpModel.objects.filter(email = email, action_type = action_type).last()
        if not obj:
            return None
        obj.update(verified = True)