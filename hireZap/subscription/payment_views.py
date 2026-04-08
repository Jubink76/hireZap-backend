from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.use_cases.subscription.create_checkout_session_usecase import CreateCheckoutSessionUseCase
from core.use_cases.subscription.cancel_subscription_usecase import CancelSubscriptionUseCase
from infrastructure.repositories.user_subscription_repository import UserSubscriptionRepository


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        use_case = CreateCheckoutSessionUseCase()
        result = use_case.execute(user=request.user, plan_id=plan_id)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        use_case = CancelSubscriptionUseCase()
        result = use_case.execute(user_id=request.user.id)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = UserSubscriptionRepository()
        sub = repo.get_by_user(request.user.id)
        if not sub:
            return Response({'success': True, 'subscription': None})
        return Response({
            'success': True,
            'subscription': {
                'plan': sub.plan.name if sub.plan else None,
                'status': sub.status,
                'is_active': sub.is_active,
                'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            }
        })