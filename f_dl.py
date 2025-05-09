# f_dl.py <Fshare File or Folder URL> [Password]
import requests, sys, os, time, re
from function import *
from urllib.parse import unquote
from bs4 import BeautifulSoup

def normalize_filename(name):
    import os
    name = os.path.splitext(name)[0]
    name = re.sub(r'[._\-]+', ' ', name)
    name = re.sub(r'\b(1080p|720p|x264|bluray|webrip|web ?dl|vietsub|sub|dub|fshare|remux|hdr|hevc|aac|mp4|mkv|avi|eng|multi|truehd|dts|ac3|h264|h265|10bit)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()

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

def is_file_url(url): return "/file/" in url
def is_folder_url(url): return "/folder/" in url

def extract_folder_code(url):
    import re
    match = re.search(r'/folder/(\w+)', url)
    return match.group(1) if match else None

def list_drive_files(target_dir):
    existing_files = set()
    for root, dirs, files in os.walk(target_dir):
        for name in files + dirs:
            existing_files.add(normalize_filename(name))
    return existing_files

def extract_fshare_file_names(folder_url):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    res = session.get(folder_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    files = []
    for tag in soup.find_all("a", href=True):
        if "/file/" in tag["href"]:
            file_name = tag.text.strip()
            if file_name:
                files.append((normalize_filename(file_name), "https://www.fshare.vn" + tag["href"]))
    return files

def file_exists_in_local_drive(filename, drive_existing):
    norm_fshare = normalize_filename(filename)
    return norm_fshare in drive_existing

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

    if file_exists_in_local_drive(file_name, list_drive_files(folder_download)):
        print(f"-> Skipping {file_name}, already exists at destination.")
        return

    if not os.path.exists(folder_download):
        os.makedirs(folder_download)

    print("┌───────────┐")
    print("| File Info |")
    print("└───────────┘")
    print(f"-> File Name: {file_name}")
    print(f"-> Save Folder: {folder_download}")

    chunk_download(dl_url, file_name, folder_download)

    print("-> File saved locally.")

    if cf['Drive'].get('remove_file_after_upload', 'False') == 'True':
        print("-> Done! Removing downloaded file...")
        removeFile(file_path)

def process_folder(folder_url, cf, current_path=""):
    print("📦 Đang quét thư mục:", folder_url)
    drive_existing = list_drive_files(cf['Drive']['file_download_path'])
    try:
        files_from_html = extract_fshare_file_names(folder_url)
        filtered_files = [(n, u) for n, u in files_from_html if n not in drive_existing]
        print(f"🔍 {len(filtered_files)} file cần tải (sau khi lọc):")
        for _, link in filtered_files:
            print(f"⬇️  Tải: {link}")
            download_and_upload(link, '', cf)
    except Exception as e:
        print("⚠️ Lỗi khi phân tích trang HTML:", e)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        exit("-> Please include file or folder URL")

    URL = sys.argv[1]
    PASSWORD = sys.argv[2] if len(sys.argv) == 3 else ''

    cf = get_config()

    if cf['Login']['session_id'] == '' or cf['Login']['token'] == '':
        exit("-> Please login first!")

    print("-> Connecting to Fshare...")

    if is_file_url(URL):
        download_and_upload(URL, PASSWORD, cf)
    elif is_folder_url(URL):
        process_folder(URL, cf)
    else:
        print("-> Unsupported Fshare URL!")
