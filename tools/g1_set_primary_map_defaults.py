"""Change only map routing in local config, preserving all other bytes."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
path=root/'Config/DefaultEngine.ini'
text=path.read_bytes().decode('utf-8')
target='/Game/KhoangLang/Production/Maps/Lvl_KL_School3_Primary.Lvl_KL_School3_Primary'
changed,count=re.subn(r'(?m)^(EditorStartupMap|GameDefaultMap)=[^\r\n]*',lambda m:m[1]+'='+target,text)
if count!=2: raise RuntimeError('Expected exactly two existing map-routing keys')
path.write_bytes(changed.encode('utf-8'))
print('EditorStartupMap and GameDefaultMap now select Lvl_KL_School3_Primary')
