import os
import sys
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.bilivox_manager import BiliVoxManager

def fix_file(manager, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has complete metadata
        if 'uid: ' in content and 'author: ' in content and 'bv: ' in content:
            return None

        # Extract BV
        bv_id = None
        match = re.search(r'bv: (BV\w+)', content)
        if match:
            bv_id = match.group(1)
        else:
            match = re.search(r'(BV[a-zA-Z0-9]{10})', os.path.basename(file_path))
            if match:
                bv_id = match.group(1)
        
        if not bv_id:
            print(f"Skipping {os.path.basename(file_path)}: No BV ID found")
            return None

        print(f"Fetching meta for {bv_id}...")
        meta = manager.downloader.get_video_meta(bv_id)
        
        if not meta or not meta.get('owner_name'):
            print(f"Failed to fetch meta for {bv_id}")
            return None

        # Re-save file with new frontmatter
        # We need to strip old frontmatter carefully or just let _save_markdown handle it?
        # _save_markdown appends new frontmatter and keeps content.
        # But here we want to replace frontmatter.
        
        # Simple parsing of body
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
        
        # Re-construct video dict
        video = {
            'bv_id': meta['bvId'],
            'title': meta['title'],
            'uploader': meta['owner_name'],
            'uid': meta['uid'],
            'url': f"https://www.bilibili.com/video/{meta['bvId']}",
            'upload_date': meta.get('upload_date')
        }
        
        # Use manager to save (it handles frontmatter generation)
        # But manager._save_markdown saves to a specific directory.
        # We want to overwrite the current file in-place or move it?
        # User wants "File Management" to show correct UP. 
        # If we keep it in "Independent Video" folder, we just update Frontmatter.
        
        # Manual Frontmatter construction to avoid directory moving complexity for now
        frontmatter = [
            "---",
            f"title: {video['title']}",
            f"bv: {video['bv_id']}",
            f"url: {video['url']}",
            f"author: {video['uploader']}",
            f"uid: {video['uid']}",
        ]
        if video['upload_date']:
            frontmatter.append(f"upload_date: {video['upload_date']}")
        frontmatter.append("source: bibigpt")
        frontmatter.append("---")
        frontmatter.append("")
        
        new_content = "\n".join(frontmatter) + body
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return f"Fixed {os.path.basename(file_path)} -> {video['uploader']}"
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return None

def main():
    manager = BiliVoxManager()
    output_dir = manager.output_dir
    
    files_to_fix = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.md'):
                files_to_fix.append(os.path.join(root, file))
    
    print(f"Found {len(files_to_fix)} files. Starting repair...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(lambda p: fix_file(manager, p), files_to_fix)
        
    for res in results:
        if res:
            print(res)

if __name__ == "__main__":
    main()
