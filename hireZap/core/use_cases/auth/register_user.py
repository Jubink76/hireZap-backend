from core.interface.auth_repository_port import AuthRepositoryPort
from infrastructure.repositories.auth_repository import AuthUserRepository
from core.interface.otp_repository_port import OtpRepositoryPort
from infrastructure.repositories.otp_repository import OtpRepository
from core.entities.user import UserEntity
import logging
logger = logging.getLogger(__name__)

class RegisterUserUsecase:
    def __init__(self, user_repo: AuthUserRepository, otp_repo: OtpRepository):
        self.user_repo = user_repo
        self.otp_repo = otp_repo

    def execute(self, user_entity: UserEntity, code: str):
        logger.info(f" RegisterUserUsecase - Starting for email: {user_entity.email}")
        
        otp = self.otp_repo.get_otp(user_entity.email, action_type='registration')
        logger.info(f" OTP retrieved: {otp}")
        logger.info(f" OTP verified status: {otp.verified if otp else 'OTP is None'}")
        
        if not otp or not otp.verified:
            logger.error(" Error: OTP is not verified for registration")
            raise ValueError("otp is not verified for registration")
        
        logger.info(f" OTP code from repo: {otp.code}, Code provided: {code}")
        if otp.code != code:
            logger.error(" Error: Invalid OTP code")
            raise ValueError("Invalid OTP code")
        
        existing_user = self.user_repo.get_by_email(user_entity.email)
        logger.info(f" Existing user check: {existing_user}")
        
        if existing_user:
            logger.error(" Error: Email already registered")
            raise ValueError("email already registered")
        
        logger.info(" All checks passed, creating user...")
        created = self.user_repo.create(user_entity)

        if created:
            logger.info(f" User created successfully: {created.id}")
        
        self.otp_repo.delete_otp(user_entity.email, 'registration')
        logger.info(" OTP deleted")
        
        return created