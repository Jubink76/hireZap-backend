from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserEntity:
    id : Optional[int]
    full_name : str
    email : str
    phone : Optional[str]
    password : Optional[str]
    role : str
    profile_image_url : Optional[str]
    is_admin : bool = False
    last_login : Optional[datetime] = None
    created_at : Optional[datetime] = None
    is_active : bool = True