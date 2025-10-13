"""
Doubao API Client

Provides interface to Doubao model via Volcengine Ark API.
"""
import os
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI


class DoubaoClient:
    """Client for Doubao API via Volcengine Ark."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "doubao-seed-1-6-thinking-250715"):
        """
        Initialize Doubao client.
        
        Args:
            api_key: Volcengine API key. If None, reads from DOUBAO_API_KEY env var.
            model_name: Endpoint ID to use (e.g., 'doubao-seed-1-6-thinking-250715')
                       Note: Use endpoint ID from Volcengine Ark console, not model name
        """
        self.api_key = api_key or os.getenv('DOUBAO_API_KEY')
        if not self.api_key:
            raise ValueError("Doubao API key not provided. Set DOUBAO_API_KEY env var or pass api_key parameter.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        self.model_name = model_name
        
    def generate(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate response from Doubao.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for model behavior
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # 如果是深度推理模型，打印思维链（可选）
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning = response.choices[0].message.reasoning_content
                if reasoning:
                    print(f"[Doubao 思维链] {reasoning[:200]}..." if len(reasoning) > 200 else f"[Doubao 思维链] {reasoning}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Doubao API error: {e}")
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
        
        Note: Doubao API currently does not support image inputs via base64 data URLs.
        This method will raise an exception. Use text-only prompts instead.
        
        Args:
            prompt: User prompt
            image_paths: List of local image file paths
            system_instruction: System instruction
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
            
        Raises:
            NotImplementedError: Doubao does not support image inputs
        """
        raise NotImplementedError("Doubao API does not support image inputs. Please use text-only prompts.")
    
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
        chat_messages = []
        if system_instruction:
            chat_messages.append({"role": "system", "content": system_instruction})
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            chat_messages.append({"role": role, "content": content})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=chat_messages,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Doubao chat error: {e}")
            raise