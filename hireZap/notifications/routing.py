from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/company/(?P<recruiter_id>\w+)/$', consumers.CompanyConsumer.as_asgi()),
    # re_path(
    #     r'^ws/hr-interview/meeting/(?P<room_id>[^/]+)/(?P<user_id>\d+)/(?P<user_type>[^/]+)/$',
    #     consumers.HRInterviewMeetingConsumer.as_asgi()
    # ),
    # re_path(
    #     r'^ws/hr-interview/chat/(?P<interview_id>\d+)/(?P<user_id>\d+)/(?P<user_type>[^/]+)/$',
    #     consumers.HRInterviewChatConsumer.as_asgi()
    # ),
]