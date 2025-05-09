# f_dl.py <Fshare Folder URL>
import requests, sys, os, time, re
from function import *
from bs4 import BeautifulSoup
from urllib.parse import unquote

def normalize_filename(name):
    import os
    name = os.path.splitext(name)[0]
    name = re.sub(r'[._\-]+', ' ', name)
    name = re.sub(r'\b(1080p|720p|x264|bluray|webrip|web ?dl|vietsub|sub|dub|fshare|remux|hdr|hevc|aac|mp4|mkv|avi|eng|multi|truehd|dts|ac3|h264|h265|10bit)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()

def list_drive_files(target_dir):
    existing = set()
    for root, dirs, files in os.walk(target_dir):
        for name in files + dirs:
            existing.add(normalize_filename(name))
    return existing

def extract_fshare_file_names(folder_url):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    res = session.get(folder_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    files = []
    for tag in soup.find_all("a", href=True):
        if "/file/" in tag["href"]:
            text = tag.text.strip()
            if text:
                files.append((normalize_filename(text), "https://www.fshare.vn" + tag["href"]))
    return files

def get_config():
    ps = myParser()
    return toDict(ps)

def get_headers(cf):
    return {
        "Content-Type": "application/json",
        "accept": "application/json",
        "User-Agent": cf['Auth']['user_agent'],
        "Cookie": "session_id=" + cf['Login']['session_id']
    }

def download_and_upload(file_url, file_password, cf):
    header = get_headers(cf)
    data = {
        "url": file_url,
        "password": file_password,
        "token": cf['Login']['token'],
        "zipflag": 0
    }

    r = rq_fshare(URL=cf['API']['file_dl_api_url'], header=header, Data=data)
    if r.status_code != 200:
        try:
            msg = r.json().get("msg", "Unknown Error")
            print(f"Fshare API error: {r.status_code} → " + bytes(msg, "utf-8").decode("unicode_escape"))
        except:
            print("Unknown Error")
        exit(errorInfo(r.status_code))

    j = requestToJson(r)
    dl_url = j['location']
    file_name = unquote(dl_url.split('/')[-1])
    folder_download = cf['Drive']['file_download_path']
    file_path = os.path.join(folder_download.rstrip('/'), file_name)

    if normalize_filename(file_name) in list_drive_files(folder_download):
        print(f"⏩ Bỏ qua {file_name}, đã có trong Drive.")
        return

    if not os.path.exists(folder_download):
        os.makedirs(folder_download)

    print("⬇️ Đang tải:", file_name)
    chunk_download(dl_url, file_name, folder_download)
    print("✅ Đã lưu:", file_name)

    if cf['Drive'].get('remove_file_after_upload', 'False') == 'True':
        removeFile(file_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("-> Please include Fshare folder URL.")

    folder_url = sys.argv[1]
    cf = get_config()
    drive_path = cf['Drive']['file_download_path']

    print("📁 Quét Google Drive...")
    existing_files = list_drive_files(drive_path)

    print("🌐 Quét danh sách file từ Fshare folder...")
    fshare_files = extract_fshare_file_names(folder_url)

    print("🔍 Lọc file chưa có trong Drive...")
    to_download = [(name, url) for name, url in fshare_files if name not in existing_files]

    print(f"📦 Tìm thấy {len(to_download)} file cần tải:")
    for name, link in to_download:
        download_and_upload(link, '', cf)
