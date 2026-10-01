"""Minimal MCP client for the live Unreal Editor endpoint on 127.0.0.1:8000.

Usage:
  python tools/ue_mcp.py status
  python tools/ue_mcp.py init
  python tools/ue_mcp.py toolsets
  python tools/ue_mcp.py describe <toolset_name>
  python tools/ue_mcp.py call <toolset_name> <tool_name> [args.json]
  python tools/ue_mcp.py top <tool_name> [args.json]
"""

import http.client
import json
import os
import secrets
import sys

HOST = '127.0.0.1'
PORT = 8000
PATH = '/mcp'
BASE = 'http://%s:%d%s' % (HOST, PORT, PATH)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.join(HERE, '_ue_mcp_session.txt')


def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def save_session(sid):
    if sid:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            f.write(sid)


def post(payload, session=None, timeout=45):
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    }
    if session:
        headers['Mcp-Session-Id'] = session
    conn = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    try:
        conn.request('POST', PATH, body=data, headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode('utf-8', 'replace')
        sid = resp.getheader('mcp-session-id')
        if resp.status >= 400:
            print('HTTP %s %s' % (resp.status, resp.reason))
            print(body)
            return sid, None
        return sid, body
    finally:
        conn.close()


def parse(body):
    """Handle both plain JSON and text/event-stream framing."""
    if body is None:
        return None
    text = body.strip()
    if text.startswith('event:') or '\ndata:' in text or text.startswith('data:'):
        chunks = []
        for line in text.splitlines():
            if line.startswith('data:'):
                chunks.append(line[5:].strip())
        text = '\n'.join(chunks)
    try:
        return json.loads(text)
    except Exception:
        return {'raw': text}


def rpc(method, params=None, notify=False, timeout=45):
    session = load_session()
    payload = {'jsonrpc': '2.0', 'method': method}
    if not notify:
        payload['id'] = secrets.randbelow(1 << 30) + 1
    if params is not None:
        payload['params'] = params
    sid, body = post(payload, session=session, timeout=timeout)
    if sid:
        save_session(sid)
    if notify:
        return None
    return parse(body)


def status():
    try:
        res = rpc('initialize', {
            'protocolVersion': '2025-11-25',
            'capabilities': {},
            'clientInfo': {'name': 'ue_mcp_status', 'version': '1.0'},
        })
        rpc('notifications/initialized', notify=True)
        tools = rpc('tools/list', {})
        names = [t['name'] for t in tools.get('result', {}).get('tools', [])]
    except Exception as exc:
        print('%s/mcp unreachable: %s' % (BASE, exc))
        print('The MCP server runs inside the Unreal Editor process. Open the')
        print('project in the editor, or run tools/mcp_doctor.ps1 -Launch.')
        return 1
    protocol = res.get('result', {}).get('protocolVersion', '?')
    print('ok  %s' % BASE)
    print('protocol %s' % protocol)
    print('tools   %s' % ', '.join(names))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]

    if cmd == 'status':
        return status()

    if cmd == 'init':
        res = rpc('initialize', {
            'protocolVersion': '2025-11-25',
            'capabilities': {},
            'clientInfo': {'name': 'cline', 'version': '1.0'},
        })
        print(json.dumps(res, indent=2, ensure_ascii=False)[:1500])
        rpc('notifications/initialized', notify=True)
        print('SESSION=' + str(load_session()))
        return 0

    if cmd == 'toolsets':
        res = rpc('tools/call', {'name': 'list_toolsets', 'arguments': {}})
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if cmd == 'describe':
        res = rpc('tools/call', {'name': 'describe_toolset',
                                 'arguments': {'toolset_name': sys.argv[2]}})
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if cmd in ('call', 'top'):
        args = {}
        if len(sys.argv) > (4 if cmd == 'call' else 3):
            path = sys.argv[4] if cmd == 'call' else sys.argv[3]
            with open(path, 'r', encoding='utf-8') as f:
                args = json.load(f)
        if cmd == 'call':
            params = {'name': 'call_tool',
                      'arguments': {'toolset_name': sys.argv[2],
                                    'tool_name': sys.argv[3],
                                    'arguments': args}}
        else:
            params = {'name': 'call_tool',
                      'arguments': {'tool_name': sys.argv[2],
                                    'arguments': args}}
        res = rpc('tools/call', params)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if (isinstance(res, dict) and 'error' not in res
                     and not res.get('result', {}).get('isError')) else 1

    print('unknown command: %s' % cmd)
    return 1


if __name__ == '__main__':
    sys.exit(main())
