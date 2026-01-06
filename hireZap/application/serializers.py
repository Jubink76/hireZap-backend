from rest_framework import serializers
from .models import ApplicationModel

class ApplicationCreateSerializer(serializers.Serializer):
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

class ApplicationSerializer(serializers.ModelSerializer):
    screening_decision = serializers.CharField(source='ats_decision', read_only=True)
    screening_scores = serializers.SerializerMethodField()
    screening_details = serializers.SerializerMethodField()
    screened_at = serializers.SerializerMethodField()

    ob_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    company_logo = serializers.CharField(source='job.company.logo_url', read_only=True)


    class Meta:
        model = ApplicationModel
        fields = [
            'id',
            'job_id',
            'candidate_id',
            'resume_url',
            'portfolio_url',
            'first_name',
            'last_name',
            'email',
            'phone',
            'location',
            'linkedin_profile',
            'years_of_experience',
            'availability',
            'expected_salary',
            'current_company',
            'cover_letter',

            # application
            'status',
            'current_stage_id',
            'current_stage_status',

            'job_title',
            'company_name', 
            'company_logo',

            # screening
            'screening_status',
            'screening_decision',
            'screening_scores',
            'screening_details',
            'screened_at',

            # timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_screening_decision(self, obj):
        """Get screening decision"""
        return obj.ats_decision if obj.ats_decision else 'pending'

    def get_screening_scores(self, obj):
        """Get screening scores"""
        return {
            'overall': obj.ats_overall_score or 0,
            'skills': obj.ats_skills_score or 0,
            'experience': obj.ats_experience_score or 0,
            'education': obj.ats_education_score or 0,
            'keywords': obj.ats_keywords_score or 0,
        }
    
    def get_screening_details(self, obj):
        """Get detailed screening results"""
        try:
            result = obj.screening_result
            return {
                'matched_skills': result.matching_skills or [],
                'missing_skills': result.missing_required_skills or [],
                'matched_keywords': result.matched_keywords or [],
                'experience_years': result.extracted_experience_years or 0,
                'education': result.extracted_education or '',
                'is_ats_friendly': result.is_ats_friendly,
                'ats_issues': result.ats_issues or [],
                'ai_summary': result.ai_summary or '',
                'strengths': result.strengths or [],
                'weaknesses': result.weaknesses or [],
            }
        except Exception as e:
            return None 
    
    def get_screened_at(self, obj):
        """Get screening timestamp"""
        try:
            if hasattr(obj, 'screening_result') and obj.screening_result.screening_at:
                return obj.screening_result.screening_at.isoformat()
        except:
            pass
        
        if obj.screening_status == 'completed':
            return obj.updated_at.isoformat()
        
        return None