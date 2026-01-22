from rest_framework import serializers
from .models import (
    HRRoundSettings,
    HRInterview,
    MeetingSession,
    InterviewRecording,
    InterviewNotes,
    InterviewChatMessage,
    InterviewResult
)
from application.models import ApplicationModel
from job.models import JobModel


class HRRoundSettingsSerializer(serializers.ModelSerializer):
    """Serializer for HR Round Settings"""
    
    class Meta:
        model = HRRoundSettings
        fields = [
            'id', 'job', 'default_duration_minutes', 'auto_schedule_enabled',
            'send_reminders', 'reminder_hours_before', 'enable_recording',
            'enable_chat', 'communication_weight', 'culture_fit_weight',
            'motivation_weight', 'professionalism_weight', 'problem_solving_weight',
            'team_collaboration_weight', 'minimum_qualifying_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HRInterviewListSerializer(serializers.ModelSerializer):
    """List serializer for HR Interviews"""
    
    candidate_name = serializers.CharField(read_only=True)
    candidate_email = serializers.EmailField(source='application.email', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = HRInterview
        fields = [
            'id', 'application', 'job', 'stage', 'candidate_name',
            'candidate_email', 'job_title', 'company_name', 'stage_name',
            'scheduled_at', 'scheduled_duration_minutes', 'timezone',
            'status', 'is_upcoming', 'conducted_by', 'created_at'
        ]


class HRInterviewDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for HR Interviews"""
    
    candidate_name = serializers.CharField(read_only=True)
    candidate_email = serializers.EmailField(source='application.email', read_only=True)
    candidate_phone = serializers.CharField(source='application.phone', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    # Related data
    has_recording = serializers.SerializerMethodField()
    has_notes = serializers.SerializerMethodField()
    has_result = serializers.SerializerMethodField()
    
    class Meta:
        model = HRInterview
        fields = [
            'id', 'application', 'job', 'stage', 'candidate_name',
            'candidate_email', 'candidate_phone', 'job_title', 'company_name',
            'stage_name', 'scheduled_at', 'scheduled_duration_minutes',
            'timezone', 'status', 'started_at', 'ended_at', 'candidate_joined_at',
            'actual_duration_minutes', 'conducted_by', 'scheduling_notes',
            'cancellation_reason', 'meeting_link', 'is_upcoming',
            'has_recording', 'has_notes', 'has_result',
            'notification_sent', 'email_sent', 'reminder_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'started_at', 'ended_at', 'candidate_joined_at',
            'actual_duration_minutes', 'notification_sent', 'email_sent',
            'reminder_sent', 'created_at', 'updated_at'
        ]
    
    def get_has_recording(self, obj):
        return hasattr(obj, 'recording') and obj.recording.video_url is not None
    
    def get_has_notes(self, obj):
        return hasattr(obj, 'notes')
    
    def get_has_result(self, obj):
        return hasattr(obj, 'result')


class ScheduleHRInterviewSerializer(serializers.Serializer):
    """Serializer for scheduling HR interviews"""
    
    application_id = serializers.IntegerField()
    scheduled_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=15, max_value=180, default=45)
    timezone = serializers.CharField(default='Asia/Kolkata')
    scheduling_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_application_id(self, value):
        """Validate application exists"""
        if not ApplicationModel.objects.filter(id=value).exists():
            raise serializers.ValidationError("Application not found")
        return value


class BulkScheduleHRInterviewSerializer(serializers.Serializer):
    """Serializer for bulk scheduling"""
    
    application_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50
    )
    scheduled_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=15, max_value=180, default=45)
    timezone = serializers.CharField(default='Asia/Kolkata')
    scheduling_notes = serializers.CharField(required=False, allow_blank=True)


class MeetingSessionSerializer(serializers.ModelSerializer):
    """Serializer for Meeting Sessions"""
    
    interview_id = serializers.IntegerField(source='interview.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate_name', read_only=True)
    
    class Meta:
        model = MeetingSession
        fields = [
            'id', 'interview', 'interview_id', 'candidate_name',
            'session_id', 'room_id', 'recruiter_id', 'candidate_id',
            'recruiter_connected', 'candidate_connected', 'is_recording',
            'recording_started_at', 'recording_stopped_at', 'connection_quality',
            'started_at', 'recruiter_joined_at', 'candidate_joined_at',
            'ended_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'started_at', 'created_at', 'updated_at'
        ]


class InterviewRecordingSerializer(serializers.ModelSerializer):
    """Serializer for Interview Recordings"""
    
    interview_id = serializers.IntegerField(source='interview.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate_name', read_only=True)
    
    class Meta:
        model = InterviewRecording
        fields = [
            'id', 'interview', 'interview_id', 'candidate_name',
            'video_url', 'video_key', 'thumbnail_url', 'thumbnail_key',
            'duration_seconds', 'file_size_bytes', 'video_format',
            'resolution', 'processing_status', 'processing_error',
            'upload_started_at', 'upload_completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'processing_status', 'processing_error',
            'upload_started_at', 'upload_completed_at',
            'created_at', 'updated_at'
        ]


class InterviewNotesSerializer(serializers.ModelSerializer):
    """Serializer for Interview Notes"""
    
    interview_id = serializers.IntegerField(source='interview.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate_name', read_only=True)
    recorder_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = InterviewNotes
        fields = [
            'id', 'interview', 'interview_id', 'candidate_name',
            'recorded_by', 'recorder_name',
            'communication_rating', 'communication_notes',
            'culture_fit_rating', 'culture_fit_notes',
            'motivation_rating', 'motivation_notes',
            'professionalism_rating', 'professionalism_notes',
            'problem_solving_rating', 'problem_solving_notes',
            'team_collaboration_rating', 'team_collaboration_notes',
            'overall_impression', 'strengths', 'areas_for_improvement',
            'general_notes', 'calculated_score', 'recommendation',
            'is_finalized', 'finalized_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'calculated_score', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Calculate score before saving"""
        notes = InterviewNotes(**data)
        calculated = notes.calculate_weighted_score()
        if calculated is not None:
            data['calculated_score'] = calculated
        return data


class InterviewChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for Chat Messages"""
    
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = InterviewChatMessage
        fields = [
            'id', 'interview', 'sender_id', 'sender_type',
            'sender_name', 'message', 'is_system_message',
            'read_by_recipient', 'sent_at'
        ]
        read_only_fields = ['id', 'sent_at']
    
    def get_sender_name(self, obj):
        """Get sender name based on type"""
        if obj.sender_type == 'recruiter':
            return "Recruiter"
        elif obj.sender_type == 'candidate':
            return obj.interview.candidate_name
        return "System"


class InterviewResultSerializer(serializers.ModelSerializer):
    """Serializer for Interview Results"""
    
    interview_id = serializers.IntegerField(source='interview.id', read_only=True)
    candidate_name = serializers.CharField(source='interview.candidate_name', read_only=True)
    job_title = serializers.CharField(source='interview.job.job_title', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    
    class Meta:
        model = InterviewResult
        fields = [
            'id', 'interview', 'interview_id', 'candidate_name', 'job_title',
            'final_score', 'decision', 'decision_reason', 'next_steps',
            'decided_by', 'decided_by_name', 'decided_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'decided_at', 'created_at', 'updated_at'
        ]


class UpdateInterviewStatusSerializer(serializers.Serializer):
    """Serializer for updating interview status"""
    
    status = serializers.ChoiceField(
        choices=['in_progress', 'completed', 'cancelled', 'no_show']
    )
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class StartRecordingSerializer(serializers.Serializer):
    """Serializer for starting recording"""
    
    session_id = serializers.CharField()


class StopRecordingSerializer(serializers.Serializer):
    """Serializer for stopping recording"""
    
    session_id = serializers.CharField()
    duration_seconds = serializers.IntegerField(required=False)


class UploadRecordingSerializer(serializers.Serializer):
    """Serializer for uploading recording"""
    
    interview_id = serializers.IntegerField()
    video_file = serializers.FileField()
    duration_seconds = serializers.IntegerField(required=False)
    resolution = serializers.CharField(required=False)
    
    def validate_video_file(self, value):
        """Validate video file"""
        # Check file size (max 500MB)
        max_size = 500 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size exceeds 500MB limit")
        
        # Check file extension
        import os
        allowed_formats = ['.webm', '.mp4', '.mkv']
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in allowed_formats:
            raise serializers.ValidationError(
                f"Invalid format. Allowed: {', '.join(allowed_formats)}"
            )
        
        return value