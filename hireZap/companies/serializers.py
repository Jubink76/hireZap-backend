from rest_framework import serializers
from companies.models import Company

class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    is_verified = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id',
            'recruiter',
            'company_name',
            'logo_url',
            'business_certificate',
            'business_email',
            'phone_number',
            'industry',
            'company_size',
            'website',
            'linkedin_url',
            'address',
            'latitude',
            'longitude',
            'verification_status',
            'founded_year',
            'description',
            'rejection_reason',
            'created_at',
            'updated_at',
            'is_verified',
            'is_pending'
        ]
        read_only_fields = ['id', 'recruiter', 'verification_status', 'created_at', 'updated_at', 'rejection_reason']


class CreateCompanySerializer(serializers.Serializer):
    """Serializer for creating company"""
    company_name = serializers.CharField(max_length=255, required=True)
    logo_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    business_certificate = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    business_email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    industry = serializers.CharField(max_length=100, required=True)
    company_size = serializers.CharField(max_length=50, required=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    founded_year = serializers.CharField(max_length=4, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_business_email(self, value):
        """Validate business email"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email address")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value


class UpdateCompanySerializer(serializers.Serializer):
    """Serializer for updating company"""
    company_name = serializers.CharField(max_length=255, required=False)
    logo_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    business_certificate = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    business_email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    industry = serializers.CharField(max_length=100, required=False)
    company_size = serializers.CharField(max_length=50, required=False)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    founded_year = serializers.CharField(max_length=4, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_founded_year(self,value):
        if value and value.strip():
            try:
                year = int(value)
                if year < 1800 or year > 2025:
                    raise serializers.ValidationError("Pleae enter a valid year")
            except ValueError:
                raise serializers.ValidationError("Year must be a number")
        return value
    def validate_company_size(self, value):
        if value:
            allowed_sizes = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001+']
            if value not in allowed_sizes:
                raise serializers.ValidationError(f"Company size must be one of: {', '.join(allowed_sizes)}")
        return value

class VerifyCompanySerializer(serializers.Serializer):
    """Serializer for verifying company (admin)"""
    status = serializers.ChoiceField(choices=['verified', 'rejected'], required=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate(self, data):
        """Validate that reason is provided when rejecting"""
        if data.get('status') == 'rejected' and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Reason is required when rejecting a company'
            })
        return data


class CompanyListSerializer(serializers.ModelSerializer):
    """Serializer for listing companies"""
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    recruiter_email = serializers.EmailField(source='recruiter.email', read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id',
            'recruiter',
            'recruiter_name',
            'recruiter_email',
            'company_name',
            'industry',
            'company_size',
            'verification_status',
            'created_at'
        ]