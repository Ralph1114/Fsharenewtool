# fshare_download_from_list.py
import json, sys, os
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

def download_and_upload(file_url, cf):
    header = get_headers(cf)
    data = {
        "url": file_url,
        "password": '',
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
        exit("Usage: python fshare_download_from_list.py <download_list.json>")

    file_list = sys.argv[1]
    cf = get_config()

    with open(file_list, "r") as f:
        urls = json.load(f)

    for _, url in urls:
        download_and_upload(url, cf)