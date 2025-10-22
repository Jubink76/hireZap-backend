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

    async def job_application(self, event):
        """Send new job application notification"""
        await self.send(text_data=json.dumps({
            'type': 'job_application',
            'application': event['application'],
            'message': f"New application for {event['job_title']}"
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