# -*- coding: utf-8 -*-


# Do your job at here.
# The script is better to write the core functions.
import requests
import tempfile
import os, subprocess
import shutil
from plugin.settings import icon_path
from plugin.extensions import _l

def api_request(query, model, api_key):
        try:
            clean_query = query.replace("||", "").strip()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = { 'Content-Type': 'application/json' }
            data = { "contents": [{"parts": [{"text": clean_query}]}] }
            response = requests.post(url, headers=headers, json=data)

            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} - {response.text}")
            
            texto_respuesta = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # Create temp file in a user-accessible directory to avoid permission issues
            try:
                cache_dir = os.path.join(os.path.expanduser("~"), ".gemini_cache")
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir)
                    
                # Clean up old files (optional, keeps last 10)
                files = sorted([os.path.join(cache_dir, f) for f in os.listdir(cache_dir)], key=os.path.getmtime)
                if len(files) > 10:
                    for f in files[:-10]:
                        try: os.remove(f)
                        except: pass

                fd, preview_path = tempfile.mkstemp(prefix="gemini_preview_", suffix=".txt", dir=cache_dir, text=True)
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(texto_respuesta)
            except Exception as e:
                # Fallback to icon check
                preview_path = icon_path

            return [
                {
                    "Title": _l("Preview with Peek"),
                    "SubTitle": _l("View full response using PowerToys Peek"),
                    "IcoPath": icon_path,
                    "JsonRPCAction": {
                        "method": "launch_peek",
                        "parameters": [preview_path],
                        "dontHideAfterAction": False
                    }
                },
                {
                    "Title": _l("Copy to Clipboard"),
                    "SubTitle": texto_respuesta[:100] + "..." if len(texto_respuesta) > 100 else texto_respuesta,
                    "IcoPath": icon_path,
                    "JsonRPCAction": {
                        "method": "copy_to_clipboard",
                        "parameters": [texto_respuesta],
                        "dontHideAfterAction": False
                    }
                },
                {
                    "Title": _l("Open in Notepad"),
                    "SubTitle": _l("See the full response in Notepad"),
                    "IcoPath": icon_path,
                    "JsonRPCAction": {
                        "method": "open_in_notepad",
                        "parameters": [texto_respuesta, clean_query],
                        "dontHideAfterAction": False
                    }
                }
            ]
        except Exception as e:
            return [{
                "Title": _l("Error"),
                "SubTitle": str(e),
                "IcoPath": icon_path
            }]

def launch_peek(path):
    # Potential paths for PowerToys Peek
    paths = [
        os.path.expandvars(r'%ProgramFiles%\PowerToys\PowerToys.Peek.UI.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\PowerToys\PowerToys.Peek.UI.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\PowerToys\PowerToys.Peek.UI.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\PowerToys\WinUI3Apps\PowerToys.Peek.UI.exe')
    ]

    peek_path = None
    for p in paths:
        if os.path.exists(p):
            peek_path = p
            break
            
    if peek_path:
        # DETACHED_PROCESS = 0x00000008
        subprocess.Popen([peek_path, "--preview", path], shell=False, creationflags=0x00000008)
    else:
        # Fallback error message using clip
        msg = "PowerToys Peek not found. Please ensure PowerToys is installed."
        os.system(f'echo {msg} | clip')
        
def open_in_notepad(text, query):
        try:
            fd, path = tempfile.mkstemp(prefix=query[:20].replace(' ', '_') + "_", suffix=".txt", text=True)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(text)
            os.startfile(path)
            
        except Exception as e:
            os.system(f'echo Error al abrir bloc de notas: {str(e)} | clip')

def copy_to_clipboard(text):
    cmd = 'echo '+text.strip()+'|clip'
    subprocess.check_call(cmd, shell=True)