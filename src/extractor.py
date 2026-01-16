import langextract as lx
from langextract.core.data import ExampleData, Extraction
from .models import EmailExtraction, ImportanceLevel
from .api_manager import GeminiManager

class EmailExtractor:
    """すべての情報を顧此失彼なく、確実に抽出・可視化する抽出クラス"""
    
    def __init__(self, api_manager: GeminiManager):
        self.api_manager = api_manager
        self.model_id = self.api_manager.model_id
        self.api_key = self.api_manager.api_key

    def _get_examples(self) -> list[ExampleData]:
        """
        全属性が網羅された複数の事例。
        メタデータ(From, To, Received)と本文中のエンティティの両立をデモ。
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
                        extraction_class="email_meta",
                        extraction_text="2026-01-10 10:00:00",
                        attributes={
                            "subject": "[至急] WisE システム不具合",
                            "sender": "support@toyota-tsusho.com",
                            "recipients": ["dev@acrosstudio.co.jp"],
                            "received_at": "2026-01-10 10:00:00",
                            "importance": "重大",
                            "summary": "WisEの不具合に関する至急の修正連絡。"
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
                        extraction_class="email_meta",
                        extraction_text="2026-01-11 09:00:00",
                        attributes={
                            "subject": "会議のご案内",
                            "sender": "saiganji@toyota-tsusho.com",
                            "recipients": ["hochi@acrosstudio.co.jp", "kido@acrosstudio.co.jp"],
                            "received_at": "2026-01-11 09:00:00",
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
        漏れ(recipients, received_at等)を完全に防ぐための厳格な抽出
        """
        examples = self._get_examples()
        
        prompt_description = """
        メールのMarkdownから、全ての情報を1つも漏らさずに抽出してください。
        
        ---抽出項目と役割---
        1. email_meta (属性として抽出):
           - subject: 件名
           - sender: 'From:' から抽出 (例: user@example.com)
           - recipients: 'To:' から全アドレスをリスト抽出 (例: ["a@x.com", "b@x.com"])
           - received_at: 'Received:' から日時を抽出 (例: 2025-11-19 09:12:50)
           - importance: '重大', '通常', '低'
           - summary: 全体の簡潔な要約
           - action_required: 受信者がすべき具体的な行動。**「～いただけますと幸いです」「～をお願いします」といった委婉な依頼も行動として抽出してください。**
        
        2. 各エンティティ (本文中のハイライト用):
           - person: 人物
           - company: 会社
           - project: システム・プロジェクト名
           - keyword: 重要度判定の根拠(至急, 打ち合わせ, 依頼 等)
           - deadline: 期限
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
            elif c == "email_meta":
                if "subject" in a: res["subject"] = a["subject"]
                if "sender" in a: res["sender"] = a["sender"]
                if "recipients" in a: res["recipients"] = a["recipients"]
                if "received_at" in a: res["received_at"] = a["received_at"]
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
