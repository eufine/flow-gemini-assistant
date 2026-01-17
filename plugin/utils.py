# -*- coding: utf-8 -*-


# Do your job at here.
# The script is better to write the core functions.
import requests
import tempfile
import os, subprocess
import shutil
from plugin.settings import icon_path
from plugin.extensions import _l

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".gemini_cache")

def cleanup_cache(keep_last=1):
    """
    Clean up old files in the cache directory, keeping only the 'keep_last' most recent ones.
    """
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
            return

        files = sorted(
            [os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR)],
            key=os.path.getmtime
        )

        if len(files) > keep_last:
            for f in files[:-keep_last]:
                try:
                    os.remove(f)
                except Exception:
                    pass
    except Exception:
        pass

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
            
            try:
                cleanup_cache()

                # Generate CamelCase filename from query
                # Keep alphanumeric and spaces to allow splitting, then title case properties
                words = "".join([c if c.isalnum() else " " for c in clean_query]).split()
                camel_name = "".join([w.capitalize() for w in words])
                
                if not camel_name:
                    camel_name = "GeminiResponse"
                    
                # Truncate to avoid path limit issues (max 50 chars for name)
                camel_name = camel_name[:50]
                
                preview_filename = f"{camel_name}.md"
                preview_path = os.path.join(CACHE_DIR, preview_filename)
                
                with open(preview_path, 'w', encoding='utf-8') as f:
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
            cleanup_cache()
            
            clean_prefix = query[:20].replace(' ', '_').replace('||', '')
            fd, path = tempfile.mkstemp(prefix=f"{clean_prefix}_", suffix=".txt", dir=CACHE_DIR, text=True)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(text)
            os.startfile(path)
            
        except Exception as e:
            os.system(f'echo Error al abrir bloc de notas: {str(e)} | clip')

def copy_to_clipboard(text):
    cmd = 'echo '+text.strip()+'|clip'
    subprocess.check_call(cmd, shell=True)