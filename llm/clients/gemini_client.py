"""
Google Gemini API Client

Provides interface to Google Gemini 2.5-flash model for AI analysis.
"""
import os
import sys
import json
import time
from typing import Optional, Dict, Any, List

# Suppress gRPC/ALTS warnings from Google API client
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

import google.generativeai as genai


class GeminiClient:
    """Client for Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google API key. If None, reads from GEMINI_API_KEY env var.
            model_name: Model name to use (default: gemini-2.5-flash)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY env var or pass api_key parameter.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
    def generate(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate response from Gemini.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for model behavior
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        generation_config.update(kwargs)
        
        try:
            # If system instruction provided, create model with it
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise
    
    def generate_with_images(
        self,
        prompt: str,
        image_paths: List[str],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response with image inputs.
        
        Args:
            prompt: User prompt
            image_paths: List of local image file paths
            system_instruction: System instruction
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        from PIL import Image
        
        generation_config = {"temperature": temperature}
        generation_config.update(kwargs)
        
        try:
            # Load images
            images = [Image.open(path) for path in image_paths]
            
            # Create content list with prompt and images
            content = [prompt] + images
            
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            response = model.generate_content(
                content,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini API error with images: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Multi-turn chat conversation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: System instruction
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        generation_config = {"temperature": temperature}
        generation_config.update(kwargs)
        
        try:
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            chat = model.start_chat(history=[])
            
            # Add message history
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                chat.history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Send last message
            response = chat.send_message(
                messages[-1]["content"],
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini chat error: {e}")
            raise
