from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone

from core.interface.resume_screening_repository_port import ResumeScreeningRepositoryPort
from application.models import ApplicationModel
from job.models import JobModel
from resume_screening.models import ResumeScreeningResult
from application.models import ApplicationModel, ApplicationStageHistory
from selection_process.models import SelectionProcessModel
from django.utils import timezone
from django.db.models import Q

class ResumeScreeningRepository(ResumeScreeningRepositoryPort):

    def get_application_by_id(self,application_id:int):
        """Get application with related data"""
        try:
            return ApplicationModel.objects.select_related(
                'job',
                'candidate__user'
            ).get(id=application_id)
        except ApplicationModel.DoesNotExist:
            return None
        
    def update_screening_status(self,application_id:int, status:str):
        """Update application status"""
        ApplicationModel.objects.filter(id=application_id).update(
            screening_status = status
        )

    def save_screening_results(self, application_id:int, results:Dict) -> bool:
        """Save complete result (atomic transaction)"""
        try:
            with transaction.atomic():
                application = ApplicationModel.objects.get(id=application_id)
                # Update application scores
                application.ats_overall_score = results['scores']['overall']
                application.ats_skills_score = results['scores']['skills']
                application.ats_experience_score = results['scores']['experience']
                application.ats_education_score = results['scores']['education']
                application.ats_keywords_score = results['scores']['keywords']
                application.ats_decision = results['decision']
                application.screening_status = 'completed'
                
                # Update application status based on decision
                if results['decision'] == 'qualified':
                    application.status = 'under_review'
                    application.current_stage_status = 'completed'
                else:
                    application.status = 'rejected'
                    application.current_stage_status = 'rejected'
                
                application.save()
                
                # Save detailed results
                ResumeScreeningResult.objects.update_or_create(
                    application=application,
                    defaults={
                        'matched_skills': results['parsed_data']['matched_skills'],
                        'missing_required_skills': results['parsed_data']['missing_skills'],
                        'matched_keywords': results['parsed_data']['matched_keywords'],
                        'extracted_experience_years': results['parsed_data']['experience_years'],
                        'experience_meets_requirement': results['scores']['experience'] >= 60,
                        'extracted_education': results['parsed_data']['education'],
                        'education_meets_requirement': results['scores']['education'] >= 60,
                        'is_ats_friendly': results['ats_friendly'],
                        'ats_issues': results['ats_issues'],
                        'ai_summary': results['ai_analysis']['summary'],
                        'strengths': results['ai_analysis']['strengths'],
                        'weaknesses': results['ai_analysis']['weaknesses'],
                        'recommendation_notes': results['ai_analysis']['notes'],
                        'processing_time_seconds': results['processing_time'],
                        'screened_at': timezone.now(),
                    }
                )
                
                return True
                
        except Exception as e:
            print(f"Error saving screening results: {str(e)}")
            return False
        
    def update_job_progress(self, job_id: int):
        """Update job screening progress count"""
        try:
            job = JobModel.objects.get(id=job_id)
            job.screened_applications_count = ApplicationModel.objects.filter(
                job=job,
                screening_status='completed'
            ).count()
            job.save(update_fields=['screened_applications_count'])
        except JobModel.DoesNotExist:
            pass

    def get_pending_applications_by_job(self, job_id: int) -> List:
        """Get all pending applications for a job"""
        return list(ApplicationModel.objects.filter(
            job_id=job_id,
            current_stage__slug='resume-screening',
            screening_status='pending'
        ).values_list('id', flat=True))
    
    def mark_screening_as_failed(self, application_id: int, error: str, retry_count: int):
        """Mark application screening as failed"""
        try:
            application = ApplicationModel.objects.get(id=application_id)
            application.screening_status = 'failed'
            application.save(update_fields=['screening_status'])
            
            # Save failure reason
            ResumeScreeningResult.objects.update_or_create(
                application=application,
                defaults={
                    'failure_reason': error,
                    'retry_count': retry_count,
                }
            )
        except ApplicationModel.DoesNotExist:
            pass
    
    def update_job_screening_status(self, job_id: int, status: str, **kwargs):
        """Update job screening status"""
        update_data = {'screening_status': status}
        
        if status == 'in_progress':
            update_data['screening_started_at'] = timezone.now()
        elif status == 'completed':
            update_data['screening_completed_at'] = timezone.now()
        
        # Add any additional fields from kwargs
        update_data.update(kwargs)
        
        JobModel.objects.filter(id=job_id).update(**update_data)
    
    def check_all_screening_complete(self, job_id: int) -> bool:
        """Check if all applications are screened"""
        pending_count = ApplicationModel.objects.filter(
            job_id=job_id,
            screening_status__in=['pending', 'processing']
        ).count()
        return pending_count == 0
    
    def get_job_by_id(self, job_id: int):
        """Get job by ID"""
        try:
            return JobModel.objects.get(id=job_id)
        except JobModel.DoesNotExist:
            return None
    
    def get_pending_applications_count(self, job_id: int) -> int:
        """Get count of pending applications"""
        return ApplicationModel.objects.filter(
            job_id=job_id,
            current_stage__slug='resume-screening',
            screening_status='pending'
        ).count()
    
    def get_screening_results(self, job_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        """Get screening results for a job with filters"""
        # Base query
        queryset = ApplicationModel.objects.filter(
            job_id=job_id,
            screening_status='completed'
        ).select_related(
            'candidate__user',
            'screening_result'
        ).order_by('-ats_overall_score')
        
        # Apply filters
        if filters:
            if filters.get('decision'):
                queryset = queryset.filter(ats_decision=filters['decision'])
            
            if filters.get('min_score'):
                queryset = queryset.filter(ats_overall_score__gte=filters['min_score'])
            
            if filters.get('max_score'):
                queryset = queryset.filter(ats_overall_score__lte=filters['max_score'])
        
        # Serialize results
        results = []
        for application in queryset:
            try:
                screening_result = application.screening_result
                results.append({
                    'application_id': application.id,
                    'candidate': {
                        'id': application.candidate.id,
                        'name': application.candidate.get_full_name(),
                        'email': application.email,
                    },
                    'scores': {
                        'overall': application.ats_overall_score,
                        'skills': application.ats_skills_score,
                        'experience': application.ats_experience_score,
                        'education': application.ats_education_score,
                        'keywords': application.ats_keywords_score,
                    },
                    'decision': application.ats_decision,
                    'status': application.current_stage_status,
                    'details': {
                        'matched_skills': screening_result.matched_skills,
                        'missing_skills': screening_result.missing_required_skills,
                        'experience_years': screening_result.extracted_experience_years,
                        'education': screening_result.extracted_education,
                        'is_ats_friendly': screening_result.is_ats_friendly,
                        'ats_issues': screening_result.ats_issues,
                        'ai_summary': screening_result.ai_summary,
                        'strengths': screening_result.strengths,
                        'weaknesses': screening_result.weaknesses,
                    },
                    'screened_at': screening_result.screened_at.isoformat() if screening_result.screened_at else None,
                })
            except ResumeScreeningResult.DoesNotExist:
                continue
        
        return results
    
    def move_to_next_stage(self, application_id: int, feedback: str = None) -> Dict:
        """Move application to next stage"""
        
        try:
            application = ApplicationModel.objects.select_related(
                'current_stage',
                'job',
                'candidate__user'
            ).get(id=application_id)
            
            # Get current stage
            current_stage = application.current_stage
            
            # Check if qualified
            if application.ats_decision != 'qualified':
                return {
                    'success': False,
                    'error': 'Candidate not qualified'
                }
            
            # Get job stages in order
            job_stages = SelectionProcessModel.objects.filter(
                job=application.job,
                is_active=True
            ).order_by('order')
            
            # Find current stage index
            stage_list = list(job_stages)
            current_index = next(
                (i for i, s in enumerate(stage_list) if s.stage.id == current_stage.id),
                None
            )
            
            if current_index is None:
                return {
                    'success': False,
                    'error': 'Current stage not found'
                }
            
            # Check if there's a next stage
            if current_index + 1 >= len(stage_list):
                return {
                    'success': False,
                    'error': 'Already at final stage'
                }
            
            next_stage = stage_list[current_index + 1].stage
            
            # Update current stage history
            ApplicationStageHistory.objects.filter(
                application=application,
                stage=current_stage
            ).update(
                status='qualified',
                completed_at=timezone.now(),
                feedback=feedback
            )
            
            # Move to next stage
            application.current_stage = next_stage
            application.current_stage_status = 'pending'
            application.save()
            
            # Create new stage history
            ApplicationStageHistory.objects.create(
                application=application,
                stage=next_stage,
                status='started'
            )
            
            return {
                'success': True,
                'application_id': application_id,
                'current_stage': current_stage.name,
                'next_stage': next_stage.name
            }
            
        except ApplicationModel.DoesNotExist:
            return {
                'success': False,
                'error': 'Application not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }