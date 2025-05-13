# f_dl.py <Fshare File or Folder URL> [Password]
import requests, sys, os, time, json
from function import *
from urllib.parse import unquote
from datetime import datetime, timedelta

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

def get_existing_files():
    target_path = "/content/drive/MyDrive/Moviesall/media/movies/All"
    existing_files = set()
    if os.path.exists(target_path):
        print("-> Đang quét thư mục đích để kiểm tra file trùng lặp...")
        for file in os.listdir(target_path):
            existing_files.add(file)
        print(f"-> Đã tìm thấy {len(existing_files)} file hiện có.")
    return existing_files

EXISTING_FILES = get_existing_files()

def file_exists_in_local_drive(filename):
    return filename in EXISTING_FILES

def download_and_upload(file_url, file_password, cf, file_name=None):
    header = get_headers(cf)
    data = {
        "url": file_url,
        "password": file_password,
        "token": cf['Login']['token'],
        "zipflag": 0
    }

    if file_name and file_exists_in_local_drive(file_name):
        print(f"-> Bỏ qua {file_name}, đã tồn tại ở thư mục đích.")
        return

    r = rq_fshare(URL=cf['API']['file_dl_api_url'], header=header, Data=data)
    if r.status_code != 200:
        print(f"Lỗi khi lấy link tải: {r.status_code}")
        return

    j = requestToJson(r)
    dl_url = j['location']
    if not file_name:
        file_name = unquote(dl_url.split('/')[-1])
    
    folder_download = cf['Drive']['file_download_path']
    file_path = os.path.join(folder_download.rstrip('/'), file_name)

    if file_exists_in_local_drive(file_name):
        print(f"-> Bỏ qua {file_name}, đã tồn tại ở thư mục đích.")
        return

    if not os.path.exists(folder_download):
        os.makedirs(folder_download)

    print("┌───────────┐")
    print("| File Info |")
    print("└───────────┘")
    print(f"-> File Name: {file_name}")
    print(f"-> Save Folder: {folder_download}")

    chunk_download(dl_url, file_name, folder_download)
    print("-> File đã lưu thành công.")
    EXISTING_FILES.add(file_name)

    if cf['Drive'].get('remove_file_after_upload', 'False') == 'True':
        print("-> Hoàn tất! Đang xóa file đã tải...")
        removeFile(file_path)

def get_folder_file_list(folder_url, cf, current_path=""):
    folder_code = extract_folder_code(folder_url)
    all_files = []
    page = 1
    print(f"-> Đang quét thư mục Fshare {folder_url}...")
    while True:
        api_path = f"https://www.fshare.vn/api/v3/files/folder?linkcode={folder_code}&sort=type,-modified&page={page}"
        r = requests.get(api_path, headers=get_headers(cf))
        if r.status_code != 200:
            print(f"Lỗi khi đọc trang thư mục {page}: {r.status_code}")
            break
        data = r.json()
        folder_name = data['current']['name']
        full_path = os.path.join(current_path, folder_name)
        for item in data['items']:
            if item['type'] == 1:
                file_url = f"https://fshare.vn/file/{item['linkcode']}"
                file_name = item['name']
                if not file_exists_in_local_drive(file_name):
                    all_files.append({
                        'url': file_url,
                        'name': file_name
                    })
                else:
                    print(f"-> Bỏ qua {file_name}, đã tồn tại.")
            else:
                sub_folder_url = f"https://www.fshare.vn/folder/{item['linkcode']}"
                sub_files = get_folder_file_list(sub_folder_url, cf, full_path)
                all_files.extend(sub_files)
        if not data.get('_links', {}).get('next'):
            break
        page += 1
        time.sleep(1)
    return all_files

def process_folder(folder_url, cf):
    files_to_download = get_folder_file_list(folder_url, cf)
    print(f"-> Tìm thấy {len(files_to_download)} file cần tải.")
    for i, file_info in enumerate(files_to_download, 1):
        print(f"-> Đang tải file {i}/{len(files_to_download)}: {file_info['name']}")
        download_and_upload(file_info['url'], '', cf, file_info['name'])

if __name__ == "__main__":
    if len(sys.argv) == 1:
        exit("-> Vui lòng cung cấp URL file hoặc thư mục")
    URL = sys.argv[1]
    PASSWORD = sys.argv[2] if len(sys.argv) == 3 else ''
    cf = get_config()
    if cf['Login']['session_id'] == '' or cf['Login']['token'] == '':
        exit("-> Vui lòng đăng nhập trước!")
    print("-> Đang kết nối đến Fshare...")
    if is_file_url(URL):
        download_and_upload(URL, PASSWORD, cf)
    elif is_folder_url(URL):
        process_folder(URL, cf)
    else:
        print("-> URL Fshare không được hỗ trợ!")
