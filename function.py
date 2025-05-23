import requests, configparser, sys, os

def exit(err):
    sys.exit(err)

if not os.path.isfile('config.ini'):
    print('Missing config file! Please read tutorial and create a config file.')
    exit(0)

def myParser(path = 'config.ini'):
    ps = configparser.ConfigParser()
    ps.read(path)
    return ps

def toDict(parser, get='All'):
    config_dict = {}
    for section in parser.sections():
        config_dict[section] = {}
        for key, val in parser.items(section):
            config_dict[section][key] = val.strip()
    return config_dict if get == 'All' else config_dict.get(get, {})

def errorInfo(error_code):
    ec = str(error_code)
    i = {
        '405': '-> Wrong Password, please edit correct information config',
        '406': '-> Account not activated',
        '409': '-> Account is locked login',
        '410': '-> Account is locked login',
        '424': '-> You entered wrong password 3 times, please enter again after 10 minutes',
        '201': '-> Not logged in yet! Please rerun login file!'
    }
    return i[ec] if ec in i else "Unknown Error"

def rq_fshare(type = 'POST', URL = '', header = {}, Data = {}):
    r = requests.post(url = URL, headers = header, json = Data)
    if r.status_code != 200:
        print("⚠️ Fshare API error:", r.status_code, r.text)
    return r


def requestToJson(response):
    import json
    return json.loads(json.dumps(response.json()))

def chunk_download(furl, name, folder = 'downloaded/'):
    import math, enlighten
    url = furl
    fname = name
    MANAGER = enlighten.get_manager()
    r = requests.get(url, stream = True)
    assert r.status_code == 200, r.status_code
    dlen = int(r.headers.get('Content-Length', '0')) or None
    print("-> File Size: ", "{:.2f}".format(dlen/(2**20)/1024),"GB (" + str(math.ceil(dlen/2**20)), "MB)")
    if not os.path.exists(folder):
        os.makedirs(folder)
    with MANAGER.counter(color = 'green', total = dlen and math.ceil(dlen / 2 ** 20), unit = 'MiB', leave = False) as ctr,         open(os.path.join(folder, fname), 'wb', buffering = 2 ** 24) as f:
        for chunk in r.iter_content(chunk_size = 2 ** 20):
            f.write(chunk)
            ctr.update()
    return fname

def pushToDrive(file = '', path = ''):
    print("gdrive upload -p " + path + " '" + file + "'")
    with os.popen("gdrive upload -p " + path + " '" + file + "'") as f:
        print(f.readlines())

def pushToOneDrive(file = '', remotename ='', path = ''):
    cmd = "rclone copy '" + file + "' " + remotename + ":" + path + " --drive-acknowledge-abuse --drive-keep-revision-forever --drive-use-trash=false"
    print(cmd)
    with os.popen(cmd) as f:
        print(f.readlines())

def removeFile(file = ''):
    print("-> Deleting local File...")
    os.remove(file)
