import pytest
from src.extractor import EmailExtractor
from src.api_manager import GeminiManager
from src.models import EmailExtraction, ImportanceLevel

@pytest.fixture
def extractor():
    manager = GeminiManager()
    return EmailExtractor(manager)

def test_extraction_basic(extractor):
    # サンプルの Markdown 形式メール
    sample_email = """
    # マイクロソフトワークショップ準備打ち合わせ
    **To:** hochi@acrosstudio.co.jp
    **From:** yoshihiko_saiganji@toyota-tsusho.com
    **Received:** 2025-11-19 09:12:50
    
    ---
    お世話になっております。
    掲題の件、12/24のワークショップ準備としてMS社と打ち合わせすることになりました。
    """
    
    result, _ = extractor.extract(sample_email)
    
    # 検証
    assert isinstance(result, EmailExtraction)
    assert result.sender == "yoshihiko_saiganji@toyota-tsusho.com"
    assert "マイクロソフト" in result.subject or "MS" in result.subject or "ワークショップ" in result.subject
    assert result.importance in [ImportanceLevel.CRITICAL, ImportanceLevel.NORMAL, ImportanceLevel.LOW]
    print(f"\n抽出された JSON: {result.model_dump_json(indent=2)}")

if __name__ == "__main__":
    # 手動テスト用
    try:
        mgr = GeminiManager()
        ext = EmailExtractor(mgr)
        test_email = """
        # 重要：契約内容の最終確認
        **From:** legal@example.com
        **Received:** 2026-01-16 10:00:00
        
        緊急の契約案件について、至急ご確認をお願いします。
        """
        print(ext.extract(test_email).model_dump_json(indent=2))
    except Exception as ex:
        print(f"テスト失敗: {ex}")
