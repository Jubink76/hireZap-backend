from rest_framework import serializers

class ApplicationSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(required=True)
    resume_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    portfolio_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    location = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    linkedin_profile = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    years_of_experience = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    availability = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=50)
    expected_salary = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    current_company = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    cover_letter = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_draft = serializers.BooleanField(default=False)

class UpdateApplicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            'applied', 'under_review','qualified', 'shortlisted', 'interview_scheduled',
            'interviewed', 'offered', 'rejected', 'withdrawn', 'hired'
        ],
        required=True
    )