# English Companion NX - Feature Implementation Guide

## Project Overview
Enhance the existing English Companion NX voice assistant (Phase 2B complete) to become an intelligent language learning system that helps users achieve C1-level English fluency through targeted practice, real-time feedback, and adaptive training.

## Current System Architecture
```
Wake word → Start session → VAD recording → Whisper STT → Ollama LLM → Coqui TTS → Audio output
```
- **Hardware**: NVIDIA Jetson Orin NX 16GB
- **Current Memory**: 9.8 GB / 15.6 GB (64.9%)
- **Stack**: Python, Ollama (llama3.2:3b), Whisper (small), Coqui TTS
- **Performance**: ~12-15s response time

## Core Learning Objectives
- Eliminate filler words ("um", "uh", "like")
- Master register switching (formal ↔ informal)
- Build confidence through synonym alternatives
- Achieve natural expression with phrasal verbs and idioms
- Develop circumlocution skills (never get stuck)
- Perfect collocations and natural word combinations

## Feature Implementation Roadmap

### Phase 1: Foundation Enhancement (Week 1-2)

#### 1.1 Enhanced Conversation Manager
```python
class EnhancedConversationManager:
    """Wraps existing LLM with training capabilities"""
    
    def __init__(self):
        self.training_mode = "adaptive"  # adaptive, focused, casual
        self.session_goals = []
        self.confidence_tracker = ConfidenceTracker()
        
    def process_conversation(self, user_text):
        # Analyze user speech for training opportunities
        analysis = self.analyze_speech_patterns(user_text)
        
        # Enhance LLM prompt based on training goals
        enhanced_prompt = self.build_training_prompt(user_text, analysis)
        
        # Get LLM response
        response = ollama.generate(enhanced_prompt)
        
        # Post-process to inject training elements
        final_response = self.inject_training_elements(response, analysis)
        
        return final_response
```

#### 1.2 Vocabulary Database Schema
```sql
-- Core vocabulary tracking
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    part_of_speech TEXT,
    difficulty_level INTEGER, -- 1-5 (A1-C2)
    frequency_rank INTEGER,
    first_encountered DATE,
    times_seen INTEGER DEFAULT 0,
    times_used_correctly INTEGER DEFAULT 0,
    confidence_score REAL DEFAULT 0.0,
    notes TEXT
);

-- Synonyms with context
CREATE TABLE synonyms (
    word_id INTEGER,
    synonym_word_id INTEGER,
    context TEXT, -- 'formal', 'informal', 'business'
    strength REAL, -- similarity score 0-1
    FOREIGN KEY (word_id) REFERENCES vocabulary(id)
);

-- Collocations
CREATE TABLE collocations (
    id INTEGER PRIMARY KEY,
    word_id INTEGER,
    pattern TEXT, -- "make + [decision]"
    example TEXT,
    frequency TEXT, -- 'very common', 'common', 'rare'
    FOREIGN KEY (word_id) REFERENCES vocabulary(id)
);

-- Phrasal verb equivalents
CREATE TABLE phrasal_equivalents (
    formal_word_id INTEGER,
    phrasal_verb TEXT,
    context TEXT,
    example_formal TEXT,
    example_phrasal TEXT,
    FOREIGN KEY (formal_word_id) REFERENCES vocabulary(id)
);

-- User progress tracking
CREATE TABLE user_progress (
    word_id INTEGER,
    date DATE,
    event_type TEXT, -- 'seen', 'used', 'corrected', 'mastered'
    conversation_context TEXT,
    confidence_delta REAL,
    FOREIGN KEY (word_id) REFERENCES vocabulary(id)
);
```

### Phase 2: Core Survival Toolkit (Week 2-3)

