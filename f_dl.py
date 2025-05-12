# f_dl.py <Fshare File or Folder URL> [Password]
import requests, sys, os, time, re
from function import *
from bs4 import BeautifulSoup
from urllib.parse import unquote

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
    match = re.search(r'/folder/(\w+)', url)
    return match.group(1) if match else None

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

def extract_fshare_files_from_html(folder_url, cf):
    headers = {"User-Agent": cf['Auth']['user_agent']}
    res = requests.get(folder_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    files = []

    for span in soup.find_all("span", class_="mdc-grid-tile__title"):
        file_name = span.get_text(strip=True)
        if not file_name:
            continue

        parent_tag = span.find_parent("fshare-file")
        if not parent_tag:
            continue

        file_id = None
        class_list = parent_tag.get("class", [])
        for cls in class_list:
            if cls.startswith("file") and len(cls) > 8:
                file_id = cls.replace("file", "")
                break

        if file_id:
            file_url = f"https://www.fshare.vn/file/{file_id}"
            files.append((file_name, normalize_filename(file_name), file_url))

    return files

def file_exists_in_local_drive(filename):
    norm_fshare = normalize_filename(filename)
    target_dir = "/content/drive/MyDrive/Moviesall/media/movies/All"

    for root, dirs, files in os.walk(target_dir):
        for d in dirs:
            if normalize_filename(d) == norm_fshare:
                return True
        for f in files:
            if normalize_filename(f) == norm_fshare:
                return True
    return False

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
        print("Fshare API error:", r.status_code)
        exit(errorInfo(r.status_code))

    j = requestToJson(r)
    dl_url = j['location']
    file_name = unquote(dl_url.split('/')[-1])
    folder_download = cf['Drive']['file_download_path']
    file_path = os.path.join(folder_download.rstrip('/'), file_name)

    if file_exists_in_local_drive(file_name):
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
        removeFile(file_path)

def process_folder(folder_url, cf, current_path=""):
    print("🌐 Scanning Fshare folder from HTML...")
    drive_existing = list_drive_files(cf['Drive']['file_download_path'])
    all_files = extract_fshare_files_from_html(folder_url, cf)

    to_download = [(name, url) for name_raw, name, url in all_files if name not in drive_existing]
    print(f"🔍 Found {len(to_download)} new file(s) to download")

    for _, url in to_download:
        download_and_upload(url, '', cf)
        time.sleep(1)

# Entry point
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
