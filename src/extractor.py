import langextract as lx
from langextract.core.data import ExampleData, Extraction
from .models import EmailExtraction, ImportanceLevel
from .api_manager import GeminiManager

class EmailExtractor:
    """ヘッダー情報と分析結果を明確に分離して抽出するクラス"""
    
    def __init__(self, api_manager: GeminiManager):
        self.api_manager = api_manager
        self.model_id = self.api_manager.model_id
        self.api_key = self.api_manager.api_key

    def _get_examples(self) -> list[ExampleData]:
        """
        ヘッダー(Metadata)と、本文の分析(Analysis)を分離した例示データ
        """
        text_1 = """# [至急] WisE システム不具合
**To:** dev@acrosstudio.co.jp
**From:** support@toyota-tsusho.com
**Received:** 2026-01-10 10:00:00

佐藤 様、
WisE で 不具合 が発生。 至急 修正 を。 期限 は 明日 です。"""

        text_2 = """# 会議のご案内
**To:** hochi@acrosstudio.co.jp; kido@acrosstudio.co.jp
**From:** saiganji@toyota-tsusho.com
**Received:** 2026-01-11 09:00:00

保知 様、 西願寺 です。
来週 トヨタ通商 にて 打ち合わせ を行います。 ご 同席 ください。"""

        return [
            ExampleData(
                text=text_1,
                extractions=[
                    Extraction(extraction_class="person", extraction_text="佐藤"),
                    Extraction(extraction_class="project", extraction_text="WisE"),
                    Extraction(extraction_class="keyword", extraction_text="至急"),
                    Extraction(extraction_class="keyword", extraction_text="不具合"),
                    Extraction(extraction_class="deadline", extraction_text="明日"),
                    Extraction(
                        extraction_class="header_info",
                        extraction_text="2026-01-10 10:00:00",
                        attributes={
                            "subject": "[至急] WisE システム不具合",
                            "sender": "support@toyota-tsusho.com",
                            "recipients": ["dev@acrosstudio.co.jp"],
                            "received_at": "2026-01-10 10:00:00"
                        }
                    ),
                    Extraction(
                        extraction_class="analysis_result",
                        extraction_text="至急 修正 を。",
                        attributes={
                            "importance": "重大",
                            "summary": "WisEの不具合に関する至急の修正連絡。",
                            "action_required": "不具合の修正対応"
                        }
                    )
                ]
            ),
            ExampleData(
                text=text_2,
                extractions=[
                    Extraction(extraction_class="person", extraction_text="保知"),
                    Extraction(extraction_class="person", extraction_text="西願寺"),
                    Extraction(extraction_class="company", extraction_text="トヨタ通商"),
                    Extraction(extraction_class="keyword", extraction_text="打ち合わせ"),
                    Extraction(extraction_class="keyword", extraction_text="同席"),
                    Extraction(
                        extraction_class="header_info",
                        extraction_text="2026-01-11 09:00:00",
                        attributes={
                            "subject": "会議のご案内",
                            "sender": "saiganji@toyota-tsusho.com",
                            "recipients": ["hochi@acrosstudio.co.jp", "kido@acrosstudio.co.jp"],
                            "received_at": "2026-01-11 09:00:00"
                        }
                    ),
                    Extraction(
                        extraction_class="analysis_result",
                        extraction_text="ご 同席 ください。",
                        attributes={
                            "importance": "通常",
                            "summary": "来週の打ち合わせ案内と同席依頼。",
                            "action_required": "打ち合わせへの同席"
                        }
                    )
                ]
            )
        ]

    def extract(self, markdown_text: str) -> tuple[EmailExtraction, lx.data.AnnotatedDocument]:
        """
        Metadata(header_info) と分析結果(analysis_result) を分離して抽出
        """
        examples = self._get_examples()
        
        prompt_description = """
        メールのMarkdownから情報を抽出してください。
        
        ---1. ヘッダー情報 (header_info クラス)---
        メールの形式的な情報を属性として抽出してください。
        - subject: 件名
        - sender: 送信者 (From)
        - recipients: 受信者リスト (To)
        - received_at: 受信日時 (Received)
        
        ---2. 分析結果 (analysis_result クラス)---
        本文の内容を解釈した結果を属性として抽出してください。
        - importance: '重大', '通常', '低'
        - summary: 本文の要約（日本語）
        - action_required: 具体的な行動指示（委婉な依頼も含む）
        
        ---3. 個別エンティティ (本文中のハイライト用)---
        - person: 人物名
        - company: 会社名
        - project: プロジェクト・システム名
        - keyword: 判断根拠となったキーワード
        - deadline: 期限・日時
        """

        annotated_doc = lx.extract(
            text_or_documents=markdown_text,
            examples=examples,
            prompt_description=prompt_description,
            model_id=self.model_id,
            api_key=self.api_key,
            show_progress=False
        )
        
        res = {
            "subject": "件名なし", "sender": "不明", "recipients": [], "received_at": None,
            "importance": "通常", "summary": "", "action_required": None, "deadline": None,
            "people": [], "companies": [], "projects": [], "keywords": []
        }

        for ext in annotated_doc.extractions:
            c = ext.extraction_class
            t = ext.extraction_text
            a = ext.attributes or {}

            if c == "person": res["people"].append(t)
            elif c == "company": res["companies"].append(t)
            elif c == "project": res["projects"].append(t)
            elif c == "keyword": res["keywords"].append(t)
            elif c == "deadline": res["deadline"] = t
            elif c == "header_info":
                if "subject" in a: res["subject"] = a["subject"]
                if "sender" in a: res["sender"] = a["sender"]
                if "recipients" in a: res["recipients"] = a["recipients"]
                if "received_at" in a: res["received_at"] = a["received_at"]
            elif c == "analysis_result":
                if "importance" in a: res["importance"] = a["importance"]
                if "summary" in a: res["summary"] = a["summary"]
                if "action_required" in a: res["action_required"] = a["action_required"]

        return EmailExtraction(
            subject=res["subject"],
            sender=res["sender"],
            recipients=res["recipients"] if isinstance(res["recipients"], list) else [res["recipients"]],
            received_at=res["received_at"],
            importance=ImportanceLevel(res["importance"]),
            keywords_detected=list(set(res["keywords"])),
            summary=res["summary"],
            action_required=res["action_required"],
            deadline=res["deadline"],
            mentioned_people=list(set(res["people"])),
            mentioned_companies=list(set(res["companies"])),
            mentioned_projects=list(set(res["projects"]))
        ), annotated_doc
