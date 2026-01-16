import os
import langextract as lx
from langextract.core.data import ExampleData, Extraction
from src.models import EmailExtraction, ImportanceLevel

def test_lx():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("API Key missing")
        return

    # One simple example for langextract
    examples = [
        ExampleData(
            text="From: test@example.com\nTo: user@example.com\nSubject: Test\n\nHello, this is a test.",
            extractions=[
                Extraction(
                    extraction_class="email",
                    extraction_text="this is a test",
                    attributes={
                        "subject": "Test",
                        "sender": "test@example.com",
                        "importance": "通常"
                    }
                )
            ]
        )
    ]

    text = """
    # マイクロソフトワークショップ準備打ち合わせ
    **To:** hochi@acrosstudio.co.jp
    **From:** yoshihiko_saiganji@toyota-tsusho.com
    **Received:** 2025-11-19 09:12:50
    """

    try:
        # Using lx.extract
        result = lx.extract(
            text_or_documents=text,
            examples=examples,
            model_id="gemini-2.0-flash",
            api_key=api_key
        )
        print("Success:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_lx()
