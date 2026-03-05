from rest_framework import serializers
from .models import OfferLetterModel


class SendOfferSerializer(serializers.Serializer):
    position_title    = serializers.CharField(max_length=255)
    offered_salary    = serializers.CharField(max_length=100)
    joining_date      = serializers.DateField()
    offer_expiry_date = serializers.DateField()
    custom_message    = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if data['offer_expiry_date'] <= data['joining_date']:
            raise serializers.ValidationError(
                "Offer expiry date must be after joining date."
            )
        return data


class BulkSendOfferSerializer(serializers.Serializer):
    application_ids   = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    position_title    = serializers.CharField(max_length=255)
    offered_salary    = serializers.CharField(max_length=100)
    joining_date      = serializers.DateField()
    offer_expiry_date = serializers.DateField()
    custom_message    = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if data['offer_expiry_date'] <= data['joining_date']:
            raise serializers.ValidationError(
                "Offer expiry date must be after joining date."
            )
        return data


class CandidateRespondSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'decline'])
    note   = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.SerializerMethodField()
    job_title      = serializers.CharField(source='application.job.job_title',     read_only=True)
    company_name   = serializers.CharField(source='application.job.company.company_name', read_only=True)
    is_expired     = serializers.BooleanField(read_only=True)

    class Meta:
        model  = OfferLetterModel
        fields = [
            'id', 'application_id',
            'candidate_name', 'candidate_email',
            'job_title', 'company_name',
            'position_title', 'offered_salary',
            'joining_date', 'offer_expiry_date',
            'custom_message', 'offer_letter_url',
            'status', 'is_expired',
            'candidate_response_note', 'responded_at',
            'sent_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_candidate_name(self, obj):
        return f"{obj.application.first_name} {obj.application.last_name}"

    def get_candidate_email(self, obj):
        return obj.application.email