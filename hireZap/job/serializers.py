from rest_framework import serializers
from job.models import JobModel
from companies.serializers import CompanySerializer

class JobSerializer(serializers.ModelSerializer):

    company = CompanySerializer(read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    has_configured_stages = serializers.BooleanField(read_only=True)
    configured_stages_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = JobModel
        fields = [
            'id',
            'company',
            'company_name',
            'recruiter',
            'recruiter_name',
            'job_title',
            'location',
            'work_type',
            'employment_type',
            'compensation_range',
            'posting_date',
            'cover_image',
            'role_summary',
            'skills_required',
            'key_responsibilities',
            'requirements',
            'benefits',
            'application_link',
            'application_deadline',
            'applicants_visibility',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'company',
            'recruiter',
            'created_at',
            'updated_at',
            'posting_date'
        ]

class CreateJobSerializer(serializers.Serializer):
    
    job_title = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=True)
    work_type = serializers.ChoiceField(choices=['remote', 'onsite', 'hybrid'], required=True)
    employment_type = serializers.ChoiceField(
        choices=['full-time', 'part-time', 'contract', 'internship'],
        required=True
    )
    compensation_range = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    cover_image = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    role_summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    skills_required = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    key_responsibilities = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    requirements = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    benefits = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    application_link = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    application_deadline = serializers.DateTimeField(required=False, allow_null=True)
    applicants_visibility = serializers.ChoiceField(
        choices=['public', 'private'],
        required=False,
        default='private'
    )
    status = serializers.ChoiceField(
        choices=['active', 'paused', 'closed', 'draft'],
        required=False,
        default='active'
    )

    def validate_job_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters long")
        return value

    def validate_location(self, value):
        if not value:
            raise serializers.ValidationError("Location is required")
        return value
    
    def validate_skills_required(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list of strings")
        if any(not isinstance(skill, str) for skill in value):
            raise serializers.ValidationError("Each skill must be a string")
        return value