import time
import logging
# Get a logger for this module
logger = logging.getLogger(__name__)
import os
# Set environment variables for this process
os.environ['GOOGLE_CLOUD_PROJECT'] = # Enter your project name
os.environ['GOOGLE_CLOUD_LOCATION'] = # Enter your VM location
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'
from google import genai
import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel
import random

class VertexAI:
    
    def __init__(self, project_id, location):
        # Initialize GCP VM instance with service account that could access Vertex AI and "Allow full access to all cloud APIs" 
        import vertexai
        from vertexai.generative_models import (
            GenerativeModel,
            Tool,
            grounding
        )
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash-001")
        self.leader_model = GenerativeModel("gemini-2.5-flash-preview-04-17")

    def generate(self, prompt, low_temp=0.05, top_P=0.95, top_K=20):
        # Generate completion with backoff for API waiting.
        max_retries = 6
        retries = 0
        while retries < max_retries:
            try:
                response = self.model.generate_content(prompt, generation_config={"temperature":low_temp})
                return response.text
            except Exception as e:
                retries += 1
                wait_time = (2 ** retries) + 1 # Exponential backoff
                logger.info(f"Exception: {e}")
                logger.info(f"Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
        logger.error("Max retries exceeded. API call failed.")

    def leader_generate(self, prompt, low_temp=0.05):
        # Generate completion with backoff for API waiting.
        max_retries = 6
        retries  = 0
        while retries < max_retries:
            try:
                response = self.leader_model.generate_content(prompt, generation_config={"temperature":low_temp})
                return response.text
            except Exception as e:
                retries += 1
                wait_time = (2 ** retries) + 1 # Exponential backoff
                logger.info(f"Exception: {e}")
                logger.info(f"Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
        logger.error("Max retries exceeded. API call failed.")
