from rest_framework import serializers  
from resume_screening.models import ATSConfiguration

class ATSConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATSConfiguration
        fields = [
            'id',
            'job',
            'skills_weight',
            'experience_weight',
            'education_weight',
            'keywords_weight',
            'passing_score',
            'required_skills',
            'preferred_skills',
            'minimum_experience_years',
            'required_education',
            'important_keywords',
            'auto_reject_missing_skills',
            'auto_reject_below_experience',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at','updated_at']

    def validate(self,data):

        total_weight = (
            data.get('skills_weight',0) +
            data.get('experience_weight',0) +
            data.get('education_weight', 0) + 
            data.get('keywords_weight', 0)
        )
        if total_weight != 100:
            raise serializers.ValidationError(
                "Weights must sum to 100%"
            )
        return data
