from infrastructure.repositories.auth_repository import AuthUserRepository
class ResetPasswordUseCase:
    def __init__(self,auth_repo:AuthUserRepository):
        self.auth_repo = auth_repo

    def execute(self, email:str, password:str) -> bool:
        return self.auth_repo.update_password(email, password)
