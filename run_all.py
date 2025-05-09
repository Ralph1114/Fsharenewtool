# run_all.py <fshare_folder_url>
import os, sys
import subprocess

if len(sys.argv) < 2:
    exit("Usage: python run_all.py <fshare_folder_url>")

folder_url = sys.argv[1]
download_list_file = "download_list.json"

print("🔍 Bước 1: Lọc file chưa có trong Google Drive...")
subprocess.run(["python", "fshare_check_unique.py", folder_url, download_list_file])

if not os.path.exists(download_list_file):
    exit("⚠️ Không tìm thấy file download_list.json sau khi lọc.")

print("⬇️ Bước 2: Bắt đầu tải các file chưa có...")
subprocess.run(["python", "f_dl.py", download_list_file])