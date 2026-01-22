from typing import Dict, BinaryIO
from django.conf import settings
from infrastructure.services.storage_factory import StorageFactory
from PIL import Image
import io
import os


class VideoProcessingService:
    """Service for processing interview recordings"""
    
    def __init__(self):
        self.storage = StorageFactory.get_default_storage()
    
    def upload_recording(
        self,
        video_file: BinaryIO,
        interview_id: int,
        filename: str
    ) -> Dict:
        """
        Upload interview recording to R2
        
        Returns:
            {
                'success': bool,
                'video_url': str,
                'video_key': str,
                'file_size': int
            }
        """
        try:
            # Determine content type
            content_type = self._get_video_content_type(filename)
            
            # Upload to R2
            result = self.storage.upload_file(
                file=video_file,
                folder='hr-interviews/recordings',
                filename=f"interview_{interview_id}_{filename}",
                content_type=content_type,
                make_public=False  # Private recordings
            )
            
            return {
                'success': True,
                'video_url': result['url'],
                'video_key': result['key'],
                'file_size': video_file.size if hasattr(video_file, 'size') else None
            }
            
        except Exception as e:
            print(f"❌ Video upload error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_thumbnail(
        self,
        video_url: str,
        interview_id: int
    ) -> Dict:
        """
        Generate thumbnail from video first frame
        
        NOTE: This is a simplified version. For production, you'd use
        ffmpeg or a video processing library like moviepy.
        
        For now, this returns a placeholder or you can integrate ffmpeg.
        """
        try:
            # TODO: Implement actual thumbnail generation using ffmpeg
            # For now, return success with placeholder
            
            # Example implementation would be:
            # 1. Download video temporarily
            # 2. Extract first frame using ffmpeg
            # 3. Generate thumbnail image
            # 4. Upload thumbnail to R2
            # 5. Return thumbnail URL
            
            return {
                'success': True,
                'thumbnail_url': None,  # Placeholder
                'thumbnail_key': None,
                'message': 'Thumbnail generation not yet implemented'
            }
            
        except Exception as e:
            print(f"❌ Thumbnail generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_recording(self, video_key: str, thumbnail_key: str = None) -> bool:
        """Delete recording and thumbnail from storage"""
        try:
            # Delete video
            if video_key:
                self.storage.delete_file(video_key)
            
            # Delete thumbnail
            if thumbnail_key:
                self.storage.delete_file(thumbnail_key)
            
            return True
            
        except Exception as e:
            print(f"❌ Delete recording error: {str(e)}")
            return False
    
    def _get_video_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.webm': 'video/webm',
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
        }
        
        return content_types.get(ext, 'video/webm')


class ChatService:
    """Service for managing interview chat (Redis cache)"""
    
    def __init__(self):
        from infrastructure.redis_client import redis_client
        self.redis = redis_client
        self.ttl = 7 * 24 * 60 * 60  # 7 days
    
    def save_message(
        self,
        interview_id: int,
        sender_id: str,
        sender_type: str,
        message: str,
        timestamp: str
    ) -> bool:
        """Save chat message to Redis"""
        try:
            key = f"hr_interview_chat:{interview_id}"
            
            # Create message object
            message_data = {
                'sender_id': sender_id,
                'sender_type': sender_type,
                'message': message,
                'timestamp': timestamp
            }
            
            # Save to Redis list
            import json
            self.redis.rpush(key, json.dumps(message_data))
            
            # Set expiry
            self.redis.expire(key, self.ttl)
            
            return True
            
        except Exception as e:
            print(f"❌ Save chat message error: {str(e)}")
            return False
    
    def get_messages(self, interview_id: int, limit: int = 100) -> list:
        """Get chat messages from Redis"""
        try:
            key = f"hr_interview_chat:{interview_id}"
            
            # Get messages
            messages = self.redis.lrange(key, -limit, -1)
            
            # Parse JSON
            import json
            return [json.loads(msg) for msg in messages]
            
        except Exception as e:
            print(f"❌ Get chat messages error: {str(e)}")
            return []
    
    def delete_messages(self, interview_id: int):
        """Delete chat messages from Redis"""
        try:
            key = f"hr_interview_chat:{interview_id}"
            self.redis.delete(key)
        except Exception as e:
            print(f"❌ Delete chat messages error: {str(e)}")
    
    def get_message_count(self, interview_id: int) -> int:
        """Get total message count"""
        try:
            key = f"hr_interview_chat:{interview_id}"
            return self.redis.llen(key)
        except:
            return 0


class MeetingService:
    """Service for managing meeting logic"""
    
    @staticmethod
    def generate_webrtc_config() -> Dict:
        """Generate WebRTC configuration"""
        return {
            'iceServers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:global.stun.twilio.com:3478'},
                {'urls': 'stun:stun.services.mozilla.com:3478'},
            ]
        }
    
    @staticmethod
    def validate_meeting_access(
        interview_id: int,
        user_id: int,
        user_type: str
    ) -> Dict:
        """
        Validate if user can access meeting
        
        Args:
            interview_id: Interview ID
            user_id: User ID
            user_type: 'recruiter' or 'candidate'
        
        Returns:
            {
                'allowed': bool,
                'reason': str (if not allowed)
            }
        """
        from core.interface.hr_round_repository_port import HRRoundRepositoryPort
        
        repo = HRRoundRepositoryPort()
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview:
            return {'allowed': False, 'reason': 'Interview not found'}
        
        # Check if interview is scheduled
        if interview.status == 'not_scheduled':
            return {'allowed': False, 'reason': 'Interview not scheduled'}
        
        # Check if interview is cancelled
        if interview.status in ['cancelled', 'completed', 'no_show']:
            return {'allowed': False, 'reason': f'Interview is {interview.status}'}
        
        # Check user access
        if user_type == 'recruiter':
            if interview.conducted_by_id != user_id:
                return {'allowed': False, 'reason': 'Not the assigned recruiter'}
        elif user_type == 'candidate':
            if interview.application.candidate_id != user_id:
                return {'allowed': False, 'reason': 'Not the invited candidate'}
        
        return {'allowed': True}