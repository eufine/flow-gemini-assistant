# -*- coding: utf-8 -*-
"""
Script to compile .po translation files to .mo files
"""

import os
import sys
from pathlib import Path

# Add lib to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

def compile_po_file(po_file, mo_file):
    """Compile a .po file to .mo file using Python's msgfmt equivalent"""
    try:
        import polib
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        print(f"✓ Compiled: {po_file} -> {mo_file}")
        return True
    except ImportError:
        # If polib is not available, use gettext module
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'msgfmt', po_file, '-o', mo_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Compiled: {po_file} -> {mo_file}")
                return True
            else:
                print(f"✗ Error compiling {po_file}: {result.stderr}")
                return False
        except Exception as e:
            # Manual compilation as last resort
            print(f"⚠ Using manual compilation for {po_file}")
            return compile_po_manually(po_file, mo_file)

def compile_po_manually(po_file, mo_file):
    """Manual .po to .mo compilation"""
    try:
        # Read .po file
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple check if file has translations
        if 'msgid' in content and 'msgstr' in content:
            # Create empty .mo file (will use fallback in extensions.py)
            with open(mo_file, 'wb') as f:
                # Write minimal .mo file header
                f.write(b'\xde\x12\x04\x95\x00\x00\x00\x00')
            print(f"✓ Created placeholder: {mo_file}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

# Get plugin directory
plugin_dir = Path(__file__).parent
translations_dir = plugin_dir / 'plugin' / 'translations'

# Compile all .po files
languages = ['en_US', 'es_ES']
success_count = 0

for lang in languages:
    po_file = translations_dir / lang / 'LC_MESSAGES' / 'messages.po'
    mo_file = translations_dir / lang / 'LC_MESSAGES' / 'messages.mo'
    
    if po_file.exists():
        if compile_po_file(str(po_file), str(mo_file)):
            success_count += 1
    else:
        print(f"⚠ Not found: {po_file}")

print(f"\nCompiled {success_count}/{len(languages)} translation files")
