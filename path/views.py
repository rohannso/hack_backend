from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LearningPath
from .serializers import LearningPathSerializer
import json
import requests
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any, Union, Optional
from django.conf import settings

User = get_user_model()

class LLMLearningPathGenerator:
    """
    A learning path generator that uses Groq's LLM API to analyze diagnostic assessment results
    and create personalized learning paths with AI-driven recommendations.
    """
    
    # Base subjects and difficulty levels
    SUBJECTS = ['Math', 'Reading', 'Science', 'Language']
    DIFFICULTY_LEVELS = ['Basic', 'Intermediate', 'Advanced']
    
    # Learning styles to tailor recommendations
    LEARNING_STYLES = ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']
    
    # Career paths for goal-oriented recommendations
    CAREER_PATHS = {
        'STEM': ['Software Engineer', 'Data Scientist', 'Researcher', 'Doctor'],
        'Humanities': ['Writer', 'Journalist', 'Teacher', 'Legal Professional'],
        'Business': ['Entrepreneur', 'Manager', 'Consultant', 'Financial Analyst']
    }
    
    def __init__(self, 
                 diagnostic_data: Union[Dict, str],
                 api_key: Optional[str] = None,
                 model: str = "llama3-70b-8192"):
        """
        Initialize the LLM learning path generator.
        """
        # Parse input data if it's a string
        if isinstance(diagnostic_data, str):
            self.diagnostic_data = json.loads(diagnostic_data)
        else:
            self.diagnostic_data = diagnostic_data
        
        # Extract components from diagnostic data
        self.questions = self.diagnostic_data.get('questions', [])
        self.student_info = self.diagnostic_data.get('student_info', {})
        
        # Set up API access - use settings
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("Groq API key must be provided or set as GROQ_API_KEY environment variable")
        
        self.model = model
        self.api_base = "https://api.groq.com/openai/v1"
        
        # Subject performance tracking
        self.subject_scores = self._initialize_scores()
    
    def _initialize_scores(self) -> Dict:
        """Initialize scoring structure for basic performance tracking"""
        return {subject: {'correct': 0, 'total': 0} for subject in self.SUBJECTS}
    
    def _calculate_basic_metrics(self) -> Dict:
        """Calculate basic performance metrics as context for the LLM"""
        # Count correct/incorrect responses per subject
        for question in self.questions:
            subject = question.get('subject')
            correct = question.get('correct', False)
            
            if subject in self.SUBJECTS:
                self.subject_scores[subject]['total'] += 1
                if correct:
                    self.subject_scores[subject]['correct'] += 1
        
        # Calculate percentages
        metrics = {}
        for subject, scores in self.subject_scores.items():
            if scores['total'] > 0:
                percentage = (scores['correct'] / scores['total']) * 100
                metrics[subject] = {
                    'percentage': round(percentage, 1),
                    'correct': scores['correct'],
                    'total': scores['total']
                }
            else:
                metrics[subject] = {'percentage': 0, 'correct': 0, 'total': 0}
                
        return metrics
    
    def _analyze_difficulty_progression(self) -> Dict:
        """Analyze which difficulty level is appropriate for each subject"""
        metrics = self._calculate_basic_metrics()
        difficulty_mapping = {}
        
        for subject, data in metrics.items():
            percentage = data['percentage']
            if percentage >= 80:
                difficulty_mapping[subject] = 'Advanced'
            elif percentage >= 60:
                difficulty_mapping[subject] = 'Intermediate'
            else:
                difficulty_mapping[subject] = 'Basic'
                
        return difficulty_mapping
    
    def _call_llm_api(self, prompt: str) -> Dict:
        """Make API call to Groq LLM"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2500,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions", 
                headers=headers, 
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return json.loads(result["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "error": str(e),
                "learning_path": {
                    "strengths": [],
                    "weaknesses": [],
                    "recommended_topics": []
                }
            }
    
    def _create_analysis_prompt(self) -> str:
        """Create a detailed prompt for the LLM to analyze student performance"""
        metrics = self._calculate_basic_metrics()
        
        prompt = f"""
        You are an expert educational AI that analyzes student performance data and creates personalized learning paths.
        
        # Student Information
        {json.dumps(self.student_info, indent=2)}
        
        # Performance Metrics
        {json.dumps(metrics, indent=2)}
        
        # Detailed Question Responses
        {json.dumps(self.questions, indent=2)}
        
        Based on this information, analyze the student's performance across subjects, identify patterns, 
        misconceptions, strengths, and weaknesses.
        
        Return a detailed analysis in JSON format with the following structure:
        {{
            "strengths": ["list of subjects or topics the student excels at"],
            "weaknesses": ["list of subjects or topics the student struggles with"],
            "knowledge_gaps": ["specific areas where remediation is needed"],
            "misconceptions": ["identified misconceptions from incorrect answers"],
            "learning_style_insights": "observations about effective learning approaches for this student",
            "cognitive_patterns": ["identified patterns in how the student approaches problems"],
            "error_analysis": [
                {{
                    "subject": "subject name",
                    "pattern": "description of error pattern",
                    "remediation": "specific remediation approach"
                }}
            ],
            "perceived_learning_style": "most likely learning style from {self.LEARNING_STYLES}",
            "motivation_analysis": "analysis of intrinsic vs extrinsic motivation factors"
        }}
        """
        
        return prompt
    
    def _create_learning_path_prompt(self, analysis: Dict) -> str:
        """Create a prompt for the LLM to generate a learning path based on analysis"""
        difficulty_mapping = self._analyze_difficulty_progression()
        
        prompt = f"""
        You are an expert educational AI that creates personalized learning paths.
        
        # Student Information
        {json.dumps(self.student_info, indent=2)}
        
        # Performance Analysis
        {json.dumps(analysis, indent=2)}
        
        # Current Difficulty Mapping
        {json.dumps(difficulty_mapping, indent=2)}
        
        Based on this analysis, create a comprehensive, personalized learning path for this student,
        acting as both a mentor and expert educator. Consider the student's strengths, weaknesses, 
        learning style, cognitive patterns, motivation factors, and long-term educational goals.
        
        Return a detailed learning path in JSON format with the following structure:
        {{
            "difficulty_levels": {{"subject": "level"}},
            "recommended_topics": ["specific topics to focus on"],
            "prioritized_subjects": ["subjects that need immediate attention"],
            "estimated_completion_time": {{"weeks": number, "estimated_completion_date": "YYYY-MM-DD"}},
            "recommended_resources": [
                {{
                    "name": "resource name",
                    "type": "book|video|interactive|course",
                    "difficulty": "Basic|Intermediate|Advanced",
                    "subjects": ["applicable subjects"],
                    "alignment": "how this matches student's learning style",
                    "url": "optional URL if applicable"
                }}
            ],
            "study_plan": [
                {{
                    "week": number,
                    "focus_areas": ["main subjects to focus on"],
                    "activities": [
                        {{
                            "subject": "subject name",
                            "topics": ["specific topics"],
                            "hours": number,
                            "resources": ["specific resources"],
                            "practice_focus": "specific skills to practice"
                        }}
                    ],
                    "review_strategies": ["spaced repetition", "active recall"],
                    "milestone_check": "mini-assessment guidance"
                }}
            ],
            "milestones": [
                {{
                    "title": "milestone description",
                    "subjects": ["relevant subjects"],
                    "topics": ["specific topics"],
                    "target_date": "YYYY-MM-DD",
                    "assessment_method": "how to verify achievement",
                    "prerequisites": ["concepts that must be mastered first"]
                }}
            ],
            "mentor_guidance": [
                {{
                    "topic": "guidance topic",
                    "advice": "specific mentor advice",
                    "common_pitfalls": ["typical challenges to avoid"],
                    "success_strategies": ["approaches that work well"]
                }}
            ],
            "skill_roadmap": {{
                "foundational_skills": ["basic skills that need mastery"],
                "intermediate_skills": ["skills to develop after basics"],
                "advanced_skills": ["expert-level skills for long-term development"]
            }},
            "adaptive_recommendations": "personalized advice for this specific student",
            "metacognitive_strategies": ["strategies to improve learning effectiveness"],
            "growth_mindset_development": "approaches to build resilience and perseverance"
        }}
        """
        
        return prompt
    
    def _create_expert_roadmap_prompt(self, learning_path: Dict) -> str:
        """Create a prompt for generating an expert roadmap with comprehensive guidance"""
        prompt = f"""
        You are a master educator with decades of experience in personalized learning design.
        
        # Student Information
        {json.dumps(self.student_info, indent=2)}
        
        # Current Learning Path
        {json.dumps(learning_path, indent=2)}
        
        Based on this student's profile and learning path, create a comprehensive expert roadmap
        that extends beyond basic learning topics to include expert-level guidance, career path integration,
        and long-term skill development. Act as a mentor who can see the big picture of how this
        student's current learning connects to future success.
        
        Return an expert roadmap in JSON format with the following structure:
        {{
            "long_term_vision": {{
                "educational_trajectory": "path from current level to mastery",
                "skill_evolution": "how skills will progress over time",
                "potential_career_paths": ["career options this education enables"],
                "expert_level_outcomes": ["what mastery looks like in these subjects"]
            }},
            "skill_interconnections": [
                {{
                    "primary_skill": "skill name",
                    "connected_skills": ["related skills"],
                    "synergy_explanation": "how these skills reinforce each other"
                }}
            ],
            "expert_guidance": [
                {{
                    "topic": "guidance area",
                    "common_misconceptions": ["misconceptions to overcome"],
                    "expert_insights": "how experts approach this differently",
                    "advanced_techniques": ["techniques that accelerate mastery"]
                }}
            ],
            "mastery_progression": [
                {{
                    "phase": "beginner|intermediate|advanced|expert",
                    "duration": "estimated time in this phase",
                    "focus_areas": ["key areas of focus"],
                    "success_indicators": ["how to know you're ready to advance"],
                    "common_challenges": ["typical hurdles at this stage"],
                    "recommended_approaches": ["best methods for this phase"]
                }}
            ],
            "real_world_applications": [
                {{
                    "skill_set": ["related skills"],
                    "applications": ["real-world uses"],
                    "project_ideas": ["projects to build these skills"],
                    "industry_relevance": "how these skills apply professionally"
                }}
            ],
            "learning_community": {{
                "recommended_communities": ["forums, groups or communities"],
                "networking_opportunities": ["ways to connect with peers and experts"],
                "collaborative_projects": ["ideas for group learning"]
            }},
            "advanced_resources": [
                {{
                    "name": "resource name",
                    "type": "book|course|mentor|community",
                    "difficulty": "intermediate|advanced|expert",
                    "topic_coverage": ["specific topics covered"],
                    "special_value": "what makes this resource especially valuable"
                }}
            ],
            "development_timeline": {{
                "short_term_goals": ["3-month objectives"],
                "medium_term_goals": ["1-year objectives"],
                "long_term_goals": ["3-5 year objectives"],
                "milestone_achievements": ["significant achievements to target"]
            }},
            "mastery_principles": ["key principles that enable expertise development"],
            "expert_study_techniques": ["advanced techniques for optimal learning"]
        }}
        """
        
        return prompt
    
    def _get_completion_date(self, weeks: int) -> str:
        """Calculate estimated completion date based on weeks"""
        completion_date = datetime.now() + timedelta(weeks=weeks)
        return completion_date.strftime('%Y-%m-%d')
    
    def _ensure_valid_structure(self, learning_path: Dict) -> Dict:
        """Ensure the learning path has all required fields with valid data"""
        if "difficulty_levels" not in learning_path:
            learning_path["difficulty_levels"] = {subject: "Basic" for subject in self.SUBJECTS}
            
        if "estimated_completion_time" not in learning_path:
            learning_path["estimated_completion_time"] = {
                "weeks": 4, 
                "estimated_completion_date": self._get_completion_date(4)
            }
        elif "estimated_completion_date" not in learning_path["estimated_completion_time"]:
            weeks = learning_path["estimated_completion_time"].get("weeks", 4)
            learning_path["estimated_completion_time"]["estimated_completion_date"] = self._get_completion_date(weeks)
            
        if "study_plan" not in learning_path or not learning_path["study_plan"]:
            learning_path["study_plan"] = [{
                "week": 1,
                "focus_areas": learning_path.get("weaknesses", [self.SUBJECTS[0]]),
                "activities": [{
                    "subject": self.SUBJECTS[0],
                    "topics": learning_path.get("recommended_topics", ["Fundamentals"])[:2],
                    "hours": 5,
                    "resources": ["online tutorials", "practice exercises"]
                }]
            }]
            
        if "recommended_topics" not in learning_path or not learning_path["recommended_topics"]:
            learning_path["recommended_topics"] = ["Fundamentals review", "Core skills practice"]
            
        return learning_path
    
    def _validate_expert_roadmap(self, roadmap: Dict) -> Dict:
        """Ensure the expert roadmap has all required fields with valid data"""
        if "long_term_vision" not in roadmap:
            roadmap["long_term_vision"] = {
                "educational_trajectory": "Progressive mastery from foundational to advanced skills",
                "skill_evolution": "Iterative development with increasing complexity",
                "potential_career_paths": ["Educator", "Specialist", "Researcher"],
                "expert_level_outcomes": ["Independent problem solving", "Knowledge creation"]
            }
            
        if "mastery_progression" not in roadmap or not roadmap["mastery_progression"]:
            roadmap["mastery_progression"] = [
                {
                    "phase": "beginner",
                    "duration": "3-6 months",
                    "focus_areas": ["Fundamentals", "Core concepts"],
                    "success_indicators": ["Consistent application of basic principles"],
                    "common_challenges": ["Overwhelm with new information"],
                    "recommended_approaches": ["Structured practice", "Guided learning"]
                },
                {
                    "phase": "intermediate",
                    "duration": "6-12 months",
                    "focus_areas": ["Integration of concepts", "Problem solving"],
                    "success_indicators": ["Independent application of principles"],
                    "common_challenges": ["Plateaus in skill development"],
                    "recommended_approaches": ["Project-based learning", "Pattern recognition"]
                }
            ]
            
        if "development_timeline" not in roadmap:
            roadmap["development_timeline"] = {
                "short_term_goals": ["Master fundamental concepts", "Develop consistent study habits"],
                "medium_term_goals": ["Independently solve complex problems", "Teach basics to others"],
                "long_term_goals": ["Contribute original insights", "Achieve expert-level proficiency"],
                "milestone_achievements": ["Complete capstone projects", "Earn recognized certifications"]
            }
            
        return roadmap
    
    def _merge_learning_path_and_roadmap(self, learning_path: Dict, roadmap: Dict) -> Dict:
        """Merge the learning path and expert roadmap into a comprehensive plan"""
        comprehensive_plan = learning_path.copy()
        
        # Add roadmap components to main plan
        comprehensive_plan["expert_roadmap"] = roadmap
        
        # Enhance existing fields with roadmap insights
        if "skill_roadmap" in comprehensive_plan and "mastery_progression" in roadmap:
            for phase in roadmap["mastery_progression"]:
                if phase["phase"] == "beginner":
                    comprehensive_plan["skill_roadmap"]["foundational_skills"] = list(set(
                        comprehensive_plan["skill_roadmap"].get("foundational_skills", []) + 
                        phase.get("focus_areas", [])
                    ))
                elif phase["phase"] == "intermediate":
                    comprehensive_plan["skill_roadmap"]["intermediate_skills"] = list(set(
                        comprehensive_plan["skill_roadmap"].get("intermediate_skills", []) + 
                        phase.get("focus_areas", [])
                    ))
                elif phase["phase"] in ["advanced", "expert"]:
                    comprehensive_plan["skill_roadmap"]["advanced_skills"] = list(set(
                        comprehensive_plan["skill_roadmap"].get("advanced_skills", []) + 
                        phase.get("focus_areas", [])
                    ))
        
        # Add mentor guidance from both sources
        if "expert_guidance" in roadmap:
            if "mentor_guidance" not in comprehensive_plan:
                comprehensive_plan["mentor_guidance"] = []
            
            for guidance in roadmap["expert_guidance"]:
                mentor_item = {
                    "topic": guidance["topic"],
                    "advice": guidance.get("expert_insights", ""),
                    "common_pitfalls": guidance.get("common_misconceptions", []),
                    "success_strategies": guidance.get("advanced_techniques", [])
                }
                comprehensive_plan["mentor_guidance"].append(mentor_item)
        
        return comprehensive_plan
    
    def generate_learning_path(self) -> Dict:
        """Generate a personalized learning path using LLM analysis"""
        # Step 1: Get detailed analysis from LLM
        analysis_prompt = self._create_analysis_prompt()
        analysis = self._call_llm_api(analysis_prompt)
        
        # Step 2: Use analysis to generate learning path
        learning_path_prompt = self._create_learning_path_prompt(analysis)
        learning_path = self._call_llm_api(learning_path_prompt)
        
        # Step 3: Ensure all required fields exist and are valid
        learning_path = self._ensure_valid_structure(learning_path)
        
        # Step 4: Generate expert roadmap
        roadmap_prompt = self._create_expert_roadmap_prompt(learning_path)
        expert_roadmap = self._call_llm_api(roadmap_prompt)
        expert_roadmap = self._validate_expert_roadmap(expert_roadmap)
        
        # Step 5: Merge learning path, roadmap and analysis into comprehensive plan
        comprehensive_plan = self._merge_learning_path_and_roadmap(learning_path, expert_roadmap)
        
        # Add student info and analysis
        comprehensive_plan["student_info"] = self.student_info
        for key in analysis:
            if key not in comprehensive_plan:
                comprehensive_plan[key] = analysis[key]
        
        return comprehensive_plan
    
    def get_learning_path_summary(self, learning_path: Dict) -> Dict:
        """Generate a concise summary of the learning path for quick reference"""
        summary = {
            "student_name": self.student_info.get("name", "Student"),
            "grade_level": self.student_info.get("grade_level", "Not specified"),
            "top_strengths": learning_path.get("strengths", [])[:3],
            "priority_focus_areas": learning_path.get("weaknesses", [])[:3],
            "estimated_completion": learning_path.get("estimated_completion_time", {}).get("estimated_completion_date", "Not specified"),
            "key_milestones": [milestone.get("title") for milestone in learning_path.get("milestones", [])[:3]],
            "recommended_approach": learning_path.get("adaptive_recommendations", "Personalized learning"),
            "long_term_goals": learning_path.get("expert_roadmap", {}).get("development_timeline", {}).get("long_term_goals", [])[:2]
        }
        return summary
    
    def generate_progress_tracker(self, learning_path: Dict) -> Dict:
        """Generate a progress tracking structure based on the learning path"""
        tracker = {
            "student_info": self.student_info,
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "estimated_completion_date": learning_path.get("estimated_completion_time", {}).get("estimated_completion_date", ""),
            "weekly_progress": [],
            "milestones": []
        }
        
        # Create tracking entries for each week
        for week_plan in learning_path.get("study_plan", []):
            week_entry = {
                "week": week_plan.get("week", 0),
                "activities": [],
                "completion_status": "Not Started",
                "notes": "",
                "reflection_questions": [
                    "What went well this week?",
                    "What challenges did you face?",
                    "What strategies helped you learn effectively?",
                    "What adjustments are needed for next week?"
                ]
            }
            
            # Create activity tracking for each activity
            for activity in week_plan.get("activities", []):
                activity_entry = {
                    "subject": activity.get("subject", ""),
                    "topics": activity.get("topics", []),
                    "completed_hours": 0,
                    "target_hours": activity.get("hours", 0),
                    "status": "Not Started",
                    "difficulty_experienced": "Not Rated",
                    "mastery_self_assessment": "Not Rated"
                }
                week_entry["activities"].append(activity_entry)
            
            tracker["weekly_progress"].append(week_entry)
        
        # Create milestone tracking entries
        for milestone in learning_path.get("milestones", []):
            milestone_entry = {
                "title": milestone.get("title", ""),
                "target_date": milestone.get("target_date", ""),
                "subjects": milestone.get("subjects", []),
                "status": "Not Started",
                "assessment_result": "",
                "reflection": ""
            }
            tracker["milestones"].append(milestone_entry)
        
        return tracker

class LearningPathView(APIView):
    def post(self, request, *args, **kwargs):
        """Generate and save a learning path for a specific user"""
        user_id = request.data.get("user_id")
        diagnostic_responses = request.data.get("responses", [])

        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not diagnostic_responses:
            return Response({"error": "No responses provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            self._validate_responses(diagnostic_responses)
            
            # Prepare diagnostic data for LLM
            diagnostic_data = {
                "student_info": {
                    "user_id": user_id,
                    "username": user.username,
                },
                "questions": [
                    {
                        "question_text": response["question"],
                        "correct": response["answer"].lower() == "correct",
                        "subject": self._determine_subject(response["question"])
                    }
                    for response in diagnostic_responses
                ]
            }
            
            # Generate learning path using LLM
            generator = LLMLearningPathGenerator(diagnostic_data)
            learning_path = generator.generate_learning_path()

            # Save to database
            learning_path_obj = LearningPath.objects.create(
                student=user,
                path_data=learning_path
            )

            return Response({
                "message": "Learning path generated successfully",
                "learning_path": learning_path,
                "id": learning_path_obj.id,
                "created_at": learning_path_obj.created_at,
                "user_id": user_id
            }, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Failed to generate learning path", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Retrieve user's learning paths"""
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(id=user_id)
            learning_paths = LearningPath.objects.filter(student=user)
            serializer = LearningPathSerializer(learning_paths, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def _validate_responses(self, responses):
        required_fields = ['question', 'answer']
        for response in responses:
            if not isinstance(response, dict):
                raise ValueError("Each response must be an object")
            if not all(field in response for field in required_fields):
                raise ValueError(f"Each response must contain: {', '.join(required_fields)}")

    def _determine_subject(self, question):
        """Determine the subject of a question based on keywords"""
        subjects = {
            'Math': ['math', 'arithmetic', 'algebra', 'equation', 'number'],
            'Reading': ['reading', 'story', 'passage', 'text', 'comprehension'],
            'Science': ['science', 'scientific', 'biology', 'chemistry', 'physics'],
            'Language': ['grammar', 'sentence', 'vocabulary', 'spelling', 'writing']
        }
        
        question = question.lower()
        for subject, keywords in subjects.items():
            if any(keyword in question for keyword in keywords):
                return subject
        return 'General'
