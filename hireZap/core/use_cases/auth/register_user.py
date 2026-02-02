from core.interface.auth_repository_port import AuthRepositoryPort
from infrastructure.repositories.auth_repository import AuthUserRepository
from core.interface.otp_repository_port import OtpRepositoryPort
from infrastructure.repositories.otp_repository import OtpRepository
from core.entities.user import UserEntity


class RegisterUserUsecase:
    def __init__(self, user_repo: AuthUserRepository, otp_repo: OtpRepository):
        self.user_repo = user_repo
        self.otp_repo = otp_repo

    def execute(self, user_entity: UserEntity, code: str):
        print(f"🔍 RegisterUserUsecase - Starting for email: {user_entity.email}")
        
        otp = self.otp_repo.get_otp(user_entity.email, action_type='registration')
        print(f"🔍 OTP retrieved: {otp}")
        print(f"🔍 OTP verified status: {otp.verified if otp else 'OTP is None'}")
        
        if not otp or not otp.verified:
            print("❌ Error: OTP is not verified for registration")
            raise ValueError("otp is not verified for registration")
        
        print(f"🔍 OTP code from repo: {otp.code}, Code provided: {code}")
        if otp.code != code:
            print("❌ Error: Invalid OTP code")
            raise ValueError("Invalid OTP code")
        
        existing_user = self.user_repo.get_by_email(user_entity.email)
        print(f"🔍 Existing user check: {existing_user}")
        
        if existing_user:
            print("❌ Error: Email already registered")
            raise ValueError("email already registered")
        
        print("✅ All checks passed, creating user...")
        created = self.user_repo.create(user_entity)

        if created:
            print(f"✅ User created successfully: {created.id}")
        
        self.otp_repo.delete_otp(user_entity.email, 'registration')
        print("✅ OTP deleted")
        
        return created