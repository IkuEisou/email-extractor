from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ImportanceLevel(str, Enum):
    CRITICAL = "重大"
    NORMAL = "通常"
    LOW = "低"

class EmailExtraction(BaseModel):
    """構造化されたメール抽出結果のモデル"""
    subject: str = Field(description="メールの件名")
    sender: str = Field(description="送信者のメールアドレス")
    recipients: List[str] = Field(description="受信者のメールアドレスリスト")
    received_at: Optional[datetime] = Field(description="メールの受信日時")
    
    importance: ImportanceLevel = Field(description="判定されたメールの重要度")
    keywords_detected: List[str] = Field(
        default_factory=list,
        description="重要度判定の根拠となったキーワード（例：'契約', 'クレーム', '緊急'）"
    )
    
    summary: str = Field(description="メール内容の簡潔な要約（日本語）")
    action_required: Optional[str] = Field(
        default=None, 
        description="メール内で特定された具体的なアクションアイテム"
    )
    deadline: Optional[str] = Field(
        default=None,
        description="メール内で言及されている期限"
    )
    
    mentioned_people: List[str] = Field(default_factory=list, description="言及されている個人名")
    mentioned_companies: List[str] = Field(default_factory=list, description="言及されている組織や会社名（例：マイクロソフト、豊田通商）")
    mentioned_projects: List[str] = Field(default_factory=list, description="言及されているプロジェクト名やシステム名（例：WisE）")
