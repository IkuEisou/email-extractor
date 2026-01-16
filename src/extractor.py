from .models import EmailExtraction
from .api_manager import GeminiManager

class EmailExtractor:
    """Markdown 形式のメールから構造化データを抽出するコアクラス"""
    
    def __init__(self, api_manager: GeminiManager):
        self.api_manager = api_manager
        self.client = self.api_manager.get_client()
        self.model_id = self.api_manager.model_id

    def extract(self, markdown_text: str) -> EmailExtraction:
        """
        Markdown テキストを解析し、Gemini Flash を使用して構造化された JSON データを抽出します。
        """
        prompt = f"""
        ---Role---
        あなたはナレッジ抽出スペシャリストです。提供されたメール（Markdown形式）から構造化情報を抽出するのがあなたのタスクです。

        ---Instructions---
        1. To, From, Received フィールドと本文を解析してください。
        2. 重要度を判定してください：
           - '重大' (CRITICAL): '契約', 'クレーム', '緊急依頼', '重要' などのキーワードが含まれる場合。
           - '通常' (NORMAL): 通常の業務連絡。
           - '低' (LOW): 事務的またはCC共有のみの情報。
        3. 内容を簡潔な日本語で要約してください。
        4. 言及されている人物と会社を特定してください。
        5. 提供されたスキーマに従って、厳密に JSON 形式で出力してください。

        ---Email Content---
        {markdown_text}

        ---Output---
        """
        
        # 新しい SDK は response_schema を介して Pydantic モデルを直接サポートしています
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': EmailExtraction,
            }
        )
        
        if response.parsed:
            return response.parsed
        else:
            raise ValueError("レスポンスを EmailExtraction モデルにパースできませんでした")
