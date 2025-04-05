import logging
import json
import requests
from django.conf import settings
from typing import List, Dict
from django.utils import timezone

logger = logging.getLogger(__name__)

class TaskGenerator:
    """Service to generate tasks based on learning paths"""
    
    def _normalize_difficulty(self, difficulty: str) -> str:
        """Normalize difficulty values to match serializer expectations"""
        difficulty_map = {
            'basic': 'easy',
            'Basic': 'easy',
            'intermediate': 'medium',
            'Intermediate': 'medium',
            'advanced': 'hard',
            'Advanced': 'hard',
            # Keep existing valid values as-is
            'easy': 'easy',
            'medium': 'medium',
            'hard': 'hard'
        }
        return difficulty_map.get(difficulty, 'medium')  # Default to medium if unknown

    def generate_tasks(self, learning_objective: str, difficulty: str, student_grade: str) -> List[Dict]:
        """Generate a set of tasks for a given learning objective"""
        logger.info(f"Generating basic tasks for: {learning_objective}, difficulty: {difficulty}, grade: {student_grade}")
        
        # Normalize the difficulty value
        normalized_difficulty = self._normalize_difficulty(difficulty)
        logger.info(f"Normalized difficulty from '{difficulty}' to '{normalized_difficulty}'")
        
        task_types = ['quiz', 'assignment', 'interactive']
        tasks = []
        
        for task_type in task_types:
            task = {
                'title': f"{learning_objective} - {task_type.capitalize()}",
                'description': f"Complete this {task_type} to master {learning_objective}",
                'task_type': task_type,
                'difficulty': normalized_difficulty,  # Use normalized difficulty
                'learning_objective': learning_objective,
                'estimated_time': '30 minutes',
                'points': 100,
                'content': self._generate_task_content(task_type, learning_objective),
                'status': 'active',
                'created_at': timezone.now().isoformat(),
                'due_days': settings.TASK_GENERATION.get('DEFAULT_DUE_DAYS', 7)
            }
            tasks.append(task)
            logger.info(f"Generated {task_type} task for {learning_objective} with difficulty {normalized_difficulty}")
        
        return tasks

    def _generate_task_content(self, task_type: str, learning_objective: str) -> Dict:
        """Generate content based on task type"""
        if task_type == 'quiz':
            return {
                'instructions': f'Test your knowledge about {learning_objective}',
                'questions': [
                    {
                        'question': f'What is the primary purpose of {learning_objective}?',
                        'options': [
                            'To improve system efficiency',
                            'To enhance user experience',
                            'To maintain data integrity',
                            'To ensure security compliance'
                        ],
                        'correct_answer': 0,
                        'type': 'multiple_choice',
                        'explanation': 'Understanding the primary purpose helps establish the foundation.'
                    },
                    {
                        'question': f'Which of the following best describes {learning_objective}?',
                        'options': [
                            'A systematic approach to problem-solving',
                            'A collection of best practices',
                            'A framework for development',
                            'An implementation strategy'
                        ],
                        'correct_answer': 1,
                        'type': 'multiple_choice',
                        'explanation': 'This helps clarify the core concept.'
                    },
                    {
                        'question': 'True or False: Regular practice is essential for mastering this concept.',
                        'options': ['True', 'False'],
                        'correct_answer': 0,
                        'type': 'boolean',
                        'explanation': 'Practice is key to understanding and retention.'
                    },
                    {
                        'question': f'What are the key components of {learning_objective}?',
                        'type': 'short_answer',
                        'max_words': 100,
                        'sample_answer': 'The key components include fundamental principles, practical applications, and evaluation methods.'
                    }
                ],
                'time_limit': 30,  # in minutes
                'passing_score': 70,
                'show_explanations': True
            }
        elif task_type == 'assignment':
            return {
                'instructions': f'Complete this comprehensive assignment about {learning_objective}',
                'sections': [
                    {
                        'title': 'Theoretical Understanding',
                        'description': f'Explain the core concepts of {learning_objective}',
                        'type': 'essay',
                        'word_limit': 500,
                        'rubric': {
                            'understanding': 'Demonstrates clear understanding of concepts',
                            'analysis': 'Provides thoughtful analysis and examples',
                            'organization': 'Well-structured and coherent presentation'
                        }
                    },
                    {
                        'title': 'Practical Application',
                        'description': f'Design a solution using principles of {learning_objective}',
                        'type': 'project',
                        'requirements': [
                            'Clear problem statement',
                            'Detailed solution approach',
                            'Implementation considerations',
                            'Expected outcomes'
                        ],
                        'deliverables': [
                            'Project documentation',
                            'Implementation plan',
                            'Evaluation criteria'
                        ]
                    },
                    {
                        'title': 'Reflection',
                        'description': 'Reflect on your learning experience',
                        'type': 'short_answer',
                        'prompts': [
                            'What were the key insights you gained?',
                            'How can you apply these concepts in real-world scenarios?',
                            'What challenges did you face and how did you overcome them?'
                        ]
                    }
                ],
                'submission_format': 'pdf',
                'resources': [
                    'Course materials',
                    'Online documentation',
                    'Reference examples'
                ],
                'grading_criteria': {
                    'content': 40,
                    'analysis': 30,
                    'presentation': 20,
                    'reflection': 10
                }
            }
        else:  # interactive
            return {
                'activity_type': 'multi_stage_practice',
                'instructions': f'Complete this interactive learning session about {learning_objective}',
                'stages': [
                    {
                        'title': 'Concept Review',
                        'type': 'matching',
                        'items': [
                            {'id': 1, 'text': f'Definition of {learning_objective}'},
                            {'id': 2, 'text': 'Key Principles'},
                            {'id': 3, 'text': 'Best Practices'},
                            {'id': 4, 'text': 'Common Challenges'}
                        ],
                        'matches': [
                            {'id': 'a', 'text': 'Core understanding of the subject matter'},
                            {'id': 'b', 'text': 'Fundamental rules and guidelines'},
                            {'id': 'c', 'text': 'Recommended approaches'},
                            {'id': 'd', 'text': 'Typical obstacles and solutions'}
                        ],
                        'correct_matches': {'1': 'a', '2': 'b', '3': 'c', '4': 'd'}
                    },
                    {
                        'title': 'Practical Exercise',
                        'type': 'simulation',
                        'scenario': f'Apply {learning_objective} in a real-world situation',
                        'steps': [
                            {
                                'order': 1,
                                'action': 'Identify the problem',
                                'hints': ['Consider the context', 'Review requirements']
                            },
                            {
                                'order': 2,
                                'action': 'Plan your approach',
                                'hints': ['Break down into steps', 'Consider alternatives']
                            },
                            {
                                'order': 3,
                                'action': 'Implement solution',
                                'hints': ['Follow best practices', 'Test as you go']
                            }
                        ]
                    },
                    {
                        'title': 'Knowledge Check',
                        'type': 'drag_and_drop',
                        'elements': [
                            {'id': 1, 'text': 'First step', 'correct_position': 1},
                            {'id': 2, 'text': 'Second step', 'correct_position': 2},
                            {'id': 3, 'text': 'Third step', 'correct_position': 3},
                            {'id': 4, 'text': 'Final step', 'correct_position': 4}
                        ],
                        'feedback': {
                            'success': 'Great job! You've mastered the sequence.',
                            'partial': 'Almost there! Review the order once more.',
                            'failure': 'Review the process and try again.'
                        }
                    }
                ],
                'progress_tracking': {
                    'minimum_score': 70,
                    'attempts_allowed': 3,
                    'time_limit': 45  # minutes
                },
                'completion_criteria': {
                    'all_stages_completed': True,
                    'minimum_accuracy': 80,
                    'minimum_time_spent': 15  # minutes
                }
            }

