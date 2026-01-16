import os
from dotenv import load_dotenv
from google import genai

class GeminiManager:
    """Gemini Flash API クライアントと設定の管理"""
    
    def __init__(self, api_key: str = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY が見つかりません。.env ファイルに設定するか、直接提供してください。")
        
        # 新しい SDK クライアント
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.0-flash"

    def get_client(self):
        return self.client
