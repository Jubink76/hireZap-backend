from rest_framework import serializers
from .models import (
    TelephonicRoundSettings,
    TelephonicInterview,
    CallSession,
    InterviewTranscription,
    InterviewPerformanceResult,
    InterviewFeedback
)


class TelephonicRoundSettingsSerializer(serializers.ModelSerializer):
    """Settings serializer - similar to ATSConfiguration"""
    
    class Meta:
        model = TelephonicRoundSettings
        fields = [
            'id',
            'job',
            'communication_weight',
            'technical_knowledge_weight',
            'problem_solving_weight',
            'enthusiasm_weight',
            'clarity_weight',
            'professionalism_weight',
            'minimum_qualifying_score',
            'default_duration_minutes',
            'auto_schedule_enabled',
            'send_reminders',
            'reminder_hours_before',
            'enable_recording',
            'enable_transcription',
            'enable_ai_analysis',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id','job', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate that weights sum to 100"""
        # For updates, get current values from instance
        if self.instance:
            total_weight = (
                data.get('communication_weight', self.instance.communication_weight) +
                data.get('technical_knowledge_weight', self.instance.technical_knowledge_weight) +
                data.get('problem_solving_weight', self.instance.problem_solving_weight) +
                data.get('enthusiasm_weight', self.instance.enthusiasm_weight) +
                data.get('clarity_weight', self.instance.clarity_weight) +
                data.get('professionalism_weight', self.instance.professionalism_weight)
            )
        else:
            # For creation, all weights must be provided
            total_weight = (
                data.get('communication_weight', 0) +
                data.get('technical_knowledge_weight', 0) +
                data.get('problem_solving_weight', 0) +
                data.get('enthusiasm_weight', 0) +
                data.get('clarity_weight', 0) +
                data.get('professionalism_weight', 0)
            )
        
        if total_weight != 100:
            raise serializers.ValidationError(
                f"Weights must sum to 100%. Current sum: {total_weight}"
            )
        return data


class ScheduleInterviewSerializer(serializers.Serializer):
    """Schedule single interview"""
    candidate_id = serializers.IntegerField(required=True)
    scheduled_at = serializers.DateTimeField(required=True)
    duration = serializers.IntegerField(required=False, default=30)
    timezone = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    send_notification = serializers.BooleanField(default=True)
    send_email = serializers.BooleanField(default=True)


class BulkScheduleSerializer(serializers.Serializer):
    """Bulk schedule interviews"""
    schedules = serializers.ListField(
        child=ScheduleInterviewSerializer(),
        min_length=1
    )


class RescheduleInterviewSerializer(serializers.Serializer):
    """Reschedule existing interview"""
    interview_id = serializers.IntegerField(required=True)
    scheduled_at = serializers.DateTimeField(required=True)
    duration = serializers.IntegerField(required=False)
    timezone = serializers.CharField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    send_notification = serializers.BooleanField(default=True)
    send_email = serializers.BooleanField(default=True)


class StartCallSerializer(serializers.Serializer):
    """Start call session"""
    interview_id = serializers.IntegerField(required=True)


class EndCallSerializer(serializers.Serializer):
    """End call and upload recording"""
    call_session_id = serializers.CharField(required=True)
    duration_seconds = serializers.IntegerField(required=True)
    recording_file = serializers.FileField(required=False, allow_null=True)
    connection_quality = serializers.ChoiceField(
        choices=['excellent', 'good', 'fair', 'poor'],
        default='good'
    )


class InterviewPerformanceResultSerializer(serializers.ModelSerializer):
    """Performance result serializer"""
    candidate_name = serializers.CharField(source='interview.candidate_name', read_only=True)
    interview_date = serializers.DateTimeField(source='interview.ended_at', read_only=True)
    final_score = serializers.IntegerField(read_only=True)
    final_decision = serializers.CharField(read_only=True)
    
    class Meta:
        model = InterviewPerformanceResult
        fields = [
            'id',
            'interview',
            'candidate_name',
            'interview_date',
            'overall_score',
            'communication_score',
            'technical_knowledge_score',
            'problem_solving_score',
            'enthusiasm_score',
            'clarity_score',
            'professionalism_score',
            'decision',
            'ai_summary',
            'key_highlights',
            'areas_for_improvement',
            'technical_assessment',
            'communication_assessment',
            'key_topics_discussed',
            'questions_asked_count',
            'manual_score_override',
            'manual_decision_override',
            'override_reason',
            'final_score',
            'final_decision',
            'created_at',
        ]
        read_only_fields = fields


class TelephonicInterviewSerializer(serializers.ModelSerializer):
    """Main interview serializer"""
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.CharField(source='application.email', read_only=True)
    candidate_phone = serializers.CharField(source='application.phone', read_only=True)
    
    # Performance data
    performance_score = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()
    performance_analysis = serializers.SerializerMethodField()
    
    # Recording
    recording_url = serializers.SerializerMethodField()
    call_duration = serializers.IntegerField(source='actual_duration_seconds', read_only=True)
    
    # Transcription
    has_transcription = serializers.SerializerMethodField()
    
    class Meta:
        model = TelephonicInterview
        fields = [
            'id',
            'application_id',
            'job_id',
            'stage_id',
            'candidate_name',
            'candidate_email',
            'candidate_phone',
            
            # Scheduling
            'status',
            'scheduled_at',
            'scheduled_duration_minutes',
            'timezone',
            
            # Actual timing
            'started_at',
            'ended_at',
            'call_duration',
            
            # Performance
            'performance_score',
            'performance_metrics',
            'performance_analysis',
            
            # Recording & transcription
            'recording_url',
            'has_transcription',
            
            # Notes
            'interviewer_notes',
            'scheduling_notes',
            
            # Metadata
            'notification_sent',
            'email_sent',
            'reminder_sent',
            'conducted_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_candidate_name(self, obj):
        return f"{obj.application.first_name} {obj.application.last_name}"
    
    def get_performance_score(self, obj):
        """Get overall performance score"""
        try:
            if hasattr(obj, 'performance_result'):
                return obj.performance_result.final_score
        except:
            pass
        return None
    
    def get_performance_metrics(self, obj):
        """Get detailed scores"""
        try:
            result = obj.performance_result
            return {
                'communication': result.communication_score,
                'technical_knowledge': result.technical_knowledge_score,
                'problem_solving': result.problem_solving_score,
                'enthusiasm': result.enthusiasm_score,
                'clarity': result.clarity_score,
                'professionalism': result.professionalism_score,
            }
        except:
            return None
    
    def get_performance_analysis(self, obj):
        """Get AI analysis"""
        try:
            result = obj.performance_result
            return {
                'summary': result.ai_summary,
                'highlights': result.key_highlights,
                'improvements': result.areas_for_improvement,
                'technical': result.technical_assessment,
                'communication': result.communication_assessment,
                'decision': result.final_decision,
            }
        except:
            return None
    
    def get_recording_url(self, obj):
        """Get recording URL"""
        try:
            if hasattr(obj, 'call_session'):
                return obj.call_session.recording_url
        except:
            pass
        return None
    
    def get_has_transcription(self, obj):
        """Check if transcription exists"""
        return hasattr(obj, 'transcription') and obj.transcription.processing_status == 'completed'


class TelephonicCandidateListSerializer(serializers.Serializer):
    """List serializer for candidates in telephonic round"""
    id = serializers.IntegerField(source='application.id')
    name = serializers.SerializerMethodField()
    email = serializers.CharField(source='application.email')
    phone = serializers.CharField(source='application.phone')
    
    # Interview status
    interview_status = serializers.CharField(source='status')
    interview_scheduled_at = serializers.DateTimeField(source='scheduled_at')
    interview_duration = serializers.IntegerField(source='scheduled_duration_minutes')
    interview_timezone = serializers.CharField(source='timezone')
    interview_notes = serializers.CharField(source='scheduling_notes')
    
    # Results
    interview_completed_at = serializers.DateTimeField(source='ended_at')
    call_duration = serializers.IntegerField(source='actual_duration_seconds')
    recording_url = serializers.SerializerMethodField()
    performance_score = serializers.SerializerMethodField()
    
    # Performance breakdown
    performance_metrics = serializers.SerializerMethodField()
    
    # Analysis
    key_highlights = serializers.SerializerMethodField()
    areas_for_improvement = serializers.SerializerMethodField()
    ai_summary = serializers.SerializerMethodField()
    
    # Stage info
    current_stage = serializers.CharField(source='application.current_stage.slug')
    status = serializers.CharField(source='application.current_stage_status')
    
    def get_name(self, obj):
        return f"{obj.application.first_name} {obj.application.last_name}"
    
    def get_recording_url(self, obj):
        try:
            return obj.call_session.recording_url
        except:
            return None
    
    def get_performance_score(self, obj):
        try:
            return obj.performance_result.final_score
        except:
            return None
    
    def get_performance_metrics(self, obj):
        try:
            result = obj.performance_result
            return {
                'communication': result.communication_score,
                'technical_knowledge': result.technical_knowledge_score,
                'problem_solving': result.problem_solving_score,
                'enthusiasm': result.enthusiasm_score,
                'clarity': result.clarity_score,
                'professionalism': result.professionalism_score,
            }
        except:
            return None
    
    def get_key_highlights(self, obj):
        try:
            return obj.performance_result.key_highlights
        except:
            return []
    
    def get_areas_for_improvement(self, obj):
        try:
            return obj.performance_result.areas_for_improvement
        except:
            return []
    
    def get_ai_summary(self, obj):
        try:
            return obj.performance_result.ai_summary
        except:
            return None


class ManualScoreOverrideSerializer(serializers.Serializer):
    """Manual score override"""
    interview_id = serializers.IntegerField(required=True)
    manual_score = serializers.IntegerField(
        required=True,
        min_value=0,
        max_value=100
    )
    manual_decision = serializers.ChoiceField(
        required=True,
        choices=['qualified', 'not_qualified']
    )
    override_reason = serializers.CharField(required=True)


class MoveToNextStageSerializer(serializers.Serializer):
    """Move candidates to next stage"""
    interview_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    feedback = serializers.CharField(required=False, allow_blank=True)