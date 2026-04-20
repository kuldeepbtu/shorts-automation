import sys
import os
sys.path.append(r"c:\ShortsBot")

from dotenv import load_dotenv
load_dotenv(r"c:\ShortsBot\.env")

try:
    from pipeline import gemini
    
    print("Testing the fixed gemini() function through the pipeline...")
    result = gemini("Say 'Pipeline is fully fixed' in exactly 4 words.", max_retries=3)
    
    print(f"\nSUCCESS! Received response:\n{result}")
except Exception as e:
    print(f"\nFAILED: {e}")
