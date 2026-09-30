"""Read nominated processes' disk-file handle names; never close source handles."""
import ctypes as c
from ctypes import wintypes as w
import json
import sys

class Entry(c.Structure):
    _fields_=[('object',c.c_void_p),('pid',c.c_size_t),('value',c.c_size_t),
        ('access',w.ULONG),('trace',w.USHORT),('type',w.USHORT),('attributes',w.ULONG),('reserved',w.ULONG)]

def main():
    kernel=c.WinDLL('kernel32',use_last_error=True)
    ntdll=c.WinDLL('ntdll')
    kernel.OpenProcess.restype=w.HANDLE
    kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.GetFileType.argtypes=[w.HANDLE]
    kernel.CloseHandle.argtypes=[w.HANDLE]
    kernel.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,c.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]
    kernel.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD]
    ntdll.NtQuerySystemInformation.argtypes=[w.ULONG,c.c_void_p,w.ULONG,c.POINTER(w.ULONG)]
    needed=w.ULONG()
    size=1048576
    while True:
        buffer=c.create_string_buffer(size)
        status=ntdll.NtQuerySystemInformation(64,buffer,size,c.byref(needed))
        if status==0: break
        if (status & 0xffffffff)!=0xc0000004: raise OSError(hex(status & 0xffffffff))
        size=max(size*2,needed.value+65536)
    count=c.c_size_t.from_buffer(buffer).value
    items=(Entry*count).from_buffer(buffer,16)
    current=kernel.GetCurrentProcess()
    result=[]
    for pid in map(int,sys.argv[1:]):
        process=kernel.OpenProcess(0x40,False,pid)
        if not process:
            result.append(dict(pid=pid,error=c.get_last_error())); continue
        matches=[]
        try:
            for item in items:
                if item.pid!=pid: continue
                duplicate=w.HANDLE()
                if not kernel.DuplicateHandle(process,item.value,current,c.byref(duplicate),0,False,2): continue
                try:
                    if kernel.GetFileType(duplicate)!=1: continue
                    name=c.create_unicode_buffer(2048)
                    if kernel.GetFinalPathNameByHandleW(duplicate,name,len(name),0):
                        if 'School3' in name.value or 'BP_KL_Character' in name.value:
                            matches.append(dict(handle=item.value,path=name.value))
                finally: kernel.CloseHandle(duplicate)
        finally: kernel.CloseHandle(process)
        result.append(dict(pid=pid,handles=matches))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
