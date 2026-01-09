import requests
import json
from typing import Dict, List, BinaryIO
from django.conf import settings
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
import tempfile
import os


class TranscriptionService:
    """
    FREE audio transcription using faster-whisper (local processing)
    No API costs - runs on your machine!
    """
    
    def __init__(self):
        """
        Initialize Whisper model
        
        Models available (in order of accuracy vs speed):
        - tiny: Fastest, least accurate (~1GB RAM)
        - base: Good balance (~1GB RAM)
        - small: Better accuracy (~2GB RAM)
        - medium: Very good accuracy (~5GB RAM)
        - large-v2: Best accuracy (~10GB RAM)
        - large-v3: Latest, best accuracy (~10GB RAM)
        """
        # Use 'base' for good balance of speed and accuracy
        # Change to 'small' or 'medium' for better accuracy
        # Use 'tiny' if you have limited RAM/CPU
        self.model_size = getattr(settings, 'WHISPER_MODEL_SIZE', 'base')
        
        # Device: 'cpu' or 'cuda' (if you have NVIDIA GPU)
        # compute_type: 'int8' for CPU, 'float16' for GPU
        self.device = getattr(settings, 'WHISPER_DEVICE', 'cpu')
        self.compute_type = 'int8' if self.device == 'cpu' else 'float16'
        
        print(f"🎤 Loading Whisper model: {self.model_size} on {self.device}...")
        
        # Load model (downloads on first use, then cached)
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=None  # Uses default cache directory
        )
        
        print(f"✅ Whisper model loaded successfully!")
    
    def transcribe_audio(
        self,
        audio_file: BinaryIO,
        language: str = "en"
    ) -> Dict:
        """
        Transcribe audio file using local Whisper model (FREE!)
        
        Args:
            audio_file: Audio file object (WAV, MP3, M4A, etc.)
            language: Language code (en, es, fr, etc.)
        
        Returns:
            {
                'success': bool,
                'text': str,
                'segments': list,
                'language': str,
                'duration': float
            }
        """
        temp_path = None
        
        try:
            # Save uploaded file to temporary location
            temp_path = self._save_temp_file(audio_file)
            
            print(f"📝 Starting transcription: {temp_path}")
            
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                temp_path,
                language=language if language != "auto" else None,
                beam_size=5,  # Higher = more accurate but slower
                vad_filter=True,  # Voice Activity Detection (removes silence)
                vad_parameters=dict(
                    min_silence_duration_ms=500  # Minimum silence to split
                )
            )
            
            # Process segments
            full_text = ""
            processed_segments = []
            
            for segment in segments:
                full_text += segment.text + " "
                processed_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip()
                })
            
            print(f"✅ Transcription completed: {len(full_text)} characters")
            print(f"📊 Language: {info.language} (probability: {info.language_probability:.2f})")
            print(f"⏱️ Duration: {info.duration:.2f} seconds")
            
            return {
                'success': True,
                'text': full_text.strip(),
                'segments': processed_segments,
                'language': info.language,
                'duration': info.duration,
                'confidence': info.language_probability
            }
            
        except Exception as e:
            print(f"❌ Transcription Error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _save_temp_file(self, audio_file: BinaryIO) -> str:
        """Save uploaded file to temporary location"""
        # Create temp file with original extension
        suffix = os.path.splitext(audio_file.name)[1] if hasattr(audio_file, 'name') else '.wav'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            # Reset file pointer
            audio_file.seek(0)
            
            # Write content
            for chunk in audio_file.chunks() if hasattr(audio_file, 'chunks') else [audio_file.read()]:
                temp_file.write(chunk)
            
            return temp_file.name


class InterviewScorerService:
    """
    AI-powered interview scoring using Gemini (Updated to new API)
    """
    
    def __init__(self):
        # Initialize the new Gemini client
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    def analyze_interview(
        self,
        transcription: str,
        job_requirements: Dict,
        settings: Dict
    ) -> Dict:
        """
        Analyze interview transcription and generate scores
        
        Args:
            transcription: Full interview text
            job_requirements: Job details and requirements
            settings: Telephonic round settings with weights
        
        Returns:
            {
                'scores': {...},
                'decision': 'qualified' | 'not_qualified',
                'analysis': {...}
            }
        """
        try:
            # Build prompt for Gemini
            prompt = self._build_analysis_prompt(
                transcription,
                job_requirements,
                settings
            )
            
            # Get AI analysis using new API
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2000
                )
            )
            
            # Get response text
            analysis_text = response.text.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0]
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0]
            
            analysis = json.loads(analysis_text.strip())
            
            # Calculate weighted overall score
            scores = analysis['scores']
            weights = settings
            
            overall_score = (
                scores['communication'] * (weights.get('communication_weight', 30) / 100) +
                scores['technical_knowledge'] * (weights.get('technical_knowledge_weight', 25) / 100) +
                scores['problem_solving'] * (weights.get('problem_solving_weight', 20) / 100) +
                scores['enthusiasm'] * (weights.get('enthusiasm_weight', 10) / 100) +
                scores['clarity'] * (weights.get('clarity_weight', 10) / 100) +
                scores['professionalism'] * (weights.get('professionalism_weight', 5) / 100)
            )
            
            scores['overall'] = round(overall_score)
            
            # Determine decision
            min_score = settings.get('minimum_qualifying_score', 70)
            decision = 'qualified' if scores['overall'] >= min_score else 'not_qualified'
            
            return {
                'success': True,
                'scores': scores,
                'decision': decision,
                'analysis': {
                    'summary': analysis.get('summary', ''),
                    'highlights': analysis.get('highlights', []),
                    'improvements': analysis.get('improvements', []),
                    'technical': analysis.get('technical_assessment', ''),
                    'communication': analysis.get('communication_assessment', ''),
                    'topics': analysis.get('topics_discussed', []),
                    'questions_count': analysis.get('questions_asked', 0)
                }
            }
            
        except Exception as e:
            print(f"❌ Interview Analysis Error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_analysis_prompt(
        self,
        transcription: str,
        job_requirements: Dict,
        settings: Dict
    ) -> str:
        """Build prompt for AI analysis"""
        
        prompt = f"""
You are an expert technical interviewer analyzing a telephonic interview transcript.

JOB DETAILS:
- Position: {job_requirements.get('job_title', 'Not specified')}
- Required Skills: {', '.join(job_requirements.get('required_skills', []))}
- Experience Required: {job_requirements.get('minimum_experience', 'Not specified')} years
- Key Responsibilities: {job_requirements.get('responsibilities', 'Not specified')}

INTERVIEW TRANSCRIPT:
{transcription[:8000]}

SCORING CRITERIA:
Analyze the candidate's performance on these dimensions (0-100 scale):

1. Communication (Weight: {settings.get('communication_weight', 30)}%):
   - Clarity of speech and articulation
   - Ability to explain concepts clearly
   - Listening and comprehension skills

2. Technical Knowledge (Weight: {settings.get('technical_knowledge_weight', 25)}%):
   - Understanding of technical concepts
   - Depth of knowledge in required skills
   - Ability to discuss technical topics

3. Problem Solving (Weight: {settings.get('problem_solving_weight', 20)}%):
   - Approach to solving problems
   - Logical thinking and reasoning
   - Creativity in solutions

4. Enthusiasm (Weight: {settings.get('enthusiasm_weight', 10)}%):
   - Interest in the role and company
   - Passion for the field
   - Energy and engagement level

5. Clarity (Weight: {settings.get('clarity_weight', 10)}%):
   - Structured responses
   - Conciseness
   - Organization of thoughts

6. Professionalism (Weight: {settings.get('professionalism_weight', 5)}%):
   - Professional demeanor
   - Respect and courtesy
   - Appropriate language use

TASK:
Provide a comprehensive analysis in JSON format with:

{{
  "scores": {{
    "communication": <0-100>,
    "technical_knowledge": <0-100>,
    "problem_solving": <0-100>,
    "enthusiasm": <0-100>,
    "clarity": <0-100>,
    "professionalism": <0-100>
  }},
  "summary": "<2-3 sentence overall assessment>",
  "highlights": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "improvements": [
    "<area for improvement 1>",
    "<area for improvement 2>"
  ],
  "technical_assessment": "<detailed technical evaluation>",
  "communication_assessment": "<detailed communication evaluation>",
  "topics_discussed": ["<topic 1>", "<topic 2>"],
  "questions_asked": <number of questions candidate asked>
}}

Be objective, fair, and provide constructive feedback. Focus on evidence from the transcript.
Only return valid JSON, no markdown formatting.
"""
        return prompt


class AudioProcessorService:
    """
    Audio processing utilities
    """
    
    @staticmethod
    def validate_audio_file(file) -> Dict:
        """Validate audio file"""
        try:
            # Check file size (max 25MB for Whisper)
            max_size = 25 * 1024 * 1024  # 25MB
            if file.size > max_size:
                return {
                    'valid': False,
                    'error': 'File size exceeds 25MB limit'
                }
            
            # Check file extension
            allowed_formats = ['.mp3', '.mp4', '.wav', '.webm', '.m4a', '.ogg']
            import os
            _, ext = os.path.splitext(file.name)
            if ext.lower() not in allowed_formats:
                return {
                    'valid': False,
                    'error': f'Invalid format. Allowed: {", ".join(allowed_formats)}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """Get audio file duration in seconds"""
        try:
            import wave
            import contextlib
            
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return duration
        except:
            return 0.0