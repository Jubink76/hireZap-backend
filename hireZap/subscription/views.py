from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from core.use_cases.subscription.create_plan_usecase import CreatePlanUsecase
from core.use_cases.subscription.get_all_plan_usecase import GetALLPlansUsecase
from core.use_cases.subscription.update_plan_usecase import UpdatelanUsecase
from core.use_cases.subscription.delete_plan_usecase import DeletePlanUsecase
from core.use_cases.subscription.reactivate_plan_usecase import ReactivatePlanUsecase
from core.use_cases.subscription.get_inactive_plan_usecase import GetInactivePlanUsecase

from infrastructure.repositories.subscription_plan_repository import SubscriptionPlanRepository
import logging
logger = logging.getLogger(__name__)

plan_repo = SubscriptionPlanRepository()
create_plan_usecase = CreatePlanUsecase(plan_repo)
get_all_plan_usecase = GetALLPlansUsecase(plan_repo)
update_plan_usecase = UpdatelanUsecase(plan_repo)
delete_plan_usecase = DeletePlanUsecase(plan_repo)
reactivate_plan_usecase = ReactivatePlanUsecase(plan_repo)
get_inactive_plan_usecase = GetInactivePlanUsecase(plan_repo)
# Create your views here.

class BaseSubscriptionPlanView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def __init___(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = SubscriptionPlanRepository()

class CreatePlanView(BaseSubscriptionPlanView):
    def post(self,request):
        result = create_plan_usecase.execute(request.data)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)
    
class GetAllPlanView(BaseSubscriptionPlanView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user_type = request.query_params.get('user_type', None)
        result = get_all_plan_usecase.execute(user_type)

        if not result['success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status = status.HTTP_200_OK)

class GetInactivePlanView(BaseSubscriptionPlanView):
    def get(self,request):
        user_type = request.query_params.get('user_type',None)
        result = get_inactive_plan_usecase.execute(user_type)

        if not result['success']:
            return Response(result,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(result, status=status.HTTP_200_OK)
    
class UpdatePlanView(BaseSubscriptionPlanView):
    def put(self,request,plan_id):
        result = update_plan_usecase.execute(plan_id, request.data)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class DeletePlanView(BaseSubscriptionPlanView):
    def delete(self,request, plan_id):
        result = delete_plan_usecase.execute(plan_id)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
    
class ReactivatePlanView(BaseSubscriptionPlanView):
    def patch(self,request, plan_id):
        result = reactivate_plan_usecase.execute(plan_id)
        if not result['success']:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if 'not found' in result.get('error', '').lower()
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)

