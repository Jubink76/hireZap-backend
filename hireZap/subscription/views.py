from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from core.use_cases.subscription.create_plan_usecase import CreatePlanUsecase

from infrastructure.repositories.subscription_plan_repository import SubscriptionPlanRepository
import logging
logger = logging.getLogger(__name__)

plan_repo = SubscriptionPlanRepository()
create_plan_usecase = CreatePlanUsecase(plan_repo)

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

