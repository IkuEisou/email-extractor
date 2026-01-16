import langextract as lx
from langextract.core.data import ExampleData, Extraction
from .models import EmailExtraction, ImportanceLevel
from .api_manager import GeminiManager

class EmailExtractor:
    """langextract を利用してメールから構造化データを抽出するクラス"""
    
    def __init__(self, api_manager: GeminiManager):
        self.api_manager = api_manager
        self.model_id = self.api_manager.model_id
        self.api_key = self.api_manager.api_key

    def _get_examples(self) -> list[ExampleData]:
        """抽出の精度を高めるための例示データを提供します"""
        return [
            ExampleData(
                text="""# プロジェクト進捗報告
**To:** leader@example.com
**From:** staff@example.com
**Received:** 2026-01-10 15:00:00

お疲れ様です。プロジェクトAの進捗ですが、予定通り進んでいます。
来週月曜日にMTGをお願いします。""",
                extractions=[
                    Extraction(
                        extraction_class="email_info",
                        extraction_text="プロジェクト進捗報告",
                        attributes={
                            "subject": "プロジェクト進捗報告",
                            "sender": "staff@example.com",
                            "recipients": ["leader@example.com"],
                            "importance": "通常",
                            "summary": "プロジェクトAの進捗は順調。来週月曜日にMTGを希望。",
                            "mentioned_companies": [],
                            "mentioned_people": []
                        }
                    )
                ]
            )
        ]

    def extract(self, markdown_text: str) -> EmailExtraction:
        """
        langextract を使用して Markdown からデータを抽出します。
        """
        examples = self._get_examples()
        
        # langextract による抽出実行
        annotated_doc = lx.extract(
            text_or_documents=markdown_text,
            examples=examples,
            model_id=self.model_id,
            api_key=self.api_key,
            show_progress=False
        )
        
        if not annotated_doc.extractions:
            raise ValueError("メールから情報を抽出できませんでした")

        # 抽出された最初のデータ（email_info）を使用
        ext = annotated_doc.extractions[0]
        attrs = ext.attributes or {}

        # 属性値を Pydantic モデルに変換
        # langextract の結果を安全にパース
        return EmailExtraction(
            subject=attrs.get("subject", "件名なし"),
            sender=attrs.get("sender", "不明"),
            recipients=attrs.get("recipients", []),
            received_at=None, # 日時パースは必要に応じて実装
            importance=ImportanceLevel(attrs.get("importance", "通常")),
            keywords_detected=attrs.get("keywords_detected", []),
            summary=attrs.get("summary", ""),
            action_required=attrs.get("action_required"),
            deadline=attrs.get("deadline"),
            mentioned_people=attrs.get("mentioned_people", []),
            mentioned_companies=attrs.get("mentioned_companies", [])
        )
