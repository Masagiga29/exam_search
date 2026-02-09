#!/usr/bin/env python3
"""
各大学の解答速報ページからPDFリンクを抽出するスクリプト
"""

from bs4 import BeautifulSoup
import os
import csv
import json
from collections import defaultdict

def extract_pdf_links_from_page(html_content, university_info):
    """
    各大学ページからPDFリンクを抽出
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    pdf_links = []
    
    # PDFへのリンクを探す (href属性に.pdfを含むもの)
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href and '.pdf' in href.lower():
            # 相対パスを絶対パスに変換
            if href.startswith('/'):
                full_url = f"https://www.kawai-juku.ac.jp{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                # 相対パス (../../など)
                full_url = f"https://www.kawai-juku.ac.jp/nyushi/honshi/25/{university_info['code']}/{href}"
            
            # リンクテキストを取得
            link_text = link.get_text(strip=True)
            
            # 親要素から科目名などのコンテキストを取得
            context = ""
            parent = link.find_parent(['td', 'th', 'div', 'li', 'p'])
            if parent:
                context = parent.get_text(strip=True)
            
            pdf_links.append({
                'university': university_info['name'],
                'code': university_info['code'],
                'link_text': link_text,
                'context': context[:100],  # 最初の100文字のみ
                'pdf_url': full_url
            })
    
    return pdf_links

def process_all_universities(html_dir='./university_htmls'):
    """
    全ての大学HTMLファイルを処理
    """
    # 大学リストを読み込み
    universities = []
    if os.path.exists('/home/claude/university_links.csv'):
        with open('/home/claude/university_links.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                universities.append({
                    'name': row['大学名'],
                    'code': row['コード'],
                    'url': row['URL']
                })
    
    all_pdf_links = []
    processed_count = 0
    not_found_count = 0
    
    print("=" * 80)
    print("PDFリンク抽出を開始します...")
    print("=" * 80)
    
    for univ in universities:
        code = univ['code']
        html_file = os.path.join(html_dir, f"{code}.html")
        
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            pdf_links = extract_pdf_links_from_page(html_content, univ)
            all_pdf_links.extend(pdf_links)
            
            print(f"✓ {univ['name']:30s} ({code}) - {len(pdf_links)} PDFs found")
            processed_count += 1
        else:
            print(f"✗ {univ['name']:30s} ({code}) - HTMLファイルが見つかりません")
            not_found_count += 1
    
    print("\n" + "=" * 80)
    print(f"処理完了: {processed_count}大学 処理済み, {not_found_count}大学 未処理")
    print(f"合計 {len(all_pdf_links)} 件のPDFリンクを抽出しました")
    print("=" * 80)
    
    return all_pdf_links

def save_results(pdf_links, output_dir='/mnt/user-data/outputs'):
    """
    結果をCSVとJSONで保存
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # CSV形式で保存
    csv_file = os.path.join(output_dir, 'pdf_links.csv')
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        if pdf_links:
            writer = csv.DictWriter(f, fieldnames=['university', 'code', 'link_text', 'context', 'pdf_url'])
            writer.writeheader()
            writer.writerows(pdf_links)
    
    # JSON形式で保存
    json_file = os.path.join(output_dir, 'pdf_links.json')
    with open(json_file, 'w', encoding='utf-8', ensure_ascii=False, indent=2) as f:
        json.dump(pdf_links, f, ensure_ascii=False, indent=2)
    
    # 大学ごとに整理したCSVも作成
    by_university = defaultdict(list)
    for link in pdf_links:
        by_university[link['university']].append(link)
    
    organized_csv = os.path.join(output_dir, 'pdf_links_by_university.csv')
    with open(organized_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['大学名', 'コード', 'PDFリンク', 'リンクテキスト', '文脈'])
        
        for univ_name in sorted(by_university.keys()):
            for link in by_university[univ_name]:
                writer.writerow([
                    link['university'],
                    link['code'],
                    link['pdf_url'],
                    link['link_text'],
                    link['context']
                ])
    
    print(f"\n結果を以下のファイルに保存しました:")
    print(f"  1. {csv_file}")
    print(f"  2. {json_file}")
    print(f"  3. {organized_csv}")
    
    return csv_file, json_file, organized_csv

if __name__ == '__main__':
    import sys
    
    # HTMLファイルが格納されているディレクトリ
    html_dir = sys.argv[1] if len(sys.argv) > 1 else './university_htmls'
    
    if not os.path.exists(html_dir):
        print(f"エラー: ディレクトリ '{html_dir}' が見つかりません")
        print(f"\n使用方法:")
        print(f"  1. 各大学のHTMLファイルをダウンロード")
        print(f"  2. '{html_dir}' ディレクトリを作成")
        print(f"  3. HTMLファイルを '{{コード}}.html' の名前で保存")
        print(f"     例: t01.html, k01.html, n01.html...")
        print(f"  4. このスクリプトを実行")
        sys.exit(1)
    
    # PDFリンクを抽出
    pdf_links = process_all_universities(html_dir)
    
    # 結果を保存
    if pdf_links:
        save_results(pdf_links)
    else:
        print("\nPDFリンクが見つかりませんでした")
