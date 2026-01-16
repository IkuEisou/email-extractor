import os
import json
import logging
import argparse
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

from src.api_manager import GeminiManager
from src.extractor import EmailExtractor
from src.models import EmailExtraction

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

def bulk_process_emails(input_dir: str, output_file: str):
    """
    入力ディレクトリ内のすべての Markdown ファイルを処理し、結果を JSON ファイルに保存します。
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logging.error(f"入力ディレクトリ {input_dir} が存在しません。")
        return

    # Extractor の初期化
    try:
        manager = GeminiManager()
        extractor = EmailExtractor(manager)
    except Exception as e:
        logging.error(f"Gemini の初期化に失敗しました: {e}")
        return

    results = []
    # .md ファイルのリストを取得
    md_files = list(input_path.glob("*.md"))
    logging.info(f"{len(md_files)} 個の Markdown ファイルが見つかりました。")

    for file_path in tqdm(md_files, desc="メール処理中"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # データの抽出
            extraction, _ = extractor.extract(content)
            
            # 辞書に変換してメタデータを追加
            data = extraction.model_dump()
            data['filename'] = file_path.name
            data['processed_at'] = datetime.now().isoformat()
            
            results.append(data)
            logging.info(f"正常に処理されました: {file_path.name}")
            
        except Exception as e:
            logging.error(f"処理エラー {file_path.name}: {e}")
            continue

    # 成果物の保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logging.info(f"一括処理が完了しました。結果は {output_file} に保存されました。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ディレクトリ内の Markdown メールを一括処理します。")
    parser.add_argument("input_dir", help="Markdown メールファイルを含むディレクトリ")
    parser.add_argument("--output", default="extraction_results.json", help="出力 JSON ファイル名 (デフォルト: extraction_results.json)")
    args = parser.parse_args()
    
    bulk_process_emails(args.input_dir, args.output)
