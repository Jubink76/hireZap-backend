from core.interface.auth_repository_port import AuthRepositoryPort
from infrastructure.repositories.auth_repository import AuthUserRepository
class LoginUserUsecase:
    def __init__(self,user_repo:AuthUserRepository):
        self.user_repo = user_repo

    def execute(self, email:str, password:str):
        user = self.user_repo.authenticate(email,password)
        if not user:
            raise ValueError("Invalid credential")
        return user