#### 2.1 Synonym Suggestion Engine
```python
class SynonymEngine:
    """Never get stuck on a missing word"""
    
    def __init__(self, db_path='vocabulary.db'):
        self.db = sqlite3.connect(db_path)
        self.load_synonyms()
    
    def real_time_help(self, description):
        """When user says 'what's the word for...'"""
        # Pattern match the description
        # Query synonym database
        # Return alternatives with difficulty levels
        
    def contextual_alternatives(self, word, context):
        """Provide register-appropriate synonyms"""
        query = """
            SELECT v2.word, s.context, s.strength
            FROM vocabulary v1
            JOIN synonyms s ON v1.id = s.word_id
            JOIN vocabulary v2 ON s.synonym_word_id = v2.id
            WHERE v1.word = ? AND s.context = ?
            ORDER BY s.strength DESC
        """
        return self.db.execute(query, (word, context))
    
    def progressive_difficulty(self, word):
        """Return synonyms at different levels"""
        return {
            'basic': self.get_synonyms(word, max_difficulty=2),
            'intermediate': self.get_synonyms(word, max_difficulty=3),
            'advanced': self.get_synonyms(word, max_difficulty=5)
        }
```

#### 2.2 Filler Word Detection System
```python
class FillerDetector:
    """Eliminate ums and uhs"""
    
    FILLER_PATTERNS = ["um", "uh", "you know", "like", "basically", "actually"]
    
    def __init__(self):
        self.filler_count = defaultdict(int)
        self.alternatives = {
            "um": "pause silently instead",
            "you know": "as you're aware",
            "like": "approximately / for instance",
            "basically": "essentially / fundamentally"
        }
    
    def detect_in_realtime(self, audio_segment):
        """Interrupt with gentle beep on filler detection"""
        if self.contains_filler(audio_segment):
            return {
                'action': 'gentle_beep',
                'feedback': 'filler_detected',
                'alternative': self.get_alternative()
            }
    
    def session_feedback(self):
        """End-of-session filler report"""
        return {
            'total_fillers': sum(self.filler_count.values()),
            'filler_rate': self.calculate_rate(),
            'most_common': self.get_most_common(),
            'improvement': self.compare_to_baseline()
        }
```

#### 2.3 Phrasal Verb Trainer
```python
class PhrasalVerbGym:
    """Master natural English expressions"""
    
    def __init__(self):
        self.verb_patterns = self.load_phrasal_patterns()
        self.formal_to_phrasal = self.load_mappings()
        
    def daily_workout(self, day_of_week):
        """Structured practice by verb family"""
        workouts = {
            'Monday': 'work + particles',  # work out, work on
            'Tuesday': 'get + particles',   # get by, get over
            'Wednesday': 'put + particles'  # put off, put up with
        }
        return self.generate_exercises(workouts[day_of_week])
    
    def natural_replacement(self, formal_phrase):
        """Convert formal to natural phrasal verb"""
        # "postpone the meeting" → "put off the meeting"
        # "investigate this" → "look into this"
        return self.formal_to_phrasal.get(formal_phrase)
    
    def contextual_practice(self, context):
        """Generate context-appropriate exercises"""
        if context == 'business':
            return self.business_phrasals()
        elif context == 'casual':
            return self.casual_phrasals()
```

### Phase 3: Multi-Agent System (Week 3-4)

#### 3.1 Agent Architecture
```python
class ConversationObserver(ABC):
    """Base class for all observer agents"""
    
    @abstractmethod
    def observe(self, user_text, context):
        """Analyze conversation and return actions if needed"""
        pass
    
    @abstractmethod
    def priority(self):
        """Return priority level (1-5)"""
        pass

class AgentOrchestrator:
    """Manages multiple observing agents"""
    
    def __init__(self):
        self.agents = []
        self.action_queue = PriorityQueue()
        self.db = VocabularyDatabase()
        
    def register_agent(self, agent):
        """Add new agent to observation team"""
        self.agents.append(agent)
    
    def process_conversation(self, user_text, context):
        """All agents observe, actions queued by priority"""
        
        # Collect observations from all agents
        for agent in self.agents:
            action = agent.observe(user_text, context)
            if action:
                self.action_queue.put((action.priority, action))
        
        # Execute highest priority action
        if not self.action_queue.empty():
            priority, action = self.action_queue.get()
            return self.execute_action(action)
        
        return None
    
    def execute_action(self, action):
        """Execute training intervention"""
        if action.type == 'immediate_feedback':
            return self.provide_immediate_feedback(action)
        elif action.type == 'queue_for_later':
            self.session_end_queue.append(action)
        elif action.type == 'trigger_exercise':
            return self.start_exercise(action.exercise_type)
```

#### 3.2 Specialized Agents
```python
class FillerWordAgent(ConversationObserver):
    """Monitors and reduces filler usage"""
    
    def observe(self, user_text, context):
        filler_count = self.count_fillers(user_text)
        if filler_count > 0:
            return Action(
                type='filler_feedback',
                priority=3,
                data={'count': filler_count, 'text': user_text}
            )

class ConfidenceAgent(ConversationObserver):
    """Detects low confidence and provides support"""
    
    def observe(self, user_text, context):
        hesitation_markers = ['um', 'uh', '...', 'how do you say']
        confidence_score = self.calculate_confidence(user_text)
        
        if confidence_score < 0.5:
            return Action(
                type='confidence_support',
                priority=4,
                intervention='scaffold_support'
            )

class GrammarAgent(ConversationObserver):
    """Tracks grammatical patterns and errors"""
    
    def observe(self, user_text, context):
        errors = self.detect_errors(user_text)
        if errors:
            return Action(
                type='grammar_feedback',
                priority=2,
                errors=errors,
                timing='end_of_session'  # Don't interrupt flow
            )

class VocabularyTrackerAgent(ConversationObserver):
    """Tracks vocabulary usage and suggests alternatives"""
    
    def observe(self, user_text, context):
        words_used = self.extract_words(user_text)
        
        for word in words_used:
            # Update database
            self.db.update_word_usage(word)
            
            # Check for phrasal alternatives
            if self.has_phrasal_alternative(word):
                return Action(
                    type='phrasal_suggestion',
                    priority=1,
                    suggestion=self.get_phrasal_form(word)
                )
```

### Phase 4: Adaptive Training System (Week 4-5)

#### 4.1 Daily Workout System
```python
class DailyWorkout:
    """Adaptive daily training sessions"""
    
    def __init__(self, user_profile):
        self.user = user_profile
        self.workout_history = []
        
    def generate_daily_session(self):
        """Create personalized daily workout"""
        
        # Check user energy level
        energy = self.assess_energy_level()
        
        # Select appropriate challenges
        if energy == 'high':
            return self.challenging_workout()
        elif energy == 'medium':
            return self.balanced_workout()
        else:
            return self.light_workout()
    
    def light_workout(self):
        """Low-pressure practice for tired days"""
        return {
            'warm_up': SimpleConversation(2),  # 2 minutes
            'main': DescriptionPractice(5),    # 5 minutes
            'cool_down': None,
            'corrections': False,  # No corrections on tired days
            'encouragement': True
        }
    
    def balanced_workout(self):
        """Standard practice session"""
        return {
            'warm_up': ConversationStarter(3),
            'main': MixedPractice(10),
            'cool_down': QuickReview(2),
            'corrections': 'gentle',
            'challenges': ['phrasal_verbs', 'synonyms']
        }
    
    def challenging_workout(self):
        """Push boundaries when feeling strong"""
        return {
            'warm_up': RapidFireQuestions(3),
            'main': RegisterSwitching(10),
            'advanced': DebateMode(5),
            'corrections': 'full',
            'challenges': ['complex_syntax', 'idioms', 'formal_register']
        }
```

#### 4.2 LLM as Intelligent Agent
```python
class LLMAgent:
    """LLM that actively orchestrates learning"""
    
    def __init__(self, model='llama3.2:3b'):
        self.model = model
        self.db = VocabularyDatabase()
        
    def analyze_and_decide(self, user_text):
        """LLM analyzes conversation and triggers actions"""
        
        analysis_prompt = f"""
        Analyze this user speech: "{user_text}"
        
        Respond with JSON:
        {{
            "confidence_level": "low|medium|high",
            "detected_errors": [],
            "missed_opportunities": [],
            "suggested_intervention": "none|synonym_help|phrasal_practice",
            "retrieve_from_history": null | "word_to_retrieve"
        }}
        """
        
        decision = ollama.generate(
            model=self.model,
            prompt=analysis_prompt,
            format='json'
        )
        
        return self.execute_decision(json.loads(decision))
    
    def execute_decision(self, decision):
        """Act on LLM's analysis"""
        
        if decision['retrieve_from_history']:
            # Get previous learning context
            history = self.db.get_word_history(decision['retrieve_from_history'])
            
        if decision['suggested_intervention']:
            # Trigger appropriate training module
            return self.trigger_intervention(decision['suggested_intervention'])
        
        return None
```

#### 4.3 Progress Tracking
```python
class ProgressTracker:
    """Monitor improvement over time"""
    
    def __init__(self):
        self.metrics = {
            'filler_rate': [],
            'vocabulary_diversity': [],
            'phrasal_verb_usage': [],
            'confidence_scores': [],
            'grammar_accuracy': []
        }
    
    def calculate_c1_readiness(self):
        """Assess progress toward C1 level"""
        indicators = {
            'filler_rate': self.average_filler_rate() < 0.5,
            'speech_rate': 150 <= self.words_per_minute() <= 180,
            'syntactic_variety': self.unique_structures() > 8,
            'register_accuracy': self.register_accuracy() > 0.9,
            'collocation_errors': self.collocation_errors() < 2
        }
        
        readiness_score = sum(indicators.values()) / len(indicators)
        return {
            'score': readiness_score,
            'details': indicators,
            'recommendations': self.get_improvement_areas(indicators)
        }
    
    def generate_report(self):
        """Weekly progress report"""
        return {
            'sessions_completed': self.session_count,
            'total_speaking_time': self.total_minutes,
            'new_vocabulary': self.new_words_learned,
            'phrasal_verbs_mastered': self.phrasal_verb_count,
            'filler_reduction': f"{self.filler_improvement}%",
            'confidence_trend': self.confidence_graph,
            'next_week_focus': self.recommend_focus_areas()
        }
```

## Implementation Priorities

### Must Have (Core Features)
1. **Synonym Engine** - Never get stuck
2. **Filler Detection** - Clean up speech
3. **Phrasal Verb Training** - Sound natural
4. **Vocabulary Database** - Track progress

### Should Have (Enhancement)
5. **Multi-Agent System** - Intelligent observation
6. **Confidence Support** - Adaptive difficulty
7. **Progress Tracking** - Measure improvement
8. **Daily Workouts** - Consistent practice

### Nice to Have (Advanced)
9. **Register Switching** - Formal/informal mastery
10. **Idiom Integration** - Native-like expression
11. **Collocation Patterns** - Natural combinations
12. **Circumlocution Skills** - Advanced fluency

## Technical Integration Points

### Minimal Changes to Existing System
```python
# In voice_assistant.py, modify conversation loop:

def conversation_loop(self):
    # Existing code...
    user_text = self.transcribe(audio)
    
    # NEW: Pre-processing
    training_context = self.training_manager.analyze(user_text)
    
    # NEW: Enhanced prompt
    enhanced_prompt = self.training_manager.enhance_prompt(
        user_text, 
        training_context
    )
    
    # Existing LLM call with enhanced prompt
    response = self.llm_client.generate(enhanced_prompt)
    
    # NEW: Post-processing
    final_response = self.training_manager.post_process(
        response, 
        training_context
    )
    
    # Existing TTS
    self.tts.speak(final_response)
    
    # NEW: Update progress
    self.training_manager.update_progress(user_text, response)
```

### Configuration
```env
# Training features
TRAINING_MODE=adaptive  # off, gentle, adaptive, intensive
FOCUS_AREA=phrasal_verbs  # vocabulary, grammar, fluency
CORRECTION_STYLE=gentle  # none, gentle, immediate, strict
DATABASE_PATH=~/companion-data/vocabulary.db

# Agent settings
ENABLE_FILLER_DETECTION=true
ENABLE_GRAMMAR_CHECKING=false  # Can be overwhelming
ENABLE_VOCABULARY_TRACKING=true
ENABLE_CONFIDENCE_SUPPORT=true
```

## Success Metrics
- Filler words reduced by 80% in 4 weeks
- Phrasal verb usage increased 5x
- Conversation confidence self-rating improved 40%
- Speaking sessions increased to daily habit
- Vocabulary diversity score doubled

## Notes for Implementation
1. Start with single features, test thoroughly
2. Database should be local SQLite for privacy
3. All processing stays on-device (no cloud)
4. Feedback should encourage, not discourage
5. Allow easy mode for tired days
6. Make daily practice as easy as possible to maintain

## Testing Strategy
- Unit tests for each agent
- Integration tests for agent orchestration  
- User testing for feedback timing
- Performance monitoring (memory/CPU)
- A/B testing for intervention strategies
