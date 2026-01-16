import json
import os
import argparse
from pathlib import Path
from src.api_manager import GeminiManager
from src.extractor import EmailExtractor

def run_single_test(target_file: str):
    # 1. 準備
    mgr = GeminiManager()
    extractor = EmailExtractor(mgr)
    
    if not os.path.exists(target_file):
        print(f"エラー：ファイル {target_file} が見つかりません。")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    print(f"ファイル処理中: {Path(target_file).name}...")

    # 3. 抽出ロジックの実行
    try:
        result = extractor.extract(md_content)
        
        # 4. JSONファイルに変換して出力
        output_data = result.model_dump_json(indent=2)
        
        output_filename = "single_test_result.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output_data)
            
        print("\n--- 抽出完了 ---")
        print(f"結果を保存しました: {output_filename}")
        print("\nJSON 内容プレビュー:")
        print(output_data)
        
    except Exception as e:
        print(f"処理失敗: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="単一の Markdown メールから構造化データを抽出します。")
    parser.add_argument("file", help="Markdown メールファイルへのパス")
    args = parser.parse_args()
    
    run_single_test(args.file)
