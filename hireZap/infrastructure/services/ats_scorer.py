"""
infrastructure/services/ats_scorer.py
Updated to use google.genai (new package) - Maintains all existing functionality
"""
from google import genai
from google.genai import types
from typing import Dict, List
from django.conf import settings
import json


class ATSScorer:
    """AI powered ATS scoring by using Google Gemini"""

    def __init__(self, api_key: str):
        # Initialize the new Gemini client
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-1.5-flash'  # Keep using the same model

    def calculate_score(
            self,
            resume_text: str,
            parsed_data: Dict,
            ats_config: Dict,
            job_requirements: Dict
        ) -> Dict:
        """Calculate comprehensive score"""

        passing_score = ats_config.get('passing_score', 60)

        # 1. Skills score
        skills_score = self._calculate_skills_score(
            parsed_data['matched_skills'],
            parsed_data['missing_skills'],
            ats_config
        )

        # 2. Experience score
        experience_score = self._calculate_experience_score(
            parsed_data['experience_years'],
            ats_config['minimum_experience_years']
        )

        # 3. Education Score
        education_score = self._calculate_education_score(
            parsed_data['education'],
            ats_config.get('required_education')
        )
        
        # 4. Keywords Score
        keywords_score = self._calculate_keywords_score(
            parsed_data['matched_keywords'],
            ats_config.get('important_keywords', [])
        )
        
        # 5. Calculate weighted overall score
        overall_score = (
            (skills_score * ats_config['skills_weight'] / 100) +
            (experience_score * ats_config['experience_weight'] / 100) +
            (education_score * ats_config['education_weight'] / 100) +
            (keywords_score * ats_config['keywords_weight'] / 100)
        )
        
        # 6. Get AI analysis
        ai_analysis = self._get_ai_analysis(
            resume_text,
            job_requirements,
            overall_score
        )
        
        # 7. Make decision
        decision = 'qualified' if overall_score >= ats_config['passing_score'] else 'rejected'
        
        # Auto-rejection checks
        if ats_config.get('auto_rejection_missing_skills', False):
            if len(parsed_data['missing_skills']) > 0:
                decision = 'rejected'
                overall_score = min(overall_score, 40)  # Cap at 40 if missing required skills
        
        if ats_config.get('auto_reject_below_experience', False):
            min_exp = ats_config.get('minimum_experience_years', 0)
            if parsed_data['experience_years'] < min_exp:
                decision = 'rejected'
                overall_score = min(overall_score, 45)  # Cap at 45 if below experience
        
        # Final decision if no auto-rejection
        decision = 'qualified' if overall_score >= passing_score else 'rejected'
        
        return {
            'overall_score': int(overall_score),
            'decision': decision,
            'skills_score': skills_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'keywords_score': keywords_score,
            'ai_summary': ai_analysis['summary'],
            'strengths': ai_analysis['strengths'],
            'weaknesses': ai_analysis['weaknesses'],
            'recommendation_notes': ai_analysis['notes']
        }

    def _calculate_skills_score(
            self,
            matched_skills: List[str],
            missing_skills: List[str],
            ats_config: Dict
        ) -> int:
        """Calculate skills match score"""
        total_required = len(matched_skills) + len(missing_skills)
        if total_required == 0:
            return 50
        match_percentage = (len(matched_skills) / total_required) * 100
        return int(match_percentage)
    
    def _calculate_experience_score(
        self,
        candidate_years: float,
        required_years: int
    ) -> int:
        """Calculate experience score"""
        if required_years == 0:
            return 100  # No requirement
        
        if candidate_years >= required_years:
            # Extra experience gives bonus points (capped at 100)
            bonus = min((candidate_years - required_years) * 10, 20)
            return min(100, 100 + bonus)
        else:
            # Penalize for missing experience
            return int((candidate_years / required_years) * 100)
    
    def _calculate_education_score(
        self,
        candidate_education: str,
        required_education: str
    ) -> int:
        """Calculate education score"""
        if not required_education:
            return 100
        
        education_hierarchy = {
            'diploma': 1,
            'associate': 2,
            'bachelor': 3,
            'master': 4,
            'phd': 5,
            'doctorate': 5
        }
        
        candidate_level = education_hierarchy.get(candidate_education.lower(), 0)
        required_level = education_hierarchy.get(required_education.lower(), 0)
        
        if candidate_level >= required_level:
            return 100
        else:
            return max(0, int((candidate_level / required_level) * 100))
    
    def _calculate_keywords_score(
        self,
        matched_keywords: List[str],
        important_keywords: List[str]
    ) -> int:
        """Calculate keywords match score"""
        if len(important_keywords) == 0:
            return 100
        
        match_percentage = (len(matched_keywords) / len(important_keywords)) * 100
        return int(match_percentage)
    
    def _get_ai_analysis(
        self,
        resume_text: str,
        job_requirements: Dict,
        overall_score: float
    ) -> Dict:
        """Get AI-powered analysis using Gemini (Updated to new API)"""
        
        prompt = f"""
Analyze this resume for the given job and provide insights.

**Job Requirements:**
- Skills: {', '.join(job_requirements.get('skills_required', []))}
- Responsibilities: {job_requirements.get('key_responsibilities', '')}
- Requirements: {job_requirements.get('requirements', '')}

**Resume Text:**
{resume_text[:3000]}

**Current ATS Score:** {overall_score}/100

Provide your response as a JSON object:
{{
    "summary": "<2-3 sentence overall assessment>",
    "strengths": [<list of 3-5 key strengths>],
    "weaknesses": [<list of 3-5 areas of concern>],
    "notes": "<brief recommendation notes>"
}}

Provide ONLY the JSON response, no markdown formatting.
"""
        
        try:
            # Use the new API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            # Get response text
            response_text = response.text.strip()
            
            # Clean JSON (same logic as before)
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            return result
            
        except Exception as e:
            print(f"⚠️ AI analysis error: {str(e)}")
            # Fallback if AI fails (same as before)
            return {
                'summary': f"Automated screening completed with score: {overall_score}/100",
                'strengths': ["Resume processed successfully"],
                'weaknesses': ["Detailed analysis unavailable"],
                'notes': "System analysis only"
            }