import langextract as lx
from langextract.core.data import ExampleData, Extraction
from .models import EmailExtraction, ImportanceLevel
from .api_manager import GeminiManager

class EmailExtractor:
    """ヘッダー情報と分析結果を明確に分離し、スマートにハイライト範囲を調整するクラス"""
    
    def __init__(self, api_manager: GeminiManager):
        self.api_manager = api_manager
        self.model_id = self.api_manager.model_id
        self.api_key = self.api_manager.api_key

    def _get_examples(self) -> list[ExampleData]:
        """
        アライメント（位置合わせ）の確実性と、データの綺麗さを両立するための例示。
        """
        text_1 = """# [至急]WisEシステム不具合
**To:** dev@acrosstudio.co.jp
**From:** support@toyota-tsusho.com
**Received:** 2026-01-10 10:00:00

佐藤様
WisEで不具合が発生しました。至急、修正をお願いします。期限は明日です。"""

        text_2 = """# 会議のご案内
**To:** hochi@acrosstudio.co.jp
**From:** saiganji@toyota-tsusho.com
**Received:** 2026-01-11 09:00:00

保知様
西願寺です。来週トヨタ通商にて打ち合わせを行います。ご同席ください。"""

        return [
            ExampleData(
                text=text_1,
                extractions=[
                    # 敬称を含めて抽出させることでアライメントを100%成功させる
                    Extraction(extraction_class="person", extraction_text="佐藤様"),
                    Extraction(extraction_class="project", extraction_text="WisE"),
                    Extraction(extraction_class="keyword", extraction_text="至急"),
                    Extraction(extraction_class="keyword", extraction_text="不具合"),
                    Extraction(extraction_class="deadline", extraction_text="明日"),
                    Extraction(
                        extraction_class="header_info",
                        extraction_text="2026-01-10 10:00:00",
                        attributes={
                            "subject": "[至急]WisEシステム不具合",
                            "sender": "support@toyota-tsusho.com",
                            "recipients": ["dev@acrosstudio.co.jp"],
                            "received_at": "2026-01-10 10:00:00"
                        }
                    ),
                    Extraction(
                        extraction_class="analysis_result",
                        extraction_text="至急、修正をお願いします。",
                        attributes={
                            "importance": "重大",
                            "summary": "WisEの不具合に関する修正依頼。",
                            "action_required": "不具合の修正"
                        }
                    )
                ]
            ),
            ExampleData(
                text=text_2,
                extractions=[
                    Extraction(extraction_class="person", extraction_text="保知様"),
                    Extraction(extraction_class="person", extraction_text="西願寺"),
                    Extraction(extraction_class="company", extraction_text="トヨタ通商"),
                    Extraction(extraction_class="keyword", extraction_text="打ち合わせ"),
                    Extraction(extraction_class="keyword", extraction_text="ご同席"),
                    Extraction(
                        extraction_class="header_info",
                        extraction_text="2026-01-11 09:00:00",
                        attributes={
                            "subject": "会議のご案内",
                            "sender": "saiganji@toyota-tsusho.com",
                            "recipients": ["hochi@acrosstudio.co.jp"],
                            "received_at": "2026-01-11 09:00:00"
                        }
                    ),
                    Extraction(
                        extraction_class="analysis_result",
                        extraction_text="ご同席ください。",
                        attributes={
                            "importance": "通常",
                            "summary": "来週の打ち合わせ案内。",
                            "action_required": "打ち合わせへの出席"
                        }
                    )
                ]
            )
        ]

    def extract(self, markdown_text: str) -> tuple[EmailExtraction, lx.data.AnnotatedDocument]:
        examples = self._get_examples()
        
        prompt_description = """
        メールを分析してください。
        
        ---人物抽出の注意---
        - person: 本文に出現する人物名。アライメント確度を上げるため、「様」等の敬称がある場合はそれも含めて抽出してください。
        
        ---その他---
        - company, project, keyword, deadline: 本文中の該当箇所を抽出。
        - header_info, analysis_result: 属性として各情報を抽出。
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

        # 敬称の自動クリーンアップ用
        honorifics = ["様", "先生", "殿", "氏", "君", "さん"]

        for ext in annotated_doc.extractions:
            c = ext.extraction_class
            t = ext.extraction_text
            a = ext.attributes or {}

            if c == "person":
                clean_name = t
                for h in honorifics:
                    if clean_name.endswith(h):
                        clean_name = clean_name[:-len(h)].strip()
                        # HTML高亮の範囲を敬称の手前までに縮小
                        # 注: char_interval.start_pos/end_pos を使用
                        if hasattr(ext, 'char_interval') and ext.char_interval:
                            ext.char_interval.end_pos = ext.char_interval.start_pos + len(clean_name)
                        break
                res["people"].append(clean_name)
            
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
