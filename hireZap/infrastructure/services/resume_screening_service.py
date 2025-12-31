from infrastructure.services.resume_parser import ResumeParser
from infrastructure.services.ats_scorer import ATSScorer
from django.conf import settings
from typing import Dict
import time

class ResumeScreeningService:
    """Main service to handle resume screening"""
    def __init__(self):
        self.parser = ResumeParser()
        self.scorer = ATSScorer(api_key=settings.GEMINI_API_KEY)

    def screen_resume(self, resume_url:str, ats_config:Dict, job_requirements:Dict) -> Dict:
        """Complete resume screening pipeline"""
        start_time = time.time()
        try:
            # step -1 Download resume
            pdf_content = self.parser.download_resume(resume_url)

            # step - 2 Extract text
            resume_text = self.parser.extract_text_from_pdf(pdf_content)

            if not resume_text or len(resume_text) < 50:
                raise Exception("Failed to extract text from resume or resume is too short")
            
            # step - 3 parse resume data
            parsed_data = {
                'experience_years': self.parser.extract_experience_years(resume_text),
                'education': self.parser.extract_education(resume_text),
                'matched_skills': self.parser.find_skills(
                    resume_text,
                    ats_config.get('required_skills', []) + ats_config.get('preferred_skills', [])
                ),
                'missing_skills': [],
                'matched_keywords': self.parser.find_keywords(
                    resume_text,
                    ats_config.get('important_keywords', [])
                ),
            }

            # Calculate missing skills
            all_required = set(ats_config.get('required_skills', []))
            matched_set = set(parsed_data['matched_skills'])
            parsed_data['missing_skills'] = list(all_required - matched_set)
            
            # Step 4: Check ATS friendliness
            is_ats_friendly, ats_issues = self.parser.check_ats_friendliness(
                resume_text,
                pdf_content
            )
            
            # Step 5: Calculate comprehensive score
            scoring_result = self.scorer.calculate_score(
                resume_text,
                parsed_data,
                ats_config,
                job_requirements
            )
            
            # Step 6: Combine all results
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'scores': {
                    'overall': scoring_result['overall_score'],
                    'skills': scoring_result['skills_score'],
                    'experience': scoring_result['experience_score'],
                    'education': scoring_result['education_score'],
                    'keywords': scoring_result['keywords_score'],
                },
                'decision': scoring_result['decision'],
                'parsed_data': parsed_data,
                'ats_friendly': is_ats_friendly,
                'ats_issues': ats_issues,
                'ai_analysis': {
                    'summary': scoring_result['ai_summary'],
                    'strengths': scoring_result['strengths'],
                    'weaknesses': scoring_result['weaknesses'],
                    'notes': scoring_result['recommendation_notes'],
                },
                'processing_time': processing_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }