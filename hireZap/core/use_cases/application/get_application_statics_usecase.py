from core.interface.application_repository_port import ApplicationRepositoryPort

class GetApplicationStatisticsUsecase:
    def __init__(self,repository:ApplicationRepositoryPort):
        self.repository = repository
    
    def execute(self,job_id:int) -> dict:
        """Get application statistics for a job"""
        try:
            all_applications = self.repository.get_applications_by_job(job_id)
            
            status_counts = {}
            for app in all_applications:
                status_counts[app.status] = status_counts.get(app.status, 0) + 1
            
            return {
                'success': True,
                'data': {
                    'total_applications': len(all_applications),
                    'status_breakdown': status_counts,
                    'applied': status_counts.get('applied', 0),
                    'under_review': status_counts.get('under_review', 0),
                    'shortlisted': status_counts.get('shortlisted', 0),
                    'interviewed': status_counts.get('interviewed', 0),
                    'offered': status_counts.get('offered', 0),
                    'rejected': status_counts.get('rejected', 0),
                    'hired': status_counts.get('hired', 0),
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }