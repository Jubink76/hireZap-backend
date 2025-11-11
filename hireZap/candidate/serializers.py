from rest_framework import serializers
from datetime import date

class CandidateProfileSerializer(serializers.Serializer):
    """Serializer for updating candidate profile"""
    bio = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=15)
    linkedin_url = serializers.URLField(required=False, allow_blank=True, max_length=255)
    github_url = serializers.URLField(required=False, allow_blank=True, max_length=255)
    location = serializers.CharField(required=False, allow_blank=True, max_length=255)
    website = serializers.URLField(required=False, allow_blank=True, max_length=255)
    resume_url = serializers.URLField(required=False, allow_blank=True, max_length=1024)

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Invalid phone number format")
        return value


class EducationSerializer(serializers.Serializer):
    """Serializer for education records"""
    degree = serializers.CharField(max_length=255)
    field_of_study = serializers.CharField(max_length=255)
    institution = serializers.CharField(max_length=255)
    start_year = serializers.IntegerField(min_value=1950, max_value=date.today().year + 1)
    end_year = serializers.IntegerField(
        required=False, 
        allow_null=True, 
        min_value=1950, 
        max_value=date.today().year + 5
    )

    def validate(self, data):
        """Validate that end_year is after start_year"""
        if data.get('end_year') and data['start_year']:
            if data['end_year'] < data['start_year']:
                raise serializers.ValidationError({
                    "end_year": "End year must be after start year"
                })
        return data


class ExperienceSerializer(serializers.Serializer):
    """Serializer for work experience"""
    company_name = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=255)
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=2000
    )

    def validate(self, data):
        """Validate that end_date is after start_date"""
        if data.get('end_date') and data['start_date']:
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    "end_date": "End date must be after start date"
                })
            if data['end_date'] > date.today():
                raise serializers.ValidationError({
                    "end_date": "End date cannot be in the future"
                })
        
        if data['start_date'] > date.today():
            raise serializers.ValidationError({
                "start_date": "Start date cannot be in the future"
            })
        
        return data


class SkillSerializer(serializers.Serializer):
    """Serializer for skills"""
    skill_name = serializers.CharField(max_length=100)
    proficiency = serializers.IntegerField(min_value=1, max_value=5)
    years_of_experience = serializers.IntegerField(
        min_value=0, 
        max_value=50,
        default=0
    )

    def validate_skill_name(self, value):
        """Validate and normalize skill name"""
        if not value.strip():
            raise serializers.ValidationError("Skill name cannot be empty")
        return value.strip()


class CertificationSerializer(serializers.Serializer):
    """Serializer for certifications"""
    name = serializers.CharField(max_length=255)
    issuer = serializers.CharField(max_length=255)
    field = serializers.CharField(max_length=255)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    credential_url = serializers.URLField(
        required=False, 
        allow_blank=True, 
        max_length=1024
    )

    def validate(self, data):
        """Validate certification dates"""
        if data.get('issue_date') and data['issue_date'] > date.today():
            raise serializers.ValidationError({
                "issue_date": "Issue date cannot be in the future"
            })
        
        if data.get('expiry_date') and data.get('issue_date'):
            if data['expiry_date'] < data['issue_date']:
                raise serializers.ValidationError({
                    "expiry_date": "Expiry date must be after issue date"
                })
        
        return data


# Response Serializers (for consistent API responses)
class ProfileResponseSerializer(serializers.Serializer):
    """Read-only serializer for profile responses"""
    user_id = serializers.IntegerField()
    bio = serializers.CharField(allow_null=True)
    phone_number = serializers.CharField(allow_null=True)
    linkedin_url = serializers.URLField(allow_null=True)
    github_url = serializers.URLField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    resume_url = serializers.URLField(allow_null=True)
    website = serializers.URLField(allow_null=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)


class EducationResponseSerializer(serializers.Serializer):
    """Read-only serializer for education responses"""
    id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    degree = serializers.CharField()
    field_of_study = serializers.CharField()
    institution = serializers.CharField()
    start_year = serializers.IntegerField()
    end_year = serializers.IntegerField(allow_null=True)


class ExperienceResponseSerializer(serializers.Serializer):
    """Read-only serializer for experience responses"""
    id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    company_name = serializers.CharField()
    role = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True)
    description = serializers.CharField(allow_null=True)


class SkillResponseSerializer(serializers.Serializer):
    """Read-only serializer for skill responses"""
    id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    skill_name = serializers.CharField()
    proficiency = serializers.IntegerField()
    years_of_experience = serializers.IntegerField()
    proficiency_label = serializers.CharField()


class CertificationResponseSerializer(serializers.Serializer):
    """Read-only serializer for certification responses"""
    id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    name = serializers.CharField()
    issuer = serializers.CharField()
    field = serializers.CharField()
    issue_date = serializers.DateField(allow_null=True)
    expiry_date = serializers.DateField(allow_null=True)
    credential_url = serializers.URLField(allow_null=True)