class AITaskGenerator:
    """Service to generate tasks using external AI services"""
    
    @staticmethod
    def generate_tasks(learning_objective, difficulty, student_grade):
        """
        Generate tasks using an AI service
        
        In a real implementation, this would call an external AI API
        """
        # This is where you would implement the call to an AI service
        # For now, return a placeholder implementation
        
        # Example structure for an AI service call:
        """
        response = requests.post(
            settings.AI_SERVICE_URL,
            json={
                'learning_objective': learning_objective,
                'difficulty': difficulty,
                'student_grade': student_grade
            },
            headers={
                'Authorization': f'Bearer {settings.AI_SERVICE_API_KEY}'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to generate tasks")
        """
        
        # Placeholder implementation
        task_types = ['quiz', 'assignment', 'interactive', 'challenge']
        tasks = []
        
        for task_type in task_types:
            task = {
                'title': f"{task_type.capitalize()} on {learning_objective}",
                'task_type': task_type,
                'learning_objective': learning_objective,
                'difficulty': difficulty,
                'content': {}
            }
            
            # Generate content based on task type
            if task_type == 'quiz':
                task['content'] = {
                    'questions': [
                        {
                            'question': f"Question 1 about {learning_objective}",
                            'options': ["Option A", "Option B", "Option C", "Option D"],
                            'correct_answer': 0
                        },
                        {
                            'question': f"Question 2 about {learning_objective}",
                            'options': ["Option A", "Option B", "Option C", "Option D"],
                            'correct_answer': 1
                        }
                    ]
                }
            elif task_type == 'assignment':
                task['content'] = {
                    'instructions': f"Complete this assignment about {learning_objective}",
                    'questions': [
                        {
                            'question': f"Essay question about {learning_objective}",
                            'type': 'essay'
                        }
                    ]
                }
            elif task_type == 'interactive':
                task['content'] = {
                    'activity_type': 'matching',
                    'items': [
                        {'id': 1, 'text': f"Term 1 for {learning_objective}"},
                        {'id': 2, 'text': f"Term 2 for {learning_objective}"}
                    ],
                    'matches': [
                        {'id': 'a', 'text': f"Definition 1 for {learning_objective}"},
                        {'id': 'b', 'text': f"Definition 2 for {learning_objective}"}
                    ],
                    'correct_matches': {'1': 'a', '2': 'b'}
                }
            else:  # challenge
                task['content'] = {
                    'instructions': f"Solve this challenge about {learning_objective}",
                    'problem': f"A challenging problem related to {learning_objective}",
                    'hints': ["Hint 1", "Hint 2"],
                    'solution': f"Solution explanation for {learning_objective} challenge"
                }
            
            tasks.append(task)
        
        return tasks

