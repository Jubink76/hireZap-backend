from core.interface.auth_repository_port import AuthRepositoryPort
from infrastructure.repositories.auth_repository import AuthUserRepository
from core.interface.otp_repository_port import OtpRepositoryPort
from infrastructure.repositories.otp_repository import OtpRepository
from core.entities.user import UserEntity


class RegisterUserUsecase:
    def __init__(self,user_repo:AuthUserRepository, otp_repo:OtpRepository):
        self.user_repo = user_repo
        self.otp_repo = otp_repo

    def execute(self, user_entity:UserEntity):
        otp = self.otp_repo.get_otp(user_entity.email, action_type='registration')
        if not otp or not otp.verified:
            raise ValueError("otp is not verified for registration")
        if self.user_repo.get_by_email(user_entity.email):
            raise ValueError("email already registered")
        created = self.user_repo.create(user_entity)
        return created