import requests
import json
import re
import datetime
import base64
from io import BytesIO
from PIL import Image
import ddddocr
import urllib3
from loguru import logger

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define URLs
KeepAliveURL = "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive"
GetPointURL = "https://www.aeropres.in/api/atom/v1/userreferral/getpoint"
LoginURL = "https://www.aeropres.in//chromeapi/dawn/v1/user/login/v2"
PuzzleID = "https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle"

# Create a request session
session = requests.Session()

# Load proxy settings from file
def load_proxies(filename):
    with open(filename, 'r') as file:
        proxies = {
            "http": file.readline().strip(),
            "https": file.readline().strip()
        }
    return proxies

# Define proxy file
proxy_file = 'proxy.txt'

# Apply proxy settings to the session
proxies = load_proxies(proxy_file)
session.proxies.update(proxies)

# Set up logging
logger.add("file.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")

# Set up common headers
headers = {
    "Content-Type": "application/json",
    "Origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Priority": "u=1, i",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}

def GetPuzzleID():
    r = session.get(PuzzleID, headers=headers, verify=False).json()
    puzzid = r['puzzle_id']
    return puzzid

def IsValidExpression(expression):
    pattern = r'^[A-Za-z0-9]{6}$'
    return bool(re.match(pattern, expression))

def RemixCaptacha(base64_image):
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data)).convert('RGB')
    
    new_image = Image.new('RGB', image.size, 'white')
    width, height = image.size
    for x in range(width):
        for y in range(height):
            pixel = image.getpixel((x, y))
            if pixel == (48, 48, 48):  # Black pixel
                new_image.putpixel((x, y), pixel)
            else:
                new_image.putpixel((x, y), (255, 255, 255))  # White pixel

    ocr = ddddocr.DdddOcr(show_ad=False)
    ocr.set_ranges(0)
    result = ocr.classification(new_image)
    logger.debug(f'[1] Captcha result: {result}, Is valid: {IsValidExpression(result)}')
    if IsValidExpression(result):
        return result

def login(USERNAME, PASSWORD):
    puzzid = GetPuzzleID()
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "logindata": {
            "_v": "1.0.7",
            "datetime": current_time
        },
        "puzzle_id": puzzid,
        "ans": "0"
    }
    refresh_image = session.get(f'https://www.aeropres.in/chromeapi/dawn/v1/puzzle/get-puzzle-image?puzzle_id={puzzid}', headers=headers, verify=False).json()
    code = RemixCaptacha(refresh_image['imgBase64'])
    if code:
        logger.success(f'[√] Captcha result: {code}')
        data['ans'] = str(code)
        login_data = json.dumps(data)
        logger.info(f'[2] Login data: {login_data}')
        try:
            r = session.post(LoginURL, login_data, headers=headers, verify=False).json()
            logger.debug(r)
            token = r['data']['token']
            logger.success(f'[√] AuthToken obtained: {token}')
            return token
        except Exception as e:
            logger.error(f'[x] Captcha error, retrying...')

def KeepAlive(USERNAME, TOKEN):
    data = {"username": USERNAME, "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp", "numberoftabs": 0, "_v": "1.0.7"}
    json_data = json.dumps(data)
    headers['authorization'] = "Bearer " + str(TOKEN)
    r = session.post(KeepAliveURL, data=json_data, headers=headers, verify=False).json()
    logger.info(f'[3] Keeping connection alive... {r}')

def GetPoint(TOKEN):
    headers['authorization'] = "Bearer " + str(TOKEN)
    r = session.get(GetPointURL, headers=headers, verify=False).json()
    logger.success(f'[√] Points obtained: {r}')

def main(USERNAME, PASSWORD):
    TOKEN = ''
    if not TOKEN:
        while True:
            TOKEN = login(USERNAME, PASSWORD)
            if TOKEN:
                break

    count = 0
    max_count = 200
    while True:
        try:
            KeepAlive(USERNAME, TOKEN)
            GetPoint(TOKEN)
            count += 1
            if count >= max_count:
                logger.debug(f'[√] Re-login to obtain new Token...')
                while True:
                    TOKEN = login(USERNAME, PASSWORD)
                    if TOKEN:
                        break
                count = 0
        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    with open('password.txt', 'r') as f:
        username, password = f.readline().strip().split(':')
    main(username, password)
