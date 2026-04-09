import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from groq import Groq
import json

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            message = request.data.get('message', '').strip()
            conversation_history = request.data.get('history', [])  # previous messages
            current_page = request.data.get('current_page', '')

            if not message:
                return Response(
                    {'error': 'Message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Build context based on user role
            context = self._build_context(request.user, current_page)

            # Build messages for Groq
            messages = [
                {'role': 'system', 'content': self._build_system_prompt(request.user, context)},
                *conversation_history[-10:],  # last 10 messages to keep context
                {'role': 'user', 'content': message}
            ]

            # Call Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            completion = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )

            reply = completion.choices[0].message.content

            return Response({
                'success': True,
                'reply': reply,
                'role': 'assistant'
            })

        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Something went wrong. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_context(self, user, current_page):
        """Fetch relevant DB data to give the bot real context"""
        context = {}

        try:
            if user.role == 'candidate':
                from application.models import ApplicationModel
                applications = ApplicationModel.objects.filter(
                    candidate__user=user,
                    is_draft=False
                ).select_related('job', 'current_stage').order_by('-created_at')[:5]

                context['applications'] = [
                    {
                        'job': app.job.job_title,
                        'company': app.job.company.company_name,
                        'status': app.status,
                        'stage': app.current_stage.name if app.current_stage else 'Resume Screening',
                        'screening_score': app.ats_overall_score,
                        'decision': app.ats_decision,
                    }
                    for app in applications
                ]

            elif user.role == 'recruiter':
                from job.models import JobModel
                from application.models import ApplicationModel

                jobs = JobModel.objects.filter(
                    recruiter=user,
                    status='active'
                ).order_by('-created_at')[:5]

                context['active_jobs'] = [
                    {
                        'title': job.job_title,
                        'id': job.id,
                        'total_applications': job.total_applications_count,
                        'screening_status': job.screening_status,
                    }
                    for job in jobs
                ]

        except Exception as e:
            logger.error(f"Context building error: {str(e)}")

        return context

    def _build_system_prompt(self, user, context):
        """Build system prompt with user context"""
        base = f"""You are HireZap Assistant, a helpful AI for a hiring and interview platform called HireZap.
You are talking to {user.full_name}, who is a {user.role}.
Be concise, friendly, and helpful. Use bullet points when listing things.
Never make up data — only use the real data provided below.
If you don't know something, say so honestly.

Current user data:
{json.dumps(context, indent=2)}
"""
        if user.role == 'candidate':
            base += """
You help candidates with:
- Checking their application status and pipeline stage
- Resume and ATS score improvement tips
- Interview preparation advice
- Understanding the hiring process
- Navigating the HireZap platform
"""
        elif user.role == 'recruiter':
            base += """
You help recruiters with:
- Overview of active jobs and applications
- Understanding screening results
- Pipeline management guidance
- ATS configuration tips
- Using HireZap features effectively
"""
        return base
