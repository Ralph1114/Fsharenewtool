# fshare_check_unique.py
import requests, os, re, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from function import *

def normalize_filename(name):
    name = os.path.splitext(name)[0]
    name = re.sub(r'[._\-]+', ' ', name)
    name = re.sub(r'\b(1080p|720p|x264|bluray|webrip|web ?dl|vietsub|sub|dub|fshare|remux|hdr|hevc|aac|mp4|mkv|avi|eng|multi|truehd|dts|ac3|h264|h265|10bit)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9 ]+', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()

def extract_fshare_file_names(folder_url, cf):
    headers = {"User-Agent": cf["Auth"]["user_agent"]}
    res = requests.get(folder_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    files = []

    for title_tag in soup.find_all("div", class_="mdc-grid-tile__title"):
        file_name = title_tag.get_text(strip=True)
        if not file_name:
            continue

        fshare_file_tag = title_tag.find_parent("fshare-file")
        if not fshare_file_tag:
            continue

        class_list = fshare_file_tag.get("class", [])
        file_id = None
        for c in class_list:
            if c.startswith("file"):
                file_id = c.replace("file", "")
                break

        if file_id and len(file_id) >= 8:
            file_url = urljoin("https://www.fshare.vn", f"/file/{file_id}")
            files.append((normalize_filename(file_name), file_url))

    return files

def list_drive_files(target_dir):
    existing = set()
    for root, dirs, files in os.walk(target_dir):
        for name in files + dirs:
            existing.add(normalize_filename(name))
    return existing

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        exit("Usage: python fshare_check_unique.py <fshare_folder_url> <output_json>")

    folder_url = sys.argv[1]
    output_path = sys.argv[2]
    cf = toDict(myParser())
    drive_path = cf['Drive']['file_download_path']

    existing_files = list_drive_files(drive_path)
    fshare_files = extract_fshare_file_names(folder_url, cf)
    to_download = [(name, url) for name, url in fshare_files if name not in existing_files]

    with open(output_path, "w") as f:
        json.dump(to_download, f, indent=2)

    print(f"🔍 Found {len(to_download)} file(s) to download. Saved to {output_path}")
