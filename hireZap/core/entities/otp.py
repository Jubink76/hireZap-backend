from datetime import datetime
from dataclasses import dataclass

# When using dataclass all non-default should be first in order
@dataclass
class OtpEntity:
    email : str
    code : str
    expires_at : datetime
    action_type : str
    verified : bool = False # default last
