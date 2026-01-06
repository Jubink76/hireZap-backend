# infrastructure/storage/cloudinary_storage.py
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings
from core.interface.storage_repository_port import StorageRepositoryPort
from typing import BinaryIO, Dict
import uuid
import os

class CloudinaryStorage(StorageRepositoryPort):
    """Cloudinary Storage Implementation"""
    
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY['cloud_name'],
            api_key=settings.CLOUDINARY['api_key'],
            api_secret=settings.CLOUDINARY['api_secret'],
            secure=True
        )
    
    def upload_file(
        self,
        file: BinaryIO,
        folder: str,
        filename: str,
        content_type: str,
        **kwargs
    ) -> Dict:
        """Upload file to Cloudinary"""
        try:
            # Determine resource type
            resource_type = kwargs.get('resource_type', 'auto')
            if 'pdf' in content_type or 'document' in content_type:
                resource_type = 'raw'
            elif 'image' in content_type:
                resource_type = 'image'
            
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type=resource_type,
                type='upload',
                access_mode='public'
            )
            
            return {
                'url': result['secure_url'],
                'key': result['public_id'],
                'bucket': 'cloudinary',
                'success': True
            }
            
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
    
    def delete_file(self, file_key: str) -> bool:
        """Delete file from Cloudinary"""
        try:
            cloudinary.uploader.destroy(file_key)
            return True
        except:
            return False
    
    def generate_signed_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Generate signed Cloudinary URL"""
        import time
        return cloudinary.CloudinaryResource(file_key).build_url(
            resource_type="raw",
            type="upload",
            sign_url=True,
            secure=True,
            expires_at=int(time.time()) + expires_in
        )
    
    def file_exists(self, file_key: str) -> bool:
        """Check if file exists"""
        try:
            cloudinary.api.resource(file_key)
            return True
        except:
            return False