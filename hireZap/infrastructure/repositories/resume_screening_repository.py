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

import logging
import traceback
logger = logging.getLogger(__name__)

class ResumeScreeningRepository(ResumeScreeningRepositoryPort):

    def get_application_by_id(self,application_id:int):
        try:
            return ApplicationModel.objects.select_related(
                'job',
                'candidate__user',
            ).get(id=application_id)
        except ApplicationModel.DoesNotExist:
            return None
        
    def update_screening_status(self,application_id:int, status:str):
        ApplicationModel.objects.filter(id=application_id).update(
            screening_status = status
        )

    def save_screening_results(self, application_id: int, result: Dict) -> bool:
        try:
            from application.models import ApplicationModel
            from resume_screening.models import ResumeScreeningResult
            from django.utils import timezone

            logger.info(f" Saving screening results for application {application_id}")
            
            application = ApplicationModel.objects.get(id=application_id)
            
            scores = result.get('scores', {})
            parsed_data = result.get('parsed_data', {})
            ai_analysis = result.get('ai_analysis', {})
            
            #Save scores to ApplicationModel
            application.ats_overall_score = int(scores.get('overall', 0))
            application.ats_skills_score = int(scores.get('skills', 0))
            application.ats_experience_score = int(scores.get('experience', 0))
            application.ats_education_score = int(scores.get('education', 0))
            application.ats_keywords_score = int(scores.get('keywords', 0))
            
            #Save decision
            application.ats_decision = result.get('decision', 'pending')
            
            #Update screening status
            application.screening_status = 'completed'
            
            #Update main status if qualified
            if result.get('decision') == 'qualified':
                application.status = 'qualified'
                application.current_stage_status = 'qualified'
            
            application.save()
            logger.info(f"Saved scores to ApplicationModel")
            
            #Save detailed results to ResumeScreeningResult
            screening_result, created = ResumeScreeningResult.objects.update_or_create(
                application=application,
                defaults={
                    # Extract from parsed_data
                    'matching_skills': parsed_data.get('matched_skills', []),
                    'missing_required_skills': parsed_data.get('missing_skills', []),
                    'matched_keywords': parsed_data.get('matched_keywords', []),
                    'extracted_experience_years': parsed_data.get('experience_years', 0),
                    'extracted_education': parsed_data.get('education', ''),
                    
                    # ATS friendliness
                    'is_ats_friendly': result.get('ats_friendly', True),
                    'ats_issues': result.get('ats_issues', []),
                    
                    # Extract from ai_analysis
                    'ai_summary': ai_analysis.get('summary', ''),
                    'strengths': ai_analysis.get('strengths', []),
                    'weaknesses': ai_analysis.get('weaknesses', []),
                    'recommendation_notes': ai_analysis.get('notes', ''),
                    
                    # Metadata
                    'processing_time_seconds': result.get('processing_time', 0),
                    'screening_at': timezone.now(),
                }
            )
            
            action = "Created" if created else "Updated"
            logger.info(f" {action} ResumeScreeningResult: {screening_result.id}")
            logger.info(f"   - Matched skills: {screening_result.matching_skills}")
            logger.info(f"   - AI Summary: {screening_result.ai_summary[:100]}...")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to save screening results for application {application_id}: {e}")
            logger.error(f" Result data: {result}")
            logger.error(traceback.format_exc())
            return False
        
    def update_job_progress(self, job_id: int):
        try: 
            job = JobModel.objects.get(id=job_id)
            
            # Count screened applications
            screened_count = ApplicationModel.objects.filter(
                job=job,
                screening_status='completed'
            ).count()
            
            job.screened_applications_count = screened_count
            
            # Check if all completed
            total_count = ApplicationModel.objects.filter(job=job).count()
            percentage = (screened_count / total_count * 100) if total_count > 0 else 0
            
            if screened_count >= total_count and job.screening_status == 'in_progress':
                job.screening_status = 'completed'
                job.screening_completed_at = timezone.now()
            
            job.save()
            
            # Send WebSocket update
            from infrastructure.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            progress_data = {
                'status': job.screening_status,
                'total_applications': total_count,
                'screened_applications': screened_count,
                'percentage': round(percentage, 2)
            }
            
            logger.info(f" Sending progress update: {progress_data}")
            
            notification_service.send_websocket_notification(
                user_id=job.recruiter.id,
                notification_type='screening_progress',
                data={
                    'job_id': job.id,
                    'progress': progress_data  
                }
            )
            
        except Exception as e:
            import traceback
            logger.info(f" Failed to update job progress: {str(e)}")
            print(traceback.format_exc())

    def get_pending_applications_by_job(self, job_id: int) -> List:
        all_apps = ApplicationModel.objects.filter(job_id=job_id)
        logger.info(f"Total applications for job {job_id}: {all_apps.count()}")
        for app in all_apps:
            logger.info(f"  App {app.id}: is_draft={app.is_draft}, "
                        f"screening_status={app.screening_status}, "
                        f"current_stage={app.current_stage}, "
                        f"current_stage_slug={app.current_stage.slug if app.current_stage else 'NULL'}")

        applications = ApplicationModel.objects.filter(
            job_id=job_id,
            is_draft=False,
        ).filter(
            Q(current_stage__isnull=True) |
            Q(current_stage__slug='resume-screening')
        ).filter(
            Q(screening_status='pending') |
            Q(screening_status='failed')
        ).values_list('id', flat=True)

        result = list(applications)
        logger.info(f"Filtered pending applications: {result}")
        return result
    
    def mark_screening_as_failed(self, application_id: int, error: str, retry_count: int):
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
        update_data = {'screening_status': status}
        
        if status == 'in_progress':
            update_data['screening_started_at'] = timezone.now()
        elif status == 'completed':
            update_data['screening_completed_at'] = timezone.now()
        
        # Add any additional fields from kwargs
        update_data.update(kwargs)
        
        JobModel.objects.filter(id=job_id).update(**update_data)
    
    def check_all_screening_complete(self, job_id: int) -> bool:
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
        count = ApplicationModel.objects.filter(
            job_id=job_id,
            is_draft=False,
        ).filter(
            Q(current_stage__isnull=True) |
            Q(current_stage__slug='resume-screening')
        ).filter(
            Q(screening_status='pending') |
            Q(screening_status='failed')
        ).count()

        logger.info(f"Pending applications count for job {job_id}: {count}")
        return count
    
    def get_screening_results(self, job_id: int, filters: Optional[Dict] = None) -> List[Dict]:
        # Base query
        queryset = ApplicationModel.objects.filter(
            job_id=job_id,
            screening_status='completed'
        ).select_related(
            'candidate',
            'candidate__user',
            'current_stage',
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
                        'id'   : application.candidate.user_id,
                        'name' : application.candidate.user.full_name,
                        'email': application.candidate.user.email,
                    },
                    'scores': {
                        'overall'   : application.ats_overall_score,
                        'skills'    : application.ats_skills_score,
                        'experience': application.ats_experience_score,
                        'education' : application.ats_education_score,
                        'keywords'  : application.ats_keywords_score,
                    },
                    'decision'   : application.ats_decision,
                    'status'     : application.current_stage_status,
                    'current_stage': {
                        'slug': application.current_stage.slug if application.current_stage else None,
                        'name': application.current_stage.name if application.current_stage else None,
                    },
                    'details': {
                        'matched_skills'     : screening_result.matching_skills,
                        'missing_skills'     : screening_result.missing_required_skills,
                        'experience_years'   : screening_result.extracted_experience_years,
                        'education'          : screening_result.extracted_education,
                        'is_ats_friendly'    : screening_result.is_ats_friendly,
                        'ats_issues'         : screening_result.ats_issues,
                        'ai_summary'         : screening_result.ai_summary,
                        'strengths'          : screening_result.strengths,
                        'weaknesses'         : screening_result.weaknesses,
                    },
                    'screened_at': screening_result.created_at.isoformat() if screening_result.created_at else None,
                })
            except ResumeScreeningResult.DoesNotExist:
                continue
        
        return results
    
    def move_to_next_stage(self, application_id: int, feedback: str = None) -> Dict:
        try:
            application = ApplicationModel.objects.select_related(
                'current_stage',
                'job',
                'candidate__user'
            ).get(id=application_id)
            
            # Get current stage
            current_stage = application.current_stage
            
            # Check if qualified
            if current_stage.slug == 'resume-screening':
                if application.ats_decision != 'qualified':
                    return {'success': False, 'error': 'Candidate not qualified in resume screening'}
            else:
                history = ApplicationStageHistory.objects.filter(
                    application=application, stage=current_stage
                ).first()
                if history and history.status == 'rejected':
                    return {'success': False, 'error': 'Candidate was rejected in this stage'}
            
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
            
            
            application.current_stage = next_stage
            application.current_stage_status = 'pending'
            application.status='qualified'
            application.save(update_fields=['current_stage', 'current_stage_status','status','updated_at'])
            
            # Create new stage history
            ApplicationStageHistory.objects.update_or_create(
                application=application,
                stage=next_stage,
                defaults={                   
                    'status': 'started',
                    'feedback': None,
                    'completed_at': None,
                }
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
        

    def reset_job_screening(self, job_id: int):
        JobModel.objects.filter(id=job_id).update(
            screening_status='not_started',
            screened_applications_count=0,
            screening_started_at=None,
            screening_completed_at=None
        )

    def reset_applications_for_job(self, job_id: int):
        ApplicationModel.objects.filter(job_id=job_id).update(
            screening_status='pending',
            ats_overall_score=None,
            ats_skills_score=None,
            ats_experience_score=None,
            ats_education_score=None,
            ats_keywords_score=None,
            ats_decision='pending'
        )

    def delete_screening_results(self, job_id: int):
        ResumeScreeningResult.objects.filter(
            application__job_id=job_id
        ).delete()

    def lock_job_for_applications(self,job_id:int):
        JobModel.objects.filter(id=job_id).update(
            screening_status = 'in_progress',
            screening_started = timezone.now()
        )
        logger.info(f" Job {job_id} locked — no new applications accepted")