from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings

from hr_round.serializers import(
    HRRoundSettingsSerializer,
    HRInterviewListSerializer,
    HRInterviewDetailSerializer,
    ScheduleHRInterviewSerializer,
    BulkScheduleHRInterviewSerializer,
    MeetingSessionSerializer,
    InterviewRecordingSerializer,
    InterviewNotesSerializer,
    InterviewResultSerializer,
    UpdateInterviewStatusSerializer,
    HRMoveToNextStageSerializer,
    UploadRecordingSerializer
)

from infrastructure.services.notification_service import NotificationService
from infrastructure.services.storage_factory import StorageFactory
from infrastructure.repositories.hr_round_repository import HRInterviewRepository

from core.use_cases.hr_round.schedule_interiew import (
    ScheduleInterviewUsecase,
    BulkScheduleHRInterviewUsecase,
    RescheduleHRInterviewUsecase,
    CancelHRInterviewUsecase
)
from core.use_cases.hr_round.conduct_interview import(
    ConductInterviewUseCase,
    StartMeetingUseCase,
    JoinMeetingUseCase,
    EndMeetingUseCase,
    LeaveMeetingUseCase,
    ResetInterviewSessionUseCase
)
from core.use_cases.hr_round.recording_management import(
    # UploadRecordingUseCase,
    DeleteRecordingUseCase,
    ProcessZegoCloudWebhookUseCase
)
from core.use_cases.hr_round.process_results import(
    FinalizeResultUseCase,
    MoveToNextStageUseCase
)
from core.use_cases.hr_round.notes_management import(
    CreateNotesUseCase,
    UpdateNotesUseCase,
    FinalizeNotesUseCase
)
from infrastructure.services.hr_round_service import MeetingService, VideoProcessingService


