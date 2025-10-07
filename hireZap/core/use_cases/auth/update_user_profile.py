from core.interface.auth_repository_port import AuthRepositoryPort
from core.entities.user import UserEntity
from typing import Optional
import re

class UpdateUserProfileUseCase:
    def __init__(self, user_repo:AuthRepositoryPort):
        self.user_repo = user_repo

    def execute(self, user_id:int, profile_data:dict) -> UserEntity:
        """ Update user profile with validation

            Args:
                user_id : Id of the user update
                profile_data : Dictionary containing fields to update
            
            Returns:
                Updated UserEntity
            Raises:
                ValueError: If validation fails
            
        """
        existing_user = self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise ValueError("User not found")
        
        new_email = profile_data.get('email')
        if new_email and new_email != existing_user.email:
            if self.user_repo.email_exists_for_other_user(new_email, user_id):
                raise ValueError("Email is already in use by another user")
            if not self._is_valid_email(new_email):
                raise ValueError("Invalid email format")
        
        full_name = profile_data.get('full_name')
        if full_name is not None:
            if not full_name or not full_name.strip():
                raise ValueError("Full name cannot be empty")
            if len(full_name.strip()) < 2:
                raise ValueError("Full name must be at least 2 characters")
        
        location = profile_data.get('location', existing_user.location)
        if location and len(location) > 255:
            raise ValueError("Location must be less than 255 characters")
        
        phone = profile_data.get('phone')
        if phone:
            if not self._is_valid_phone(phone):
                raise ValueError("Invalid phone number format")
        
        updated_entity = UserEntity(
            id=existing_user.id,
            full_name=profile_data.get('full_name', existing_user.full_name).strip(),
            email=profile_data.get('email', existing_user.email).lower(),
            phone=profile_data.get('phone', existing_user.phone),
            password=existing_user.password,  # Don't update password here
            role=existing_user.role,  # Don't allow role change
            profile_image_url=profile_data.get('profile_image_url', existing_user.profile_image_url),
            location=location,
            is_admin=existing_user.is_admin,
            last_login=existing_user.last_login,
            created_at=existing_user.created_at,
            is_active=existing_user.is_active
        )

        return self.user_repo.update_user_profile(user_id, updated_entity)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not cleaned.replace('+', '').isdigit():
            return False
        return len(cleaned) >= 10