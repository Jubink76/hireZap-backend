from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional

class StorageRepositoryPort(ABC):

    @abstractmethod
    def upload_file(self,file:BinaryIO, folder:str, filename:str, content_type:str, **kwargs)->Dict:
        """
        Upload a file
        Returns: {
            'url': 'public_url',
            'key': 'file_key',
            'bucket': 'bucket_name'
        }
        """
        pass

    @abstractmethod
    def delete_file(self, file_key:str) ->bool:
        """Delete a file"""
        pass

    @abstractmethod
    def generate_signed_url(self, file_key:str, expires_in:int = 3600) -> str:
        """Generate signed url for private files"""
        pass

    @abstractmethod
    def file_exists(self,file_key:str) -> bool:
        """Check if file exists"""
        pass
    