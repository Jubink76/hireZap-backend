from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from core.use_cases.selection_process.create_stage_usecase import CreateStageUsecase
from core.use_cases.selection_process.get_all_stage_usecase import GetAllStageUsecase
from core.use_cases.selection_process.get_stage_by_id_usecase import GetStageByIdUsecase
from core.use_cases.selection_process.update_stage_usecase import UpdateStageUsecase
from core.use_cases.selection_process.delete_stage_usecase import DeleteStageUsecase
from core.use_cases.selection_process.get_inactive_stages_usecase import GetInactiveStages
from core.use_cases.selection_process.reactivate_stage_usecase import ReactivateStageUsecase
from core.use_cases.selection_process.save_job_selection_process_usecase import SaveJobSelectionProcessUsecase
from core.use_cases.selection_process.get_job_selection_process_usecase import GetJobSelectionProcessUsecase

from infrastructure.repositories.selection_stage_repository import SelectionStageRepository
from infrastructure.repositories.job_selection_process_repository import JobSelectionProcessRepository

import logging
logger = logging.getLogger(__name__)

stage_repo =  SelectionStageRepository()
job_selection_repo = JobSelectionProcessRepository()
create_stage_usecase =CreateStageUsecase(stage_repo)
get_all_stage_usecase = GetAllStageUsecase(stage_repo)
get_stage_by_id_usecase = GetStageByIdUsecase(stage_repo)
update_stage_usecase = UpdateStageUsecase(stage_repo)
delete_stage_usecase = DeleteStageUsecase(stage_repo)
get_inactive_stage_usecase = GetInactiveStages(stage_repo)
reactivate_stage_usecase = ReactivateStageUsecase(stage_repo)
save_job_selection_process_usecase = SaveJobSelectionProcessUsecase(job_selection_repo)
get_job_selection_process_usecase = GetJobSelectionProcessUsecase(job_selection_repo)

class BaseSelectionStageView(APIView):
    """Base view with common setup"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = SelectionStageRepository()


class CreateStageView(BaseSelectionStageView):
    def post(self,request):
        result = create_stage_usecase.execute(request.data)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_201_CREATED)
    
class GetAllStagesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        result = get_all_stage_usecase.execute()
        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)
    
class GetStageById(BaseSelectionStageView):
    def get(self,request,stage_id):
        result = get_stage_by_id_usecase.execute(stage_id)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class UpdateStageView(BaseSelectionStageView):
    def put(self,request,stage_id):
        result = update_stage_usecase.execute(stage_id, request.data)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class DeleteStageView(BaseSelectionStageView):
    def delete(self,request, stage_id):
        result = delete_stage_usecase.execute(stage_id)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class GetInactiveStagesView(BaseSelectionStageView):
    def get(self, request):
        result = get_inactive_stage_usecase.execute()
        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)
    
class ReactivateStageView(BaseSelectionStageView):
    def patch(self, request, stage_id):
        result = reactivate_stage_usecase.execute(stage_id)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class SaveJobSelectionProcessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, job_id):
        stage_ids = request.data.get('stage_ids', [])
        
        if not stage_ids:
            return Response(
                {'success': False, 'error': 'stage_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        result = save_job_selection_process_usecase.execute(job_id,stage_ids)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
    

class GetJobSelectionProcessView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        """Get selection stages for a job"""
        result = get_job_selection_process_usecase.execute(job_id)
        
        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)
    
class DeleteJobSelectionProcessView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self,request, job_id):
        try:
            success = job_selection_repo.delete_job_selection_process(job_id)
            if success:
                return Response(
                    {
                        'success': True,
                        'message': 'Selection process deleted successfully'
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'success': False,
                        'error': 'Failed to delete selection process'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error deleting selection process: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )