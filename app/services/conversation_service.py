import google.generativeai as genai
from app.config import Config
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    """Service for handling conversations with Gemini AI"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-latest')
        else:
            self.model = None
            logger.warning("Gemini API key not configured")
        
        # Store conversation context (in production, use a proper database)
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    def get_conversation_response(self, user_input: str, phone_number: str, language: str = "arabic") -> str:
        """
        Get AI response for user input
        
        Args:
            user_input (str): User's spoken input
            phone_number (str): Unique identifier for conversation session
            language (str): Response language preference
            
        Returns:
            str: AI generated response
        """
        if not self.model:
            return "عذراً، خدمة المحادثة غير متاحة حالياً"
        
        try:
            # Initialize conversation history for new users
            if phone_number not in self.conversation_history:
                self.conversation_history[phone_number] = []
            
            # Build conversation context
            context = self._build_context(language)
            full_prompt = self._build_conversation_prompt(user_input, phone_number, context)
            
            logger.info(f"Sending prompt to Gemini for {phone_number}")
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            ai_response = response.text.strip()
            
            # Store conversation history
            self._update_conversation_history(phone_number, user_input, ai_response)
            
            logger.info(f"Generated response for {phone_number}: {ai_response[:100]}...")
            
            return ai_response
                
        except Exception as e:
            logger.error(f"Error in conversation service: {str(e)}")
            return "عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى"
    
    def _build_context(self, language: str) -> str:
        """Build conversation context and personality"""
        if language.lower() == "arabic":
            return """أنت مساعد ذكي ودود يتحدث العربية الشامية (السورية). 
            يجب أن تكون:
            - مفيد ومتعاون
            - تستخدم اللهجة السورية الطبيعية
            - تجيب بشكل موجز وواضح
            - تظهر الاهتمام والود في المحادثة
            - لا تستخدم كلمات معقدة أو فصحى مفرطة
            
            احرص على أن تكون إجاباتك قصيرة ومناسبة للمحادثة الهاتفية."""
        else:
            return """You are a helpful and friendly AI assistant. 
            You should:
            - Be helpful and cooperative
            - Use natural, conversational language
            - Keep responses concise and clear
            - Show interest and warmth in conversation
            - Keep answers brief and suitable for phone conversations."""
    
    def _build_conversation_prompt(self, user_input: str, phone_number: str, context: str) -> str:
        """Build the complete conversation prompt including context and history"""
        prompt = context + "\n\n"
        
        # Add recent conversation history (last 5 exchanges)
        history = self.conversation_history.get(phone_number, [])
        recent_history = history[-5:] if len(history) > 5 else history
        
        for exchange in recent_history:
            prompt += f"المستخدم: {exchange['user']}\n"
            prompt += f"المساعد: {exchange['assistant']}\n\n"
        
        prompt += f"المستخدم: {user_input}\nالمساعد:"
        
        return prompt
    
    def _update_conversation_history(self, phone_number: str, user_input: str, ai_response: str):
        """Update conversation history for the user"""
        if phone_number not in self.conversation_history:
            self.conversation_history[phone_number] = []
        
        self.conversation_history[phone_number].append({
            "user": user_input,
            "assistant": ai_response
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(self.conversation_history[phone_number]) > 10:
            self.conversation_history[phone_number] = self.conversation_history[phone_number][-10:]
    
    def clear_conversation(self, phone_number: str):
        """Clear conversation history for a user"""
        if phone_number in self.conversation_history:
            del self.conversation_history[phone_number]
    
    def get_welcome_message(self, language: str = "arabic") -> str:
        """Get welcome message for new conversations"""
        if language.lower() == "arabic":
            return "أهلاً وسهلاً! أنا مساعدك الذكي. كيف بدك أساعدك اليوم؟"
        else:
            return "Hello! I'm your AI assistant. How can I help you today?"

# Global instance
conversation_service = ConversationService()
