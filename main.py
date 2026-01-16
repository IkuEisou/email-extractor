import json
import os
import argparse
import langextract as lx
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
        # extraction: Pydanticモデル, annotated_doc: langextractの中間データ
        extraction, annotated_doc = extractor.extract(md_content)
        
        # 入力ファイル名に基づいたベース名の生成
        file_stem = Path(target_file).stem
        
        # 4. JSONファイルに変換して出力
        output_data = extraction.model_dump_json(indent=2)
        json_output = f"{file_stem}_result.json"
        with open(json_output, "w", encoding="utf-8") as f:
            f.write(output_data)
            
        print("\n--- 抽出完了 ---")
        print(f"結果を保存しました: {json_output}")
        
        # 5. 可視化機能の追加
        print("可視化ファイルを生成中...")
        
        # 結果を JSONL ファイルに保存 (動的名)
        jsonl_output = f"{file_stem}.jsonl"
        lx.io.save_annotated_documents([annotated_doc], output_name=jsonl_output, output_dir=".")

        # ファイルから可視化を生成
        html_content = lx.visualize(jsonl_output)
        visualization_file = f"{file_stem}_visualization.html"
        with open(visualization_file, "w", encoding="utf-8") as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)
            else:
                f.write(html_content)
        
        print(f"可視化ファイルを保存しました: {visualization_file}")
        print("\nJSON 内容プレビュー:")
        print(output_data)
        
    except Exception as e:
        print(f"処理失敗: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="単一の Markdown メールから構造化データを抽出します。")
    parser.add_argument("file", help="Markdown メールファイルへのパス")
    args = parser.parse_args()
    
    run_single_test(args.file)
