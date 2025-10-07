from core.interface.auth_repository_port import AuthRepositoryPort
from core.entities.user import UserEntity
from accounts.models import User
from typing import Optional
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password


class AuthUserRepository(AuthRepositoryPort):
    def create(self,user:UserEntity) -> User:
        u = User.objects.create(
            email = user.email,
            full_name = user.full_name,
            phone = user.phone or None,
            role = user.role,
            profile_image_url = user.profile_image_url or None,
            is_admin = user.is_admin,
            is_active = user.is_active
        )
        if user.password:
            u.set_password(user.password)
            u.save()
        return u
    
    def get_by_email(self, email: str) -> Optional[User]:
        try:
            return User.objects.get(email__iexact = email)
        except User.DoesNotExist:
            return None
        
    def get_by_id(self, user_id:int) -> Optional[UserEntity]:
        try:
            user = User.objects.get(id=user_id)
            return self._to_entity(user)
        except User.DoesNotExist:
            return None
        
    def authenticate(self, email:str, password: str) -> Optional[User]:
        user = self.get_by_email(email) 
        if not user:
            return None
        if not user.is_active:
            return None
        if not user.check_password(password):
            return None
        return user
    
    def update_last_login(self, user_id: int):
        try:
            u = User.objects.get(pk = user_id)
            u.last_login = timezone.now()
            u.save(update_fields=['last_login'])
        except User.DoesNotExist:
            pass
    
    def update_password(self, email, new_password):
        try:
            user = User.objects.get(email = email)
            user.password = make_password(new_password)
            user.save(update_fields=['password'])
            return True
        except User.DoesNotExist:
            return False
    
    def update_user_profile(self, user_id: int, user_entity: UserEntity) -> UserEntity:
        """Update user profile"""
        try:
            user = User.objects.get(id=user_id)
            user.full_name = user_entity.full_name
            user.email = user_entity.email
            user.phone = user_entity.phone
            user.profile_image_url = user_entity.profile_image_url
            user.location = user_entity.location
            user.save()
            return self._to_entity(user)
        except User.DoesNotExist:
            raise ValueError("User not found")
    
    def email_exists_for_other_user(self, email: str, user_id: int) -> bool:
        return User.objects.filter(email=email).exclude(id=user_id).exists()
    
    def _to_entity(self, user: User) -> UserEntity:
        return UserEntity(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            password=None,  # Don't expose password
            role=user.role,
            profile_image_url=user.profile_image_url,
            location=user.location,
            is_admin=user.is_admin,
            last_login=user.last_login,
            created_at=user.created_at,
            is_active=user.is_active
        )
