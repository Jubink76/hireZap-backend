from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class Roles(models.TextChoices):
    CANDIDATE = 'candidate','Candidate'
    RECRUITER = 'recruiter', 'Recruiter'
    ADMIN = 'admin', 'Admin'

class UserManager(BaseUserManager):
    def create_user(self, email, full_name=None, password = None,**extra_fields):
        if not email:
            raise ValueError("Email required")
        email= self.normalize_email(email)

        if not full_name:
            first = extra_fields.pop('first_name', '')
            last = extra_fields.pop('last_name', '')
            full_name = (first + ' ' + last).strip()
            
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
        extra_fields.setdefault('role',Roles.ADMIN)
        user = self.create_user(full_name=full_name, email=email, password= password, **extra_fields)
        user.is_staff = True
        user.save(using = self._db)
        return user
    

class User(AbstractBaseUser,PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image_url = models.CharField(max_length=1024,blank=True, null= True)
    role = models.CharField(max_length=20,choices=Roles.choices, default=Roles.CANDIDATE, db_index=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default = True, db_index=True)
    is_staff = models.BooleanField(default = False)
    last_login = models. DateTimeField(blank=True, null= True)
    created_at = models.DateField(auto_now_add=True, db_index=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS =['full_name']

    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=['role','-created_at']), # composite index for filtering and sorting 
            models.Index(fields=['email','is_active'])  # composite for loging requirements
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.role})"