class GetHRRoundSettingsAPIView(APIView):
    permission_classes  = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            repository = HRInterviewRepository()
            settings = repository.get_settings_by_id(job_id)
            
            if not settings:
                # Create default settings
                settings = repository.create_default_settings(job_id)
            
            serializer = HRRoundSettingsSerializer(settings)
            
            return Response({
                'success': True,
                'settings': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UppdateHRRoundSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self,request,job_id):
        try:
            repository = HRInterviewRepository()
            try:
                existing_settings = repository.get_settings_by_id(job_id)
                is_update = True
            except:
                existing_settings = None
                is_update = False

            if is_update:
                serializer = HRRoundSettingsSerializer(
                    existing_settings,
                    data = request.data,
                    partial = True
                )
            else:
                data = request.data.copy()
                data['job'] = job_id
                serializer = HRRoundSettingsSerializer(data=data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            settings = repository.update_settings(
                job_id=job_id,
                settings_data=serializer.validated_data
            )
            response_serializer = HRRoundSettingsSerializer(settings)
            
            return Response({
                'success': True,
                'settings': response_serializer.data,
                'message': 'Settings updated successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class GetHRInterviewsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            status_filter = request.query_params.get('status', None)
            
            repository = HRInterviewRepository()
            interviews = repository.list_interviews_by_job(job_id, status_filter)
            
            serializer = HRInterviewListSerializer(interviews, many=True)
            
            return Response({
                'success': True,
                'interviews': serializer.data,
                'count': len(interviews)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class GetInterviewByApplicationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, application_id):
        try:
            repository = HRInterviewRepository()
            interview = repository.get_interview_by_application(application_id)
            
            if not interview:
                return Response({
                    'success': False,
                    'error': 'Interview not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = HRInterviewDetailSerializer(interview)
            
            return Response({
                'success': True,
                'interview': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class GetInterviewDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        try:
            repository = HRInterviewRepository()
            interview = repository.get_interview_by_id(interview_id)
            
            if not interview:
                return Response({
                    'success': False,
                    'error': 'Interview not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = HRInterviewDetailSerializer(interview)
            
            return Response({
                'success': True,
                'interview': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetUpcomingInterviewsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            repository = HRInterviewRepository()
            user = request.user
            
            if user.user_type == 'recruiter':
                interviews = repository.list_interviews_by_recruiter(
                    user.id,
                    status='scheduled'
                )
            else:
                from .models import HRInterview
                interviews = HRInterview.objects.filter(
                    application__candidate__user=user,
                    status='scheduled',
                    scheduled_at__gte=timezone.now()
                )
            
            serializer = HRInterviewListSerializer(interviews, many=True)
            
            return Response({
                'success': True,
                'interviews': serializer.data,
                'count': len(interviews)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScheduleHRInterviewAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        repository = HRInterviewRepository()  
        notification_service = NotificationService()
        try:
            # Validate input
            serializer = ScheduleHRInterviewSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Execute use case
            use_case = ScheduleInterviewUsecase(repository, notification_service)
            result = use_case.execute(
                application_id=data['application_id'],
                scheduled_at=data['scheduled_at'],
                duration_minutes=data.get('duration_minutes', 45),
                timezone_str=data.get('timezone', 'Asia/Kolkata'),
                conducted_by_id=request.user.id,
                scheduling_notes=data.get('scheduling_notes')
            )
            
            if result['success']:
                response_serializer = HRInterviewDetailSerializer(result['interview'])
                return Response({
                    'success': True,
                    'interview': response_serializer.data,
                    'message': 'Interview scheduled successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class BulkScheduleHRInterviewsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = BulkScheduleHRInterviewSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            # Execute use case
            use_case = BulkScheduleHRInterviewUsecase(repository, notification_service)
            result = use_case.execute(
                application_ids=data['application_ids'],
                scheduled_at=data['scheduled_at'],
                duration_minutes=data.get('duration_minutes', 45),
                timezone_str=data.get('timezone', 'Asia/Kolkata'),
                conducted_by_id=request.user.id,
                scheduling_notes=data.get('scheduling_notes')
            )
            
            return Response({
                'success': result['success'],
                'scheduled_count': result['scheduled_count'],
                'failed_count': result['failed_count'],
                'errors': result['errors'],
                'message': f"Scheduled {result['scheduled_count']} interviews"
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RescheduleHRInterviewAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, interview_id):
        try:
            new_scheduled_at = request.data.get('scheduled_at')
            new_duration = request.data.get('duration_minutes')
            reschedule_reason = request.data.get('reason')
            
            if not new_scheduled_at:
                return Response({
                    'success': False,
                    'error': 'scheduled_at is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execute use case
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = RescheduleHRInterviewUsecase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                new_scheduled_at=new_scheduled_at,
                new_duration_minutes=new_duration,
                reschedule_reason=reschedule_reason
            )
            
            if result['success']:
                response_serializer = HRInterviewDetailSerializer(result['interview'])
                return Response({
                    'success': True,
                    'interview': response_serializer.data,
                    'message': 'Interview rescheduled successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CancelHRInterviewAPIView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request, interview_id):
        try:
            reason = request.data.get('reason', '')
            
            # Execute use case
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = CancelHRInterviewUsecase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                cancellation_reason=reason,
                cancelled_by_id=request.user.id
            )
            
            if result['success']:
                response_serializer = HRInterviewDetailSerializer(result['interview'])
                return Response({
                    'success': True,
                    'interview': response_serializer.data,
                    'message': 'Interview cancelled successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateInterviewStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, interview_id):
        try:
            # Validate input
            serializer = UpdateInterviewStatusSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            repository = HRInterviewRepository()
            interview = repository.update_interview_status(
                interview_id=interview_id,
                status=serializer.validated_data['status'],
                cancellation_reason=serializer.validated_data.get('cancellation_reason')
            )
            
            response_serializer = HRInterviewDetailSerializer(interview)
            
            return Response({
                'success': True,
                'interview': response_serializer.data,
                'message': 'Status updated successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StartMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            interview_id = request.data.get('interview_id')
            
            if not interview_id:
                return Response({
                    'success': False,
                    'error': 'interview_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            
            use_case = StartMeetingUseCase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                recruiter_id=request.user.id
            )
            
            if result['success']:
                session_serializer = MeetingSessionSerializer(result['session'])
                interview_serializer = HRInterviewDetailSerializer(result['interview'])
                
                return Response({
                    'success': True,
                    'session': session_serializer.data,
                    'interview': interview_serializer.data,
                    'zegocloud_config': result['zegocloud_config'],
                    'message': 'Meeting started successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JoinMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # def post(self, request):
    #     try:
    #         session_id = request.data.get('session_id')
            
    #         if not session_id:
    #             return Response({
    #                 'success': False,
    #                 'error': 'session_id is required'
    #             }, status=status.HTTP_400_BAD_REQUEST)
            
    #         user_type = 'candidate' if request.user.user_type == 'candidate' else 'recruiter'
            
    #         # Execute use case
    #         use_case = JoinMeetingUseCase()
    #         result = use_case.execute(
    #             session_id=session_id,
    #             participant_type=user_type,
    #             user_id=request.user.id
    #         )
            
    #         if result['success']:
    #             session_serializer = MeetingSessionSerializer(result['session'])
    #             meeting_service = MeetingService()
                
    #             return Response({
    #                 'success': True,
    #                 'session': session_serializer.data,
    #                 'webrtc_config': meeting_service.generate_webrtc_config(),
    #                 'message': 'Joined meeting successfully'
    #             })
    #         else:
    #             return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    #     except Exception as e:
    #         return Response({
    #             'success': False,
    #             'error': str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            
            if not session_id:
                return Response({
                    'success': False,
                    'error': 'session_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            repo = HRInterviewRepository()
            notification_service = NotificationService()

            session = repo.get_meeting_session(session_id)
            if not session:
                return Response({
                    'success': False,
                    'error': 'Session not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user_id_str = str(request.user.id)
            if user_id_str == str(session.candidate_id):
                participant_type = 'candidate'
            elif user_id_str == str(session.recruiter_id):
                participant_type = 'recruiter'
            else:
                # ✅ Fallback: check by role field — use whatever your model has
                # Common options: request.user.role, request.user.account_type, 
                # request.user.is_recruiter, request.user.groups, etc.
                # Replace 'role' below with your actual field name:
                role = getattr(request.user, 'role', None)
                participant_type = 'candidate' if role == 'candidate' else 'recruiter'
            from infrastructure.services.hr_round_service import MeetingService
            user_token = MeetingService.generate_zegocloud_token(
                user_id=str(request.user.id),
                room_id=session.room_id
            )
            
            repo.update_participant_connection(
                session_id=session_id,
                participant_type=participant_type,
                connected=True
            )
            if participant_type == 'candidate':
                notification_service.send_websocket_notification(
                    user_id=int(session.recruiter_id),
                    notification_type='candidate_joined',
                    data={
                        'interview_id': session.interview.id,
                        'candidate_name': session.interview.candidate_name,
                        'session_id': session_id,
                        'message': f'{session.interview.candidate_name} has joined the interview'
                    }
                )
            return Response({
                'success': True,
                'session': MeetingSessionSerializer(session).data,
                'zegocloud_config': {
                    'app_id': str(settings.ZEGOCLOUD_APP_ID),
                    'room_id': session.room_id,
                    'token': user_token,
                    'user_id': user_id_str
                },
                'message': 'Joined meeting successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class LeaveMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            if not session_id:
                return Response({
                    'success': False,
                    'error': 'session_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = LeaveMeetingUseCase(repository, notification_service)
            result = use_case.execute(
                session_id = session_id,
                left_by_id = request.user.id
            )
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Left meeting successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class EndMeetingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            notes_data = request.data.get('notes')
            recommendation = request.data.get('recommendation')

            
            if not session_id:
                return Response({
                    'success': False,
                    'error': 'session_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execute use case
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = EndMeetingUseCase(repository, notification_service)
            result = use_case.execute(
                session_id=session_id,
                ended_by_id=request.user.id,
                notes_data=notes_data,
                recommendation=recommendation
            )
            
            if result['success']:
                session_serializer = MeetingSessionSerializer(result['session'])
                return Response({
                    'success': True,
                    'session': session_serializer.data,
                    'message': 'Meeting ended successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ResetInterviewSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:
            session_id = request.data.get('session_id')
            if not session_id:
                return Response({
                    'succeess':False,
                    'error':'session_id is required'
                },status=status.HTTP_400_BAD_REQUEST)
            
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = ResetInterviewSessionUseCase(repository, notification_service)
            result = use_case.execute(
                session_id = session_id,
                reset_by_id = request.user.id
            )
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Session reset. You can reschedule the interview.'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

class ZegoCloudWebhookAPIView(APIView):
    permission_classes = []  # Public endpoint (validate signature instead)
    
    def post(self, request):
        try:

            signature = request.headers.get('X-ZegoCloud-Signature')
            if not self._validate_signature(request.body, signature):
                return Response({
                    'success': False,
                    'error': 'Invalid signature'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = ProcessZegoCloudWebhookUseCase(repository, notification_service)
            result = use_case.execute(request.data)
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        import hmac
        import hashlib
        
        secret = settings.ZEGOCLOUD_SERVER_SECRET.encode()
        expected_signature = hmac.new(
            secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

# class StartRecordingAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             session_id = request.data.get('session_id')
            
#             if not session_id:
#                 return Response({
#                     'success': False,
#                     'error': 'session_id is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             repository = HRInterviewRepository()
#             session = repository.start_recording(session_id)
            
#             serializer = MeetingSessionSerializer(session)
            
#             return Response({
#                 'success': True,
#                 'session': serializer.data,
#                 'message': 'Recording started'
#             })
            
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class StopRecordingAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             session_id = request.data.get('session_id')
            
#             if not session_id:
#                 return Response({
#                     'success': False,
#                     'error': 'session_id is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             repository = HRInterviewRepository()
#             session = repository.stop_recording(session_id)
            
#             serializer = MeetingSessionSerializer(session)
            
#             return Response({
#                 'success': True,
#                 'session': serializer.data,
#                 'message': 'Recording stopped'
#             })
            
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetRecordingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        try:
            repository = HRInterviewRepository()
            recording = repository.get_recording_by_interview(interview_id)
            
            if not recording:
                return Response({
                    'success': False,
                    'error': 'Recording not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = InterviewRecordingSerializer(recording)
            
            return Response({
                'success': True,
                'recording': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class UploadRecordingAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             # Validate input
#             serializer = UploadRecordingSerializer(data=request.data)
#             if not serializer.is_valid():
#                 return Response({
#                     'success': False,
#                     'errors': serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             data = serializer.validated_data
            
#             # Execute use case
#             use_case = UploadRecordingUseCase()
#             result = use_case.execute(
#                 interview_id=data['interview_id'],
#                 video_file=data['video_file'],
#                 filename=data['video_file'].name,
#                 duration_seconds=data.get('duration_seconds'),
#                 resolution=data.get('resolution')
#             )
            
#             if result['success']:
#                 response_serializer = InterviewRecordingSerializer(result['recording'])
#                 return Response({
#                     'success': True,
#                     'recording': response_serializer.data,
#                     'message': 'Recording uploaded successfully'
#                 })
#             else:
#                 return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteRecordingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, interview_id):
        try:
            repository = HRInterviewRepository()
            video_service = VideoProcessingService()
            # Execute use case
            use_case = DeleteRecordingUseCase(repository, video_service)
            result = use_case.execute(
                interview_id=interview_id,
                deleted_by_id=request.user.id
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Recording deleted successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetNotesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        try:
            repository = HRInterviewRepository()
            notes = repository.get_notes_by_interview(interview_id)
            
            if not notes:
                return Response({
                    'success': False,
                    'error': 'Notes not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = InterviewNotesSerializer(notes)
            
            return Response({
                'success': True,
                'notes': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateNotesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            interview_id = request.data.get('interview')
            
            if not interview_id:
                return Response({
                    'success': False,
                    'error': 'interview is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            serializer = InterviewNotesSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
 
            repository = HRInterviewRepository()
            use_case = CreateNotesUseCase(repository)
            result = use_case.execute(
                interview_id=interview_id,
                recorded_by_id=request.user.id,
                notes_data=request.data
            )
            
            if result['success']:
                response_serializer = InterviewNotesSerializer(result['notes'])
                return Response({
                    'success': True,
                    'notes': response_serializer.data,
                    'message': 'Notes created successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateNotesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, interview_id):
        try:
            # Validate input
            serializer = InterviewNotesSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execute use case
            repository = HRInterviewRepository()
            use_case = UpdateNotesUseCase(repository)
            result = use_case.execute(
                interview_id=interview_id,
                recorded_by_id=request.user.id,
                notes_data=request.data
            )
            
            if result['success']:
                response_serializer = InterviewNotesSerializer(result['notes'])
                return Response({
                    'success': True,
                    'notes': response_serializer.data,
                    'message': 'Notes updated successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FinalizeNotesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, interview_id):
        try:
            # Execute use case
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = FinalizeResultUseCase(repository, notification_service)
            result = use_case.execute(
                interview_id=interview_id,
                finalized_by_id=request.user.id
            )
            
            if result['success']:
                response_serializer = InterviewNotesSerializer(result['notes'])
                return Response({
                    'success': True,
                    'notes': response_serializer.data,
                    'message': 'Notes finalized successfully'
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetResultAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interview_id):
        try:
            repository = HRInterviewRepository()
            result = repository.get_result_by_interview(interview_id)
            
            if not result:
                return Response({
                    'success': False,
                    'error': 'Result not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = InterviewResultSerializer(result)
            
            return Response({
                'success': True,
                'result': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FinalizeResultAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            interview_id = request.data.get('interview_id')
            decision = request.data.get('decision')
            decision_reason = request.data.get('decision_reason', '')
            next_steps = request.data.get('next_steps', '')
            
            if not interview_id or not decision:
                return Response({
                    'success': False,
                    'error': 'interview_id and decision are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Execute use case
            use_case = FinalizeResultUseCase()
            result = use_case.execute(
                interview_id=interview_id,
                decision=decision,
                decided_by_id=request.user.id,
                decision_reason=decision_reason,
                next_steps=next_steps
            )
            
            if result['success']:
                result_serializer = InterviewResultSerializer(result['result'])
                return Response({
                    'success': True,
                    'result': result_serializer.data,
                    'application_status': result['application'].status,
                    'message': f"Candidate {decision} successfully"
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class MoveToNextStageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = HRMoveToNextStageSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'success': False, 'errors': serializer.errors}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # Execute use case
            repository = HRInterviewRepository()
            notification_service = NotificationService()
            use_case = MoveToNextStageUseCase(repository, notification_service)
            result = use_case.execute(
                interview_ids=data['interview_ids'],         
                feedback=data.get('feedback', 'Passed HR round')
            )
            
            if result['success']:
                return Response(result)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
# class GetHRInterviewStatsAPIView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, job_id):
#         try:
#             repository = HRInterviewRepository()
            
#             from .models import HRInterview, InterviewResult
#             from django.db.models import Count, Avg, Q
            
#             # Get all interviews for job
#             all_interviews = HRInterview.objects.filter(job_id=job_id)
            
#             stats = {
#                 'total_interviews': all_interviews.count(),
#                 'scheduled': all_interviews.filter(status='scheduled').count(),
#                 'in_progress': all_interviews.filter(status='in_progress').count(),
#                 'completed': all_interviews.filter(status='completed').count(),
#                 'cancelled': all_interviews.filter(status='cancelled').count(),
#                 'no_show': all_interviews.filter(status='no_show').count(),
#             }
            
#             # Get results stats
#             results = InterviewResult.objects.filter(interview__job_id=job_id)
            
#             if results.exists():
#                 stats['results'] = {
#                     'total_evaluated': results.count(),
#                     'qualified': results.filter(decision='qualified').count(),
#                     'not_qualified': results.filter(decision='not_qualified').count(),
#                     'average_score': round(results.aggregate(Avg('final_score'))['final_score__avg'] or 0, 2),
#                 }
#             else:
#                 stats['results'] = {
#                     'total_evaluated': 0,
#                     'qualified': 0,
#                     'not_qualified': 0,
#                     'average_score': 0
#                 }
            
#             return Response({
#                 'success': True,
#                 'stats': stats
#             })
            
#         except Exception as e:
#             return Response({
#                 'success': False,
#                 'error': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)