class LLMTaskGenerator:
    """Service to generate tasks using LLM based on learning paths"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.api_base = settings.GROQ_API_BASE
        self.model = "deepseek-r1-distill-qwen-32b"
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set in settings or environment")
            
        logger.info(f"Initialized LLMTaskGenerator with API base: {self.api_base}")

    def generate_tasks_from_learning_path(self, learning_path) -> List[Dict]:
        try:
            path_data = learning_path.path_data
            logger.info(f"Processing learning path data: {json.dumps(path_data, indent=2)}")
            
            if not path_data:
                logger.error("Learning path data is empty")
                return self._generate_fallback_tasks()

            tasks = []
            topics = path_data.get('topics', [])
            
            if not topics:
                logger.error("No topics found in learning path data")
                return self._generate_fallback_tasks()

            for topic in topics:
                logger.info(f"Generating tasks for topic: {topic.get('title')}")
                
                # Prepare student context from path_data
                student_info = {
                    'grade_level': path_data.get('student_grade', 'intermediate'),
                    'learning_style': path_data.get('learning_style', 'visual'),
                    'strengths': path_data.get('strengths', []),
                    'areas_for_improvement': path_data.get('weaknesses', [])
                }

                # Generate tasks using both LLM and fallback mechanism
                topic_tasks = self._generate_topic_tasks(topic, student_info)
                if topic_tasks:
                    tasks.extend(topic_tasks)
                else:
                    # If LLM fails, generate fallback tasks for this topic
                    fallback_tasks = self._generate_fallback_topic_tasks(topic)
                    tasks.extend(fallback_tasks)

            if not tasks:
                logger.warning("No tasks generated, using fallback tasks")
                return self._generate_fallback_tasks()

            logger.info(f"Total tasks generated: {len(tasks)}")
            return tasks
        
        except Exception as e:
            logger.error(f"Error in generate_tasks_from_learning_path: {str(e)}")
            return self._generate_fallback_tasks()

    def _generate_topic_tasks(self, topic: Dict, student_info: Dict) -> List[Dict]:
        """Generate tasks for a specific topic using LLM"""
        try:
            prompt = self._create_task_generation_prompt(topic, student_info)
            generated_tasks = self._call_llm_api(prompt)
            
            if not generated_tasks or 'tasks' not in generated_tasks:
                return []

            return [
                self._validate_and_format_task(task_data, topic)
                for task_data in generated_tasks['tasks']
                if self._validate_and_format_task(task_data, topic)
            ]
        except Exception as e:
            logger.error(f"Error generating tasks for topic {topic.get('title')}: {str(e)}")
            return []

    def _generate_fallback_tasks(self) -> List[Dict]:
        """Generate basic tasks when LLM generation fails"""
        logger.info("Generating fallback tasks")
        basic_tasks = []
        
        task_types = ['quiz', 'assignment', 'interactive']
        difficulties = ['easy', 'medium', 'hard']
        
        for task_type in task_types:
            task = {
                'title': f"Basic {task_type.capitalize()} Task",
                'description': f"A basic {task_type} to test your knowledge",
                'task_type': task_type,
                'difficulty': 'medium',
                'estimated_time': '30 minutes',
                'points': 100,
                'content': self._generate_fallback_content(task_type),
                'created_at': timezone.now().isoformat(),
                'due_days': settings.TASK_GENERATION.get('DEFAULT_DUE_DAYS', 7),
                'status': 'active'
            }
            basic_tasks.append(task)
        
        return basic_tasks

    def _generate_fallback_content(self, task_type: str) -> Dict:
        """Generate basic content for fallback tasks"""
        if task_type == 'quiz':
            return {
                'questions': [
                    {
                        'question': 'Sample question 1',
                        'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                        'correct_answer': 0
                    },
                    {
                        'question': 'Sample question 2',
                        'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                        'correct_answer': 1
                    }
                ]
            }
        elif task_type == 'assignment':
            return {
                'instructions': 'Complete this basic assignment',
                'questions': [
                    {
                        'question': 'Write a short essay',
                        'type': 'essay'
                    }
                ]
            }
        else:  # interactive
            return {
                'activity_type': 'matching',
                'items': [
                    {'id': 1, 'text': 'Term 1'},
                    {'id': 2, 'text': 'Term 2'}
                ],
                'matches': [
                    {'id': 'a', 'text': 'Definition 1'},
                    {'id': 'b', 'text': 'Definition 2'}
                ],
                'correct_matches': {'1': 'a', '2': 'b'}
            }

    def _generate_fallback_topic_tasks(self, topic: Dict) -> List[Dict]:
        """Generate basic tasks for a specific topic"""
        tasks = []
        title = topic.get('title', 'Unknown Topic')
        
        task_types = settings.TASK_GENERATION.get('TASK_TYPE_DISTRIBUTION', {}).keys()
        
        for task_type in task_types:
            task = {
                'title': f"{title} - {task_type.capitalize()}",
                'description': f"Practice {title} concepts",
                'task_type': task_type,
                'difficulty': topic.get('difficulty', 'medium'),
                'estimated_time': '30 minutes',
                'points': 100,
                'content': self._generate_topic_specific_content(topic, task_type),
                'topic': title,
                'learning_objective': topic.get('objectives', []),
                'created_at': timezone.now().isoformat(),
                'due_days': settings.TASK_GENERATION.get('DEFAULT_DUE_DAYS', 7),
                'status': 'active'
            }
            tasks.append(task)
        
        return tasks

    def _generate_topic_specific_content(self, topic: Dict, task_type: str) -> Dict:
        """Generate content specific to a topic and task type"""
        title = topic.get('title', 'Unknown Topic')
        objectives = topic.get('objectives', [])
        
        if task_type == 'quiz':
            return {
                'instructions': f'Test your knowledge of {title}',
                'questions': [
                    {
                        'question': f"What is the main concept of {title}?",
                        'type': 'multiple_choice',
                        'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                        'correct_answer': 0
                    }
                ]
            }
        elif task_type == 'assignment':
            return {
                'instructions': f'Apply your knowledge of {title}',
                'questions': [
                    {
                        'question': f"Explain the key principles of {title}",
                        'type': 'essay',
                        'word_limit': 250
                    }
                ]
            }
        else:  # interactive
            return {
                'instructions': f'Practice {title} concepts interactively',
                'activity_type': 'matching',
                'items': [
                    {'id': 1, 'text': f"Key concept 1 from {title}"},
                    {'id': 2, 'text': f"Key concept 2 from {title}"}
                ],
                'matches': [
                    {'id': 'a', 'text': 'Definition 1'},
                    {'id': 'b', 'text': 'Definition 2'}
                ],
                'correct_matches': {'1': 'a', '2': 'b'}
            }

    def _create_task_generation_prompt(self, topic: Dict, student_info: Dict) -> str:
        # Create the response format template separately
        response_format = '''{
            "tasks": [
                {
                    "title": "Clear and specific task title",
                    "description": "Detailed description of what the student needs to do",
                    "task_type": "quiz",
                    "difficulty": "medium",
                    "estimated_time": "30 minutes",
                    "points": 100,
                    "content": {
                        "instructions": "Step-by-step instructions",
                        "questions": [
                            {
                                "question": "Specific question text",
                                "type": "multiple_choice",
                                "options": ["Option A", "Option B", "Option C", "Option D"],
                                "correct_answer": 0
                            }
                        ]
                    }
                }
            ]
        }'''

        # Create the main prompt
        prompt = f"""
        As an educational expert, create 3 personalized learning tasks based on this context:

        TOPIC INFORMATION:
        Title: {topic.get('title')}
        Description: {topic.get('description')}
        Objectives: {', '.join(topic.get('objectives', []))}

        STUDENT PROFILE:
        Grade Level: {student_info.get('grade_level')}
        Learning Style: {student_info.get('learning_style')}
        Strengths: {', '.join(student_info.get('strengths', []))}
        Areas for Improvement: {', '.join(student_info.get('areas_for_improvement', []))}

        REQUIREMENTS:
        - Create exactly 3 tasks
        - Mix of different task types (quiz, assignment, interactive)
        - Appropriate difficulty level
        - Clear instructions
        - Engaging content

        RESPONSE FORMAT:
        {response_format}
        """
        
        logger.info("Generated prompt for task creation")
        return prompt

    def _call_llm_api(self, prompt: str) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert educational task generator. Create engaging, grade-appropriate tasks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }
        
        try:
            logger.info("Making API call to Groq LLM")
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Successfully received response from LLM API")
            
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM API call: {str(e)}")
            raise

    def _validate_and_format_task(self, task_data: Dict, topic: Dict) -> Dict:
        """Validate and format task data"""
        required_fields = ['title', 'task_type', 'difficulty', 'content']
        
        if not all(field in task_data for field in required_fields):
            return None
            
        # Add additional metadata
        task_data.update({
            'topic': topic.get('title'),
            'learning_objective': topic.get('objectives', []),
            'created_at': timezone.now().isoformat(),
            'due_days': 7,  # Default due date in days
            'status': 'active'
        })
        
        return task_data
