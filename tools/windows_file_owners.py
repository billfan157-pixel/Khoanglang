"""Read locking processes for one file with Windows Restart Manager."""
import ctypes as c
from ctypes import wintypes as w
import json
import sys

class UniqueProcess(c.Structure):
    _fields_ = [('pid',w.DWORD),('start',w.FILETIME)]
class ProcessInfo(c.Structure):
    _fields_ = [('process',UniqueProcess),('name',w.WCHAR*256),('service',w.WCHAR*64),
        ('application_type',c.c_int),('status',w.ULONG),('session',w.DWORD),('restartable',w.BOOL)]

def main():
    api = c.WinDLL('Rstrtmgr')
    session, key = w.DWORD(), c.create_unicode_buffer(33)
    error = api.RmStartSession(c.byref(session),0,key)
    if error:
        raise OSError(error)
    try:
        paths = (w.LPCWSTR*1)(sys.argv[1])
        error = api.RmRegisterResources(session,1,paths,0,None,0,None)
        if error:
            raise OSError(error)
        needed, count, reason = w.UINT(),w.UINT(),w.DWORD()
        error = api.RmGetList(session,c.byref(needed),c.byref(count),None,c.byref(reason))
        if error not in (0,234):
            raise OSError(error)
        items = (ProcessInfo*needed.value)()
        count.value = needed.value
        error = api.RmGetList(session,c.byref(needed),c.byref(count),items,c.byref(reason))
        if error:
            raise OSError(error)
        print(json.dumps([dict(pid=p.process.pid,name=p.name) for p in items[:count.value]]))
    finally:
        api.RmEndSession(session)

if __name__ == '__main__':
    main()
