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
                'candidate__user',
            ).get(id=application_id)
        except ApplicationModel.DoesNotExist:
            return None
        
    def update_screening_status(self,application_id:int, status:str):
        """Update application status"""
        ApplicationModel.objects.filter(id=application_id).update(
            screening_status = status
        )

    def save_screening_results(self, application_id: int, result: Dict) -> bool:
        """Save screening results to database"""
        try:
            from application.models import ApplicationModel
            from resume_screening.models import ResumeScreeningResult
            from django.utils import timezone
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"📝 Saving screening results for application {application_id}")
            
            application = ApplicationModel.objects.get(id=application_id)
            
            # ✅ Extract data from result structure
            scores = result.get('scores', {})
            parsed_data = result.get('parsed_data', {})
            ai_analysis = result.get('ai_analysis', {})
            
            # ✅ 1. Save scores to ApplicationModel
            application.ats_overall_score = int(scores.get('overall', 0))
            application.ats_skills_score = int(scores.get('skills', 0))
            application.ats_experience_score = int(scores.get('experience', 0))
            application.ats_education_score = int(scores.get('education', 0))
            application.ats_keywords_score = int(scores.get('keywords', 0))
            
            # ✅ 2. Save decision
            application.ats_decision = result.get('decision', 'pending')
            
            # ✅ 3. Update screening status
            application.screening_status = 'completed'
            
            # ✅ 4. Update main status if qualified
            if result.get('decision') == 'qualified':
                application.status = 'qualified'
                application.current_stage_status = 'qualified'
            
            application.save()
            logger.info(f"✅ Saved scores to ApplicationModel")
            
            # ✅ 5. Save detailed results to ResumeScreeningResult
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
            logger.info(f"✅ {action} ResumeScreeningResult: {screening_result.id}")
            logger.info(f"   - Matched skills: {screening_result.matching_skills}")
            logger.info(f"   - AI Summary: {screening_result.ai_summary[:100]}...")
            
            return True
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to save screening results for application {application_id}: {e}")
            logger.error(f"❌ Result data: {result}")
            logger.error(traceback.format_exc())
            return False
        
    def update_job_progress(self, job_id: int):
        """Update job screening progress"""
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
            
            print(f"📊 Sending progress update: {progress_data}")  # Debug log
            
            notification_service.send_websocket_notification(
                user_id=job.recruiter.id,
                notification_type='screening_progress',
                data={
                    'job_id': job.id,
                    'progress': progress_data  # ✅ Match frontend structure
                }
            )
            
        except Exception as e:
            import traceback
            print(f"❌ Failed to update job progress: {str(e)}")
            print(traceback.format_exc())

    def get_pending_applications_by_job(self, job_id: int) -> List:
        """Get all pending applications for a job"""
        applications = ApplicationModel.objects.filter(
            job_id=job_id,
            current_stage__slug='resume-screening'
        ).filter(
            Q(screening_status='pending') | 
            Q(screening_status__isnull=True) |
            Q(screening_status='')
        ).exclude(
            screening_status='completed'
        ).values_list('id', flat=True)

        # Debug logging
        app_list = list(applications)
        print(f"🔍 Found {len(app_list)} pending applications for job {job_id}")
        print(f"📋 Application IDs: {app_list}")
    
        return app_list
    
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
        count = ApplicationModel.objects.filter(
            job_id=job_id,
            current_stage__slug='resume-screening'
        ).filter(
            Q(screening_status='pending') | 
            Q(screening_status__isnull=True) |
            Q(screening_status='')
        ).exclude(
            screening_status='completed'
        ).count()
        
        print(f"🔍 Pending applications count for job {job_id}: {count}")
        
        return count
    
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