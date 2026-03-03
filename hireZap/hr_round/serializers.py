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
    candidate_name = serializers.CharField(read_only=True)
    candidate_email = serializers.EmailField(source='application.email', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    overall_score = serializers.SerializerMethodField()
    result_decision = serializers.SerializerMethodField()
    has_recording = serializers.SerializerMethodField()
    has_notes = serializers.SerializerMethodField()
    actual_duration_seconds = serializers.SerializerMethodField()
    meeting_session = serializers.SerializerMethodField()
    application_id = serializers.IntegerField(source='application.id', read_only=True)
    
    class Meta:
        model = HRInterview
        fields = [
            'id', 'application','application_id', 'job', 'stage', 'candidate_name',
            'candidate_email', 'job_title', 'company_name', 'stage_name',
            'scheduled_at', 'scheduled_duration_minutes', 'timezone',
            'status', 'is_upcoming', 'conducted_by', 'created_at',
            'started_at', 'ended_at', 'actual_duration_seconds',
            'overall_score', 'result_decision', 'has_recording', 'has_notes',
            'meeting_session',
        ]
    def get_overall_score(self, obj):
        try:
            return obj.result.final_score
        except:
            return None

    def get_result_decision(self, obj):
        try:
            return obj.result.decision  # 'qualified', 'not_qualified', 'pending_review'
        except:
            return None

    def get_has_recording(self, obj):
        try:
            return hasattr(obj, 'recording') and obj.recording.video_url is not None
        except:
            return False

    def get_has_notes(self, obj):
        return hasattr(obj, 'notes')

    def get_actual_duration_seconds(self, obj):
        if obj.actual_duration_minutes:
            return obj.actual_duration_minutes * 60
        return None

    def get_meeting_session(self, obj):
        try:
            session = obj.meeting_session
            return {
                'session_id': session.session_id,
                'recruiter_connected': session.recruiter_connected,
                'candidate_connected': session.candidate_connected,
            }
        except:
            return None


class HRInterviewDetailSerializer(serializers.ModelSerializer):
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
    
    notes = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    recording = serializers.SerializerMethodField()

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
            'notes', 'result', 'recording',
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
    def get_notes(self, obj):
        try:
            n = obj.notes
            return {
                'communication_rating':       n.communication_rating,
                'communication_notes':        n.communication_notes,
                'culture_fit_rating':         n.culture_fit_rating,
                'culture_fit_notes':          n.culture_fit_notes,
                'motivation_rating':          n.motivation_rating,
                'motivation_notes':           n.motivation_notes,
                'professionalism_rating':     n.professionalism_rating,
                'professionalism_notes':      n.professionalism_notes,
                'problem_solving_rating':     n.problem_solving_rating,
                'problem_solving_notes':      n.problem_solving_notes,
                'team_collaboration_rating':  n.team_collaboration_rating,
                'team_collaboration_notes':   n.team_collaboration_notes,
                'overall_impression':         n.overall_impression,
                'strengths':                  n.strengths,
                'areas_for_improvement':      n.areas_for_improvement,
                'general_notes':              n.general_notes,
                'calculated_score':           n.calculated_score,
                'recommendation':             n.recommendation,
                'is_finalized':               n.is_finalized,
                'finalized_at':               n.finalized_at.isoformat() if n.finalized_at else None,
            }
        except Exception:
            return None
        
    def get_result(self, obj):
        try:
            r = obj.result
            return {
                'final_score':    r.final_score,
                'decision':       r.decision,        # 'qualified' | 'not_qualified' | 'pending_review'
                'decision_reason': r.decision_reason,
                'next_steps':     r.next_steps,
                'decided_at':     r.decided_at.isoformat() if r.decided_at else None,
            }
        except Exception:
            return None

    def get_recording(self, obj):
        try:
            rec = obj.recording
            if not rec.video_url:
                return None
            return {
                'video_url':        rec.video_url,
                'thumbnail_url':    rec.thumbnail_url,
                'duration_seconds': rec.duration_seconds,
                'processing_status': rec.processing_status,
            }
        except Exception:
            return None

class ScheduleHRInterviewSerializer(serializers.Serializer):
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
    status = serializers.ChoiceField(
        choices=['in_progress', 'completed', 'cancelled', 'no_show']
    )
    cancellation_reason = serializers.CharField(required=False, allow_blank=True)


class StartRecordingSerializer(serializers.Serializer):
    session_id = serializers.CharField()


class StopRecordingSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    duration_seconds = serializers.IntegerField(required=False)


class UploadRecordingSerializer(serializers.Serializer):
    interview_id = serializers.IntegerField()
    video_file = serializers.FileField()
    duration_seconds = serializers.IntegerField(required=False)
    resolution = serializers.CharField(required=False)
    
    def validate_video_file(self, value):
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

class HRMoveToNextStageSerializer(serializers.Serializer):
    interview_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    feedback = serializers.CharField(required=False, allow_blank=True)