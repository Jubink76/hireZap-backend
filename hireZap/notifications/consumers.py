import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'user_{self.user_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"✅ WebSocket connected: User {self.user_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"❌ WebSocket disconnected: User {self.user_id}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))
    # =========================================================================
    # COMPANY NOTIFICATIONS
    # =========================================================================
    # Custom event handlers
    async def company_verified(self, event):
        """Send company verification notification"""
        await self.send(text_data=json.dumps({
            'type': 'company_verified',
            'company': event['company'],
            'message': 'Your company has been verified!'
        }))

    async def company_rejected(self, event):
        """Send company rejection notification"""
        await self.send(text_data=json.dumps({
            'type': 'company_rejected',
            'company': event['company'],
            'reason': event['reason'],
            'message': 'Your company verification was rejected'
        }))
    # =========================================================================
    # JOB APPLICATION NOTIFICATIONS
    # =========================================================================
    async def job_application(self, event):
        """Send new job application notification"""
        await self.send(text_data=json.dumps({
            'type': 'job_application',
            'application': event['application'],
            'message': f"New application for {event['job_title']}"
        }))
    # =========================================================================
    # RESUME SCREENING NOTIFICATIONS
    # =========================================================================
    async def screening_progress(self, event):
        """Send screening progress update"""
        await self.send(text_data=json.dumps({
            'type': 'screening_progress',
            'job_id': event['job_id'],
            'progress': event['progress']
        }))

    async def resume_screening_completed(self, event):
        """Send screening completion notification"""
        await self.send(text_data=json.dumps({
            'type': 'resume_screening_completed',
            'application_id': event['application_id'],
            'job_title': event['job_title'],
            'decision': event['decision'],
            'score': event['score']
        }))

    async def screening_progress_update(self, event):
        """Send progress update to recruiter"""
        await self.send(text_data=json.dumps({
            'type': 'screening_progress_update',
            'job_id': event['job_id'],
            'screened_count': event['screened_count'],
            'total_count': event['total_count']
        }))

    async def bulk_screening_started(self, event):
        """Notify bulk screening started"""
        await self.send(text_data=json.dumps({
            'type': 'bulk_screening_started',
            'job_id': event['job_id'],
            'job_title': event['job_title'],
            'total_applications': event['total_applications']
        }))

    async def bulk_screening_completed(self, event):
        """Notify bulk screening completed"""
        await self.send(text_data=json.dumps({
            'type': 'bulk_screening_completed',
            'job_id': event['job_id'],
            'job_title': event['job_title'],
            'total_screened': event['total_screened']
        }))
    # =========================================================================
    # TELEPHONIC INTERVIEW NOTIFICATIONS
    # =========================================================================
    
    async def interview_scheduled(self, event):
        """Interview scheduled notification (telephonic or HR)"""
        await self.send(text_data=json.dumps({
            'type': 'interview_scheduled',
            'message': 'Interview has been scheduled',
            'data': event.get('data', {})
        }))
    
    async def interview_rescheduled(self, event):
        """Interview rescheduled notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_rescheduled',
            'message': 'Interview has been rescheduled',
            'data': event.get('data', {})
        }))
    
    async def interview_cancelled(self, event):
        """Interview cancelled notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_cancelled',
            'message': 'Interview has been cancelled',
            'data': event.get('data', {})
        }))
    
    async def interview_started(self, event):
        """Interview started notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_started',
            'message': 'Interview has started',
            'data': event.get('data', {})
        }))
    
    async def interview_completed(self, event):
        """Interview completed notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_completed',
            'message': 'Interview has been completed',
            'data': event.get('data', {})
        }))

    async def interview_reminder(self, event):
        """Interview reminder notification (24h before)"""
        await self.send(text_data=json.dumps({
            'type': 'interview_reminder',
            'message': 'Interview reminder',
            'data': event.get('data', {})
        }))
    
    async def interview_result(self, event):
        """Interview result notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_result',
            'message': 'Interview result is ready',
            'data': event.get('data', {})
        }))

    async def call_started(self, event):
        """Call started notification (telephonic)"""
        await self.send(text_data=json.dumps({
            'type': 'call_started',
            'message': event.get('message', 'Call has started'),
            'data': event.get('data', {})
        }))
        
    async def candidate_joined(self, event):
        """Candidate joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'candidate_joined',
            'message': event.get('message', 'Candidate has joined'),
            'data': event.get('data', {})
        }))

    async def call_ended(self, event):
        """Call ended notification"""
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'message': event.get('message', 'Call has ended'),
            'data': event.get('data', {})
        }))
    
    async def interview_analyzed(self, event):
        """Interview analysis completed notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_analyzed',
            'message': 'Interview analysis completed',
            'data': event.get('data', {})
        }))

    # =========================================================================
    # HR INTERVIEW NOTIFICATIONS
    # =========================================================================
    
    async def interview_ended(self, event):
        """HR interview ended notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_ended',
            'message': event.get('message', 'Interview has ended'),
            'data': event.get('data', {})
        }))
    
    async def recording_uploaded(self, event):
        """Recording uploaded notification"""
        await self.send(text_data=json.dumps({
            'type': 'recording_uploaded',
            'message': event.get('message', 'Recording uploaded successfully'),
            'data': event.get('data', {})
        }))
    
    async def notes_finalized(self, event):
        """Notes finalized notification"""
        await self.send(text_data=json.dumps({
            'type': 'notes_finalized',
            'message': event.get('message', 'Interview notes finalized'),
            'data': event.get('data', {})
        }))
    
    async def interview_result_finalized(self, event):
        """Interview result finalized notification"""
        await self.send(text_data=json.dumps({
            'type': 'interview_result_finalized',
            'message': event.get('message', 'Interview result finalized'),
            'data': event.get('data', {})
        }))
    
    async def stage_progression(self, event):
        """Stage progression notification"""
        await self.send(text_data=json.dumps({
            'type': 'stage_progression',
            'message': event.get('message', 'You have progressed to the next stage'),
            'data': event.get('data', {})
        }))

class CompanyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.recruiter_id = self.scope['url_route']['kwargs']['recruiter_id']
        self.room_group_name = f'recruiter_{self.recruiter_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def company_update(self, event):
        """Send company update"""
        await self.send(text_data=json.dumps({
            'type': 'company_update',
            'company': event['company']
        }))

# =============================================================================
# HR INTERVIEW SPECIFIC CONSUMERS (separate WebSocket connections)
# =============================================================================

class HRInterviewMeetingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for HR interview meetings
    Handles:
    - WebRTC signaling (offer/answer/ICE candidates)
    - Connection status
    - Recording controls
    - Meeting controls
    """
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_type = self.scope['url_route']['kwargs']['user_type']  # 'recruiter' or 'candidate'
        
        self.room_group_name = f'meeting_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Meeting WebSocket connected: {self.user_type} {self.user_id} in room {self.room_id}")
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'user_type': self.user_type
            }
        )
    
    async def disconnect(self, close_code):
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user_id,
                'user_type': self.user_type
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"❌ Meeting WebSocket disconnected: {self.user_type} {self.user_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle different message types
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            
            elif message_type == 'webrtc_offer':
                # Forward WebRTC offer to other participant
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_offer',
                        'offer': data['offer'],
                        'from_user': self.user_id,
                        'from_type': self.user_type
                    }
                )
            
            elif message_type == 'webrtc_answer':
                # Forward WebRTC answer
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_answer',
                        'answer': data['answer'],
                        'from_user': self.user_id,
                        'from_type': self.user_type
                    }
                )
            
            elif message_type == 'webrtc_ice_candidate':
                # Forward ICE candidate
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'webrtc_ice_candidate',
                        'candidate': data['candidate'],
                        'from_user': self.user_id,
                        'from_type': self.user_type
                    }
                )
            
            elif message_type == 'start_recording':
                # Recording started
                session_id = data.get('session_id')
                await self.start_recording(session_id)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'recording_started',
                        'session_id': session_id
                    }
                )
            
            elif message_type == 'stop_recording':
                # Recording stopped
                session_id = data.get('session_id')
                await self.stop_recording(session_id)
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'recording_stopped',
                        'session_id': session_id
                    }
                )
            
            elif message_type == 'end_meeting':
                # End meeting
                session_id = data.get('session_id')
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'meeting_ended',
                        'session_id': session_id,
                        'ended_by': self.user_type
                    }
                )
        
        except Exception as e:
            print(f"❌ WebSocket receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': str(e)
            }))
    
    # Event handlers
    
    async def user_joined(self, event):
        """Send user joined notification"""
        # Don't send to self
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_type': event['user_type']
            }))
    
    async def user_left(self, event):
        """Send user left notification"""
        if event['user_id'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_type': event['user_type']
            }))
    
    async def webrtc_offer(self, event):
        """Forward WebRTC offer"""
        # Don't send to sender
        if event['from_user'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'from_user': event['from_user'],
                'from_type': event['from_type']
            }))
    
    async def webrtc_answer(self, event):
        """Forward WebRTC answer"""
        if event['from_user'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'from_user': event['from_user'],
                'from_type': event['from_type']
            }))
    
    async def webrtc_ice_candidate(self, event):
        """Forward ICE candidate"""
        if event['from_user'] != self.user_id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_ice_candidate',
                'candidate': event['candidate'],
                'from_user': event['from_user'],
                'from_type': event['from_type']
            }))
    
    async def recording_started(self, event):
        """Notify recording started"""
        await self.send(text_data=json.dumps({
            'type': 'recording_started',
            'session_id': event['session_id'],
            'message': 'Recording started'
        }))
    
    async def recording_stopped(self, event):
        """Notify recording stopped"""
        await self.send(text_data=json.dumps({
            'type': 'recording_stopped',
            'session_id': event['session_id'],
            'message': 'Recording stopped'
        }))
    
    async def meeting_ended(self, event):
        """Notify meeting ended"""
        await self.send(text_data=json.dumps({
            'type': 'meeting_ended',
            'session_id': event['session_id'],
            'ended_by': event['ended_by']
        }))
    
    # Database operations
    
    @database_sync_to_async
    def start_recording(self, session_id):
        """Start recording in database"""
        from core.interface.hr_round_repository_port import HRRoundRepositoryPort
        repo = HRRoundRepositoryPort()
        repo.start_recording(session_id)
    
    @database_sync_to_async
    def stop_recording(self, session_id):
        """Stop recording in database"""
        from core.interface.hr_round_repository_port import HRRoundRepositoryPort
        repo = HRRoundRepositoryPort()
        repo.stop_recording(session_id)


class HRInterviewChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for interview chat
    Handles real-time chat during HR interviews
    """
    
    async def connect(self):
        self.interview_id = self.scope['url_route']['kwargs']['interview_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_type = self.scope['url_route']['kwargs']['user_type']  # 'recruiter' or 'candidate'
        
        self.room_group_name = f'chat_{self.interview_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Chat WebSocket connected: {self.user_type} {self.user_id} in interview {self.interview_id}")
        
        # Send chat history
        messages = await self.get_chat_history()
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"❌ Chat WebSocket disconnected: {self.user_type} {self.user_id}")
    
    async def receive(self, text_data):
        """Handle incoming chat messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            
            elif message_type == 'chat_message':
                message = data.get('message', '').strip()
                
                if not message:
                    return
                
                from django.utils import timezone
                timestamp = timezone.now().isoformat()
                
                # Save to Redis cache
                await self.save_chat_message(
                    sender_id=self.user_id,
                    sender_type=self.user_type,
                    message=message,
                    timestamp=timestamp
                )
                
                # Also save to database for permanent record
                await self.save_chat_to_db(
                    sender_id=self.user_id,
                    sender_type=self.user_type,
                    message=message
                )
                
                # Broadcast to all participants
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'sender_id': self.user_id,
                        'sender_type': self.user_type,
                        'message': message,
                        'timestamp': timestamp
                    }
                )
        
        except Exception as e:
            print(f"❌ Chat receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': str(e)
            }))
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'sender_id': event['sender_id'],
            'sender_type': event['sender_type'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_chat_history(self):
        """Get chat history from Redis"""
        from infrastructure.services.hr_round_service import ChatService
        chat_service = ChatService()
        return chat_service.get_messages(self.interview_id, limit=100)
    
    @database_sync_to_async
    def save_chat_message(self, sender_id, sender_type, message, timestamp):
        """Save chat message to Redis"""
        from infrastructure.services.hr_round_service import ChatService
        chat_service = ChatService()
        chat_service.save_message(
            interview_id=self.interview_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message,
            timestamp=timestamp
        )
    
    @database_sync_to_async
    def save_chat_to_db(self, sender_id, sender_type, message):
        """Save chat message to database (permanent record)"""
        from core.interface.hr_round_repository_port import HRRoundRepositoryPort
        repo = HRRoundRepositoryPort()
        repo.save_chat_message(
            interview_id=self.interview_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message
        )