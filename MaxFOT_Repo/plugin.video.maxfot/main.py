import sys
import urllib.parse
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import re

# Addon Handle und Parameter holen
addon_handle = int(sys.argv[1])
base_url = sys.argv[0]
args = urllib.parse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()

# --- KONFIGURATION DEINER STREAMS ---
# Hier trägst du deine Links ein.
# Format: "Name": "Link zum Iframe oder direkten Video"
STREAMS = [
    {
        "name": "Chelsea vs Brentford (Beispiel)",
        "url": "https://embedsports.top/embed/admin/ppv-chelsea-vs-brentford/1",
        "is_iframe": True  # Setze auf True, wenn der Link eine Webseite mit Iframe ist
    },
    {
        "name": "Test Stream (Big Buck Bunny)",
        "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
        "is_iframe": False # Setze auf False, wenn es direkt eine .m3u8 oder .mp4 Datei ist
    }
]

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def get_real_stream_url(iframe_url):
    """
    Versucht, den echten Videolink (.m3u8) aus der Iframe-Seite zu extrahieren.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': iframe_url
    }
    
    try:
        xbmcgui.Dialog().notification('MaxFOT', 'Suche Videolink...', xbmcgui.NOTIFICATION_INFO, 2000)
        response = requests.get(iframe_url, headers=headers, timeout=10)
        html_content = response.text
        
        # Einfache Regex-Suche nach .m3u8 Links im Quelltext
        # Dies sucht nach http(s)://.....m3u8
        match = re.search(r'(https?://[^\s"\']+\.m3u8)', html_content)
        
        if match:
            real_url = match.group(1)
            # Oft brauchen diese Streams Header zum Abspielen
            # Wir fügen User-Agent und Referer für Kodi hinzu (Pipe-Syntax)
            kodi_url = f"{real_url}|User-Agent={headers['User-Agent']}&Referer={iframe_url}"
            return kodi_url
        else:
            # Falls kein m3u8 gefunden wurde, suchen wir nach src="..." in iframes
            # (Dies ist eine sehr simple Methode und funktioniert nicht bei allen geschützten Seiten)
            iframe_src_match = re.search(r'<iframe.*?src=["\'](.*?)["\']', html_content)
            if iframe_src_match:
                # Rekursiver Aufruf, falls ein Iframe im Iframe ist
                return get_real_stream_url(iframe_src_match.group(1))
            
            xbmcgui.Dialog().notification('MaxFOT', 'Kein Stream gefunden!', xbmcgui.NOTIFICATION_ERROR, 5000)
            return None
            
    except Exception as e:
        xbmcgui.Dialog().notification('MaxFOT', f'Fehler: {str(e)}', xbmcgui.NOTIFICATION_ERROR, 5000)
        return None

def main_menu():
    """Erstellt das Hauptmenü mit der Liste der Streams."""
    for stream in STREAMS:
        url = build_url({'mode': 'play', 'url': stream['url'], 'is_iframe': str(stream['is_iframe'])})
        li = xbmcgui.ListItem(stream['name'])
        li.setInfo('video', {'title': stream['name']})
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    
    xbmcplugin.endOfDirectory(addon_handle)

def play_video(url, is_iframe):
    """Spielt das Video ab."""
    play_url = url
    
    if is_iframe == 'True':
        extracted = get_real_stream_url(url)
        if extracted:
            play_url = extracted
        else:
            return # Abbruch wenn nichts gefunden

    play_item = xbmcgui.ListItem(path=play_url)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)

if __name__ == '__main__':
    mode = args.get('mode', None)
    
    if mode is None:
        main_menu()
    elif mode[0] == 'play':
        play_video(args['url'][0], args['is_iframe'][0])