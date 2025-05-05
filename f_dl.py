# f_dl.py <Fshare File or Folder URL> [Password]
import requests, sys, os, time
from function import *
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
    import re
    match = re.search(r'/folder/(\w+)', url)
    return match.group(1) if match else None

def file_exists_in_local_drive(filename):
    target_path = os.path.join("/content/drive/MyDrive/Moviesall/media/movies/All", filename)
    return os.path.exists(target_path)

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
        print("-> Done! Removing downloaded file...")
        removeFile(file_path)

def process_folder(folder_url, cf, current_path=""):
    folder_code = extract_folder_code(folder_url)
    page = 1

    while True:
        api_path = f"https://www.fshare.vn/api/v3/files/folder?linkcode={folder_code}&sort=type,-modified&page={page}"
        r = requests.get(api_path, headers=get_headers(cf))

        if r.status_code != 200:
            print(f"Error reading folder page {page}: {r.status_code}")
            return

        data = r.json()
        folder_name = data['current']['name']
        full_path = os.path.join(current_path, folder_name)

        for item in data['items']:
            if item['type'] == 1:
                file_url = f"https://fshare.vn/file/{item['linkcode']}"
                download_and_upload(file_url, '', cf)
            else:
                sub_folder_url = f"https://fshare.vn/folder/{item['linkcode']}"
                process_folder(sub_folder_url, cf, full_path)

        if not data.get('_links', {}).get('next'):
            break
        page += 1
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
