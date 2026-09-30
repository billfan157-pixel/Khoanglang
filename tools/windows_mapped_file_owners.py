"""Read file mappings for nominated processes; never close their handles."""
import ctypes as c
from ctypes import wintypes as w
import json
import sys

class Region(c.Structure):
    _fields_ = [('base',c.c_void_p),('allocation_base',c.c_void_p),('allocation_protect',w.DWORD),
        ('partition',w.WORD),('size',c.c_size_t),('state',w.DWORD),('protect',w.DWORD),('kind',w.DWORD)]

def main():
    kernel, psapi = c.WinDLL('kernel32',use_last_error=True), c.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.restype = w.HANDLE
    kernel.VirtualQueryEx.argtypes = [w.HANDLE,c.c_void_p,c.POINTER(Region),c.c_size_t]
    kernel.VirtualQueryEx.restype = c.c_size_t
    psapi.GetMappedFileNameW.argtypes = [w.HANDLE,c.c_void_p,w.LPWSTR,w.DWORD]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    result=[]
    for pid in map(int,sys.argv[1:]):
        process=kernel.OpenProcess(0x410,False,pid)
        if not process:
            result.append(dict(pid=pid,error=c.get_last_error())); continue
        try:
            region, address=Region(),0
            matches=set()
            while kernel.VirtualQueryEx(process,address,c.byref(region),c.sizeof(region)):
                if region.kind == 0x40000 and region.state == 0x1000:
                    name=c.create_unicode_buffer(2048)
                    if psapi.GetMappedFileNameW(process,region.base,name,len(name)):
                        if 'School3' in name.value or 'BP_KL_Character' in name.value:
                            matches.add(name.value)
                following=(region.base or 0)+region.size
                if following<=address: break
                address=following
            result.append(dict(pid=pid,mappings=sorted(matches)))
        finally: kernel.CloseHandle(process)
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
