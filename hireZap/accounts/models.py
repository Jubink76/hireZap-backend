from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class Roles(models.TextChoices):
    CANDIDATE = 'candidate','Candidate'
    RECRUITER = 'recruiter', 'Recruiter'

class UserManager(BaseUserManager):
    def create_user(self, full_name, email, password = None,**extra_fields):
        if not email:
            raise ValueError("Email required")
        email= self.normalize_email(email)
        user = self.model(email=email,full_name=full_name,**extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using = self._db)
        return user
    
    def create_superuser(self,full_name, email, password = None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(full_name=full_name, email=email, password= password, **extra_fields)
        user.is_staff = True
        user.save(using = self._db)
        return user
    

class User(AbstractBaseUser,PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image_url = models.CharField(max_length=1024,blank=True, null= True)
    role = models.CharField(max_length=20,choices=Roles.choices, default=Roles.CANDIDATE)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)
    last_login = models. DateTimeField(blank=True, null= True)
    created_at = models.DateField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS =['full_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

