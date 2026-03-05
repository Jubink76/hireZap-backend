from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from infrastructure.repositories.offer_repository import OfferRepository
from core.use_cases.offer.send_offer_usecase import SendOfferUseCase, BulkSendOfferUseCase
from core.use_cases.offer.respond_offer_usecase import RespondToOfferUseCase
from core.use_cases.offer.get_offer_usecase import GetRankedCandidatesUseCase, GetOfferDetailUseCase
from offer.serializers import (
    SendOfferSerializer,
    BulkSendOfferSerializer,
    CandidateRespondSerializer,
    OfferLetterSerializer
)
from infrastructure.services.notification_service import NotificationService
from infrastructure.services.r2_storage import R2Storage

import logging
logger = logging.getLogger(__name__)

class RankedCandidatesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            repository = OfferRepository()
            result = GetRankedCandidatesUseCase(repository).execute(job_id)
            return Response({
                'success':True,
                'total':result['total'],
                'candidates':result['candidates'],
            })
        except Exception as e:
            logger.error(f"Ranked candidate view error: {e}")
            return Response({
                'success':False,
                'error':str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, application_id):
        try:
            serializer = SendOfferSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'succsss':False,
                    'errors':serializer.errors
                },status=status.HTTP_400_BAD_REQUEST)
            
            repository = OfferRepository()
            notification_service = NotificationService()
            storage = R2Storage()

            result = SendOfferUseCase(repository, notification_service, storage).execute(
                application_id = application_id,
                data = serializer.validated_data,
                recruiter_user_id= request.user.id,
            )
            if not result['success']:
                return Response({
                    'success': False,
                    'error'  : result['error']
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'offer'  : OfferLetterSerializer(result['offer']).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"SendOfferView error: {e}")
            return Response({
                'success': False,
                'error'  : str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class BulkSendOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        try:
            serializer = BulkSendOfferSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors' : serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            repo    = OfferRepository()
            notif   = NotificationService()
            storage = R2Storage()

            result = BulkSendOfferUseCase(repo, notif, storage).execute(
                application_ids=serializer.validated_data['application_ids'],
                data=serializer.validated_data,
                recruiter_user_id=request.user.id,
            )

            return Response({
                'success'    : True,
                'sent_count' : result['sent_count'],
                'fail_count' : result['fail_count'],
                'sent'       : result['sent'],
                'failed'     : result['failed'],
            })

        except Exception as e:
            logger.error(f"BulkSendOfferView error: {e}")
            return Response({
                'success': False,
                'error'  : str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CandidateRespondOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, offer_id):
        try:
            serializer = CandidateRespondSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors' : serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            repo  = OfferRepository()
            notif = NotificationService()

            result = RespondToOfferUseCase(repo, notif).execute(
                offer_id=offer_id,
                action=serializer.validated_data['action'],
                note=serializer.validated_data.get('note'),
            )

            if not result['success']:
                return Response({
                    'success': False,
                    'error'  : result['error']
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'offer'  : OfferLetterSerializer(result['offer']).data
            })

        except Exception as e:
            logger.error(f"CandidateRespondOfferView error: {e}")
            return Response({
                'success': False,
                'error'  : str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetApplicationOfferView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        try:
            repo   = OfferRepository()
            result = GetOfferDetailUseCase(repo).execute(application_id)

            if not result['success']:
                return Response({
                    'success': False,
                    'error'  : result['error']
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'success': True,
                'offer'  : OfferLetterSerializer(result['offer']).data
            })

        except Exception as e:
            logger.error(f"GetApplicationOfferView error: {e}")
            return Response({
                'success': False,
                'error'  : str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)