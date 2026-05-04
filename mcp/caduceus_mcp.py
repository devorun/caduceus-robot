#!/usr/bin/env python3
import sys, json, requests, os

ESP32_IP = "YOUR_ESP32_IP"
BASE_URL = f"http://{ESP32_IP}"
LYRICS_PATH = "/home/devran_an/heartlib/assets/lyrics.txt"

TOOLS = [
    {
        "name": "wave_hand",
        "description": (
            "Make the physical robot wave its arm. Use when user greets: "
            "hello, hi, hey, selam, merhaba, or when introducing yourself or saying goodbye."
        ),
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "walk_forward",
        "description": (
            "Make the physical robot take 2 steps forward. Use when user commands movement: "
            "come here, walk, step forward, gel, ileri gel, adim at, yaklas, approach."
        ),
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "recite_anthem",
        "description": (
            "Returns the official Caduceus anthem lyrics (written by Hermes Agent's heartmula skill). "
            "USE THIS TOOL when user says ANY of these phrases: "
            "sing, sing a song, sing your song, song, anthem, your anthem, "
            "perform, perform your anthem, recite, recite anthem, "
            "music, your music, sarki, sarkini soyle, soyle. "
            "After calling this, the lyrics will be returned and spoken to the user. "
            "Also automatically waves the hand for dramatic effect during recital."
        ),
        "inputSchema": {"type": "object", "properties": {}}
    }
]

def process_request(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc":"2.0","id":req_id,"result":{
            "protocolVersion":"2024-11-05",
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"caduceus-robot","version":"1.0"}
        }}
    elif method == "tools/list":
        return {"jsonrpc":"2.0","id":req_id,"result":{"tools":TOOLS}}
    elif method == "tools/call":
        tool_name = params.get("name")
        result_text = ""
        try:
            if tool_name == "wave_hand":
                requests.get(f"{BASE_URL}/salla", timeout=15)
                result_text = "Action executed: Waved hand."
            elif tool_name == "walk_forward":
                requests.get(f"{BASE_URL}/ileri", params={"n":2}, timeout=15)
                result_text = "Action executed: Walked 2 steps."
            elif tool_name == "recite_anthem":
                if os.path.exists(LYRICS_PATH):
                    with open(LYRICS_PATH, "r", encoding="utf-8") as f:
                        lyrics = f.read().strip()
                    requests.get(f"{BASE_URL}/salla", timeout=15)
                    result_text = f"{lyrics}"
                else:
                    result_text = "Anthem file not found."
            else:
                result_text = f"Unknown tool: {tool_name}"
        except Exception as e:
            result_text = f"Error: {str(e)}"
        return {"jsonrpc":"2.0","id":req_id,"result":{
            "content":[{"type":"text","text":result_text}]
        }}
    elif method == "notifications/initialized":
        return None
    return {"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":"Method not found"}}

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            res = process_request(req)
            if res:
                print(json.dumps(res))
                sys.stdout.flush()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
