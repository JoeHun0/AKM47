"""text/AKM47_text.txt -> text/AKM47_text_paste.txt: the whole LocalizedTexts list as one line in the editor's own
copy/paste format (read from a .t3d dump of the asset). Fallback for tools/ue_add_text.py: open AKM47_Text,
right-click "Localized Texts" -> Paste. That replaces the whole list with these entries (gun name + description +
all upgrade texts, English + Ukrainian)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
texts, cur = {}, None
for line in open(os.path.join(ROOT, 'text', 'AKM47_text.txt'), encoding='utf-8'):
    s = line.strip()
    if re.match(r'^sid_\w+$', s):
        cur = s
        texts[cur] = {}
    elif cur and s.startswith('English:'):
        texts[cur]['en'] = s.split(':', 1)[1].strip()
    elif cur and s.startswith('Ukrainian:'):
        texts[cur]['uk'] = s.split(':', 1)[1].strip()


def q(t):
    return t.replace('\\', '\\\\').replace('"', '\\"')


items = [f'(SID="{k}",LanguagesToLocalizedStrings=((English, "{q(v["en"])}"),(Ukrainian, "{q(v["uk"])}")))'
         for k, v in texts.items()]
with open(os.path.join(ROOT, 'text', 'AKM47_text_paste.txt'), 'w', encoding='utf-8') as f:
    f.write('(' + ','.join(items) + ')\n')
print(len(items), 'entries')
