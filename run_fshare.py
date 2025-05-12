# run_fshare.py <Fshare folder URL>
import requests, os, sys, re, time, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from function import *

def normalize_filename(name):
    name = os.path.splitext(name)[0]
    name = re.sub(r'[._\-]+', ' ', name)
    name = re.sub(r'\b(1080p|720p|x264|bluray|webrip|web ?dl|vietsub|sub|dub|fshare|remux|hdr|hevc|aac|mp4|mkv|avi|eng|multi|truehd|dts|ac3|h264|h265|10bit)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9 ]+', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()

def list_drive_files(target_dir):
    existing = set()
    for root, dirs, files in os.walk(target_dir):
        for name in files + dirs:
            existing.add(normalize_filename(name))
    return existing

def extract_fshare_files(folder_url, cf):
    headers = {"User-Agent": cf['Auth']['user_agent']}
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
            files.append((file_name, normalize_filename(file_name), file_url))
    return files

def get_headers(cf):
    return {
        "Content-Type": "application/json",
        "accept": "application/json",
        "User-Agent": cf['Auth']['user_agent'],
        "Cookie": "session_id=" + cf['Login']['session_id']
    }

def download_and_upload(file_url, cf):
    header = get_headers(cf)
    data = {
        "url": file_url,
        "password": "",
        "token": cf['Login']['token'],
        "zipflag": 0
    }

    r = rq_fshare(URL=cf['API']['file_dl_api_url'], header=header, Data=json.dumps(data))
    if r.status_code != 200:
        try:
            msg = r.json().get("msg", "Unknown Error")
            print(f"❌ Fshare API error: {r.status_code} → " + bytes(msg, "utf-8").decode("unicode_escape"))
        except:
            print("❌ Unknown Error")
        return

    j = requestToJson(r)
    dl_url = j['location']
    file_name = unquote(dl_url.split('/')[-1])
    folder_download = cf['Drive']['file_download_path']
    file_path = os.path.join(folder_download.rstrip('/'), file_name)

    if not os.path.exists(folder_download):
        os.makedirs(folder_download)

    print(f"⬇️  Tải: {file_name}")
    chunk_download(dl_url, file_name, folder_download)
    print(f"✅ Đã lưu: {file_name}")

    if cf['Drive'].get('remove_file_after_upload', 'False') == 'True':
        removeFile(file_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("Usage: python run_fshare.py <fshare_folder_url>")

    folder_url = sys.argv[1]
    cf = toDict(myParser())
    drive_path = cf['Drive']['file_download_path']

    print("📁 Đang kiểm tra file trong Google Drive...")
    drive_existing = list_drive_files(drive_path)

    print("🌐 Đang quét danh sách file từ trang Fshare...")
    all_files = extract_fshare_files(folder_url, cf)

    to_download = [(name, url) for name_raw, name, url in all_files if name not in drive_existing]

    print(f"🔍 Tìm thấy {len(to_download)} file cần tải:")
    for name, url in to_download:
        print("   ", name)
    print("")

    for name, url in to_download:
        download_and_upload(url, cf)
        time.sleep(2)
