from rest_framework import serializers
from accounts.models import Roles, User

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(required = True)
    email = serializers.EmailField(required = True)
    password = serializers.CharField(write_only = True, min_length=8)
    role = serializers.ChoiceField(choices=Roles.choices, required = False)
    phone = serializers.CharField(required = False, allow_blank = True)
    profile_image_url = serializers.CharField(required = False, allow_blank = True)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(default = False)

class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id",
                "full_name", 
                "email", 
                "phone", 
                "role", 
                "profile_image_url", 
                "is_admin", 
                "last_login", 
                "created_at", 
                "is_active"]
        read_only_fields = fields