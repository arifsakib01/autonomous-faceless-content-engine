"""
MODULE 1: Script Generation
Generates engaging video scripts with hooks using LLM endpoints.
"""
import json
import logging
from typing import Optional
import requests
from models import ScriptData
from exceptions import ScriptGenerationError
from config import LLM_ENDPOINT, LLM_MODEL, SCRIPT_WORD_COUNT, HOOK_DURATION, SCRIPT_TEMPERATURE, OPENAI_API_KEY, MAX_RETRIES, RETRY_DELAY
import time


logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates video scripts using LLM APIs."""
    
    def __init__(self, api_key: str = OPENAI_API_KEY, endpoint: str = LLM_ENDPOINT):
        """
        Initialize the script generator.
        
        Args:
            api_key: API key for LLM service (OpenAI, etc.)
            endpoint: LLM API endpoint URL
            
        Raises:
            ScriptGenerationError: If API key is missing
        """
        if not api_key:
            raise ScriptGenerationError("LLM API key not provided in environment or config")
        
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = LLM_MODEL
        logger.info(f"ScriptGenerator initialized with model: {self.model}")
    
    def generate(self, topic: str, additional_context: Optional[str] = None) -> ScriptData:
        """
        Generate a video script for a given topic.
        
        Args:
            topic: The main topic for the video
            additional_context: Optional additional context or requirements
        
        Returns:
            ScriptData object containing title, description, script, keywords, and hook
        
        Raises:
            ScriptGenerationError: If script generation fails
        """
        try:
            logger.info(f"Generating script for topic: {topic}")
            
            # Construct prompt
            prompt = self._build_prompt(topic, additional_context)
            
            # Call LLM with retries
            response_text = self._call_llm_with_retry(prompt)
            
            # Parse response
            script_data = self._parse_response(response_text, topic)
            
            logger.info(f"Script generated successfully: {script_data.title}")
            return script_data
            
        except requests.exceptions.RequestException as e:
            raise ScriptGenerationError(f"Network error during script generation: {str(e)}")
        except json.JSONDecodeError as e:
            raise ScriptGenerationError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise ScriptGenerationError(f"Unexpected error in script generation: {str(e)}")
    
    def _build_prompt(self, topic: str, additional_context: Optional[str] = None) -> str:
        """Build the LLM prompt for script generation."""
        base_prompt = f"""Generate a compelling short-form video script for social media (TikTok/YouTube Shorts) about: {topic}

Requirements:
1. Script should be approximately {SCRIPT_WORD_COUNT} words
2. Start with a 3-second hook (approximately 20-30 words) that captures attention immediately
3. Make it engaging, fast-paced, and suitable for vertical video format
4. Include a clear call-to-action at the end
5. Use simple, conversational language

Return ONLY valid JSON (no markdown, no additional text) with this exact structure:
{{
    "title": "Catchy video title under 100 characters",
    "description": "Detailed description for YouTube/social platforms (150-200 chars)",
    "script_text": "Full script text starting with the hook",
    "hook": "First 20-30 words that hook viewers",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""
        
        if additional_context:
            base_prompt += f"\n\nAdditional Context: {additional_context}"
        
        return base_prompt
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = MAX_RETRIES) -> str:
        """
        Call LLM endpoint with exponential backoff retry logic.
        
        Args:
            prompt: The prompt to send to LLM
            max_retries: Maximum number of retry attempts
        
        Returns:
            Response text from LLM
        
        Raises:
            ScriptGenerationError: If all retries fail
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a viral short-form video scriptwriter."},
                {"role": "user", "content": prompt}
            ],
            "temperature": SCRIPT_TEMPERATURE,
            "max_tokens": 1000
        }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"LLM API call attempt {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_json = response.json()
                    return response_json["choices"][0]["message"]["content"]
                
                elif response.status_code == 429:  # Rate limit
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"LLM API error: {last_error}")
                    
                    if attempt < max_retries - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
            
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
        
        raise ScriptGenerationError(f"LLM API failed after {max_retries} retries. Last error: {last_error}")
    
    def _parse_response(self, response_text: str, topic: str) -> ScriptData:
        """
        Parse and validate LLM response.
        
        Args:
            response_text: Raw response from LLM
            topic: Original topic (fallback for title)
        
        Returns:
            Validated ScriptData object
        
        Raises:
            ScriptGenerationError: If response is invalid
        """
        try:
            # Try to extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ScriptGenerationError("No JSON object found in LLM response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["title", "description", "script_text", "keywords"]
            for field in required_fields:
                if field not in data:
                    raise ScriptGenerationError(f"Missing required field: {field}")
            
            # Ensure keywords is a list
            if isinstance(data["keywords"], str):
                data["keywords"] = [k.strip() for k in data["keywords"].split(",")]
            
            # Create and validate ScriptData
            script_data = ScriptData(
                title=data["title"][:100],  # Limit title length
                description=data["description"][:200],
                script_text=data["script_text"],
                keywords=data["keywords"][:5],  # Limit to 5 keywords
                hook=data.get("hook", data["script_text"][:100])
            )
            
            logger.debug(f"Script data parsed successfully: {len(script_data.script_text)} chars")
            return script_data
            
        except json.JSONDecodeError as e:
            raise ScriptGenerationError(f"Invalid JSON in LLM response: {str(e)}")
        except Exception as e:
            raise ScriptGenerationError(f"Failed to parse script data: {str(e)}")


# Standalone function for convenience
def generate_script(topic: str, context: Optional[str] = None) -> ScriptData:
    """
    Convenience function to generate a script.
    
    Args:
        topic: Video topic
        context: Optional additional context
    
    Returns:
        ScriptData object
    
    Raises:
        ScriptGenerationError: If generation fails
    """
    generator = ScriptGenerator()
    return generator.generate(topic, context)
