from django.conf import settings
from core.interface.storage_repository_port import StorageRepositoryPort
from infrastructure.services.r2_storage import R2Storage
from infrastructure.services.cloudinary_storage import CloudinaryStorage

class StorageFactory:
    """Factory to create storage instances based on configuration"""
    
    @staticmethod
    def create_storage(storage_type: str = None) -> StorageRepositoryPort:
        """
        Create storage instance
        storage_type: 'r2', 'cloudinary', 'django' (default from settings)
        """
        if storage_type is None:
            storage_type = getattr(settings, 'DEFAULT_STORAGE', 'r2')
        
        if storage_type == 'r2':
            return R2Storage()
        elif storage_type == 'cloudinary':
            return CloudinaryStorage()
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    @staticmethod
    def get_default_storage() -> StorageRepositoryPort:
        """Get default storage instance"""
        return StorageFactory.create_storage()