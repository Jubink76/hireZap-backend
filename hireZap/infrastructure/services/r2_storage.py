import boto3
from botocore.client import Config
from django.conf import settings
from core.interface.storage_repository_port import StorageRepositoryPort
from typing import BinaryIO, Dict
import uuid
import os

class R2Storage(StorageRepositoryPort):
    """Cloudflare R2 storage implementation"""
    def __init__(self):
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL

        # Create S3-compatible client for R2
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
    
    def upload_file(
        self,
        file: BinaryIO,
        folder: str,
        filename: str,
        content_type: str,
        make_public: bool = True,
        **kwargs) -> Dict:
        """Upload file to R2"""
        try:
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_id = uuid.uuid4().hex[:8]
            file_key = f"{folder}/{unique_id}{file_ext}"
            
            # Upload to R2
            extra_args = {
                'ContentType': content_type,
            }
            
            if make_public:
                extra_args['ACL'] = 'public-read'
            
            self.client.upload_fileobj(
                file,
                self.bucket_name,
                file_key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            public_url = f"{self.public_url}/{file_key}"
            
            return {
                'url': public_url,
                'key': file_key,
                'bucket': self.bucket_name,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ R2 Upload Error: {str(e)}")
            raise Exception(f"Failed to upload to R2: {str(e)}")
    
    def delete_file(self, file_key: str) -> bool:
        """Delete file from R2"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except Exception as e:
            print(f"❌ R2 Delete Error: {str(e)}")
            return False
    
    def generate_signed_url(self, file_key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for private files"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            print(f"❌ R2 Signed URL Error: {str(e)}")
            raise Exception(f"Failed to generate signed URL: {str(e)}")
    
    def file_exists(self, file_key: str) -> bool:
        """Check if file exists in R2"""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except:
            return False