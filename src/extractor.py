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
                            "keywords_detected": [],
                            "summary": "プロジェクトAの進捗は順調。来週月曜日にMTGを希望。",
                            "action_required": "来週月曜日のMTG実施",
                            "deadline": "2026-01-12",
                            "mentioned_companies": [],
                            "mentioned_people": ["leader"]
                        }
                    )
                ]
            ),
            ExampleData(
                text="""# 【至急】契約修正のお願い
**To:** sales@partner.co.jp
**From:** legal@mycorp.com
**Received:** 2026-01-15 10:00:00

お世話になっております。
添付の契約書に重大な不備が見つかりました。大至急、修正をお願いします。
明日16日の17時までにご返信いただけますでしょうか。宜しくお願いします。""",
                extractions=[
                    Extraction(
                        extraction_class="email_info",
                        extraction_text="【至急】契約修正のお願い",
                        attributes={
                            "subject": "【至急】契約修正のお願い",
                            "sender": "legal@mycorp.com",
                            "recipients": ["sales@partner.co.jp"],
                            "importance": "重大",
                            "keywords_detected": ["至急", "重大な不備", "修正をお願いします"],
                            "summary": "契約書に重大な不備が見つかったため、至急の修正を依頼。期限は明日17時。",
                            "action_required": "契約書の修正と返信",
                            "deadline": "2026-01-16 17:00",
                            "mentioned_companies": ["MyCorp", "Partner.co.jp"],
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
        
        prompt_description = """
        メールのMarkdownテキストから、以下の情報を厳密に抽出してください。
        
        ---抽出のガイドライン---
        1. mentioned_people (言及されている人物):
           - **本文の冒頭、本文中、または末尾の署名に実名が明記されている人物**のみを抽出してください。
           - メールのヘッダーにあるメールアドレスのID（kido, shu など）は、本文中で言及されていない限り含めないでください。
        
        2. mentioned_companies (言及されている会社・組織):
           - 実在する企業名や団体名（例：マイクロソフト、豊田通商、アクロススタジオ）のみを抽出してください。
           - ドメイン名から会社名を推測しても構いません。
        
        3. mentioned_projects (プロジェクト・システム):
           - 'WisE' やプロジェクト名、アプリ名、システム名はこちらに抽出してください。
        
        4. 重要度とキーワード、要約:
           - 依頼内容や期限がわかる表現をキーワードとして抽出してください。
        """

        # langextract による抽出実行
        annotated_doc = lx.extract(
            text_or_documents=markdown_text,
            examples=examples,
            prompt_description=prompt_description,
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
        return EmailExtraction(
            subject=attrs.get("subject", "件名なし"),
            sender=attrs.get("sender", "不明"),
            recipients=attrs.get("recipients", []),
            received_at=None, 
            importance=ImportanceLevel(attrs.get("importance", "通常")),
            keywords_detected=attrs.get("keywords_detected", []),
            summary=attrs.get("summary", ""),
            action_required=attrs.get("action_required"),
            deadline=attrs.get("deadline"),
            mentioned_people=attrs.get("mentioned_people", []),
            mentioned_companies=attrs.get("mentioned_companies", []),
            mentioned_projects=attrs.get("mentioned_projects", [])
        )
