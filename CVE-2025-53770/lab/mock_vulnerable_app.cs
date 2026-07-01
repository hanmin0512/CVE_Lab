using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration; // 환경 변수 읽기를 위해 추가
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);
// 도커 컨테이너에 전달된 환경 변수(.env)를 읽어옵니다.
builder.Configuration.AddEnvironmentVariables();
var app = builder.Build();

// 서버 설정값 불러오기 (값이 없으면 뒤의 기본값 사용)
string expectedUser = app.Configuration["LAB_ADMIN_USER"] ?? "admin";
string expectedPass = app.Configuration["LAB_ADMIN_PASS"] ?? "admin123";
string expectedCookie = app.Configuration["LAB_COOKIE_VALUE"] ?? "default_token";

// 1. GET /login : 실제 폼(Form)이 있는 로그인 페이지 출력
app.MapGet("/login", async (context) => {
    string errorMsg = context.Request.Query.ContainsKey("error") ? "<div class='error'>Invalid username or password.</div>" : "";
    
    context.Response.ContentType = "text/html; charset=utf-8";
    await context.Response.WriteAsync($@"<!DOCTYPE html>
<html>
<head>
    <title>Sign In - SharePoint</title>
    <style>
        body {{ font-family: sans-serif; background: #f3f2f1; text-align: center; padding-top: 100px; }}
        .login-box {{ background: white; padding: 40px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-block; width: 300px; }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; box-sizing: border-box; }}
        button {{ width: 100%; padding: 10px; background: #0072c6; color: white; border: none; cursor: pointer; }}
        .error {{ color: #d9534f; margin-bottom: 15px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class='login-box'>
        <h2>Sign In</h2>
        {errorMsg}
        <form method='POST' action='/login'>
            <input type='text' name='username' placeholder='someone@example.com' required />
            <input type='password' name='password' placeholder='Password' required />
            <button type='submit'>Sign in</button>
        </form>
    </div>
</body>
</html>");
});

// 2. POST /login : 로그인 정보 검증 로직
app.MapPost("/login", async (context) => {
    var form = await context.Request.ReadFormAsync();
    string user = form["username"];
    string pass = form["password"];

    if (user == expectedUser && pass == expectedPass) {
        // 성공 시: .env에 설정된 진짜 쿠키 값을 발급하고 메인 페이지로 이동
        context.Response.Cookies.Append("SP_SESSION", expectedCookie);
        context.Response.Redirect("/");
    } else {
        // 실패 시: 에러 메시지와 함께 다시 로그인 페이지로
        context.Response.Redirect("/login?error=1");
    }
});

// 3. GET / : 메인 페이지 (쿠키 '값'까지 정확한지 검사)
app.MapGet("/", async (context) => {
    context.Request.Cookies.TryGetValue("SP_SESSION", out string userCookie);
    
    // 쿠키가 없거나, 값이 우리가 .env에 설정한 값과 다르면 쫓아냄
    if (userCookie != expectedCookie) {
        context.Response.Redirect("/login");
        return;
    }

    context.Response.ContentType = "text/html; charset=utf-8";
    await context.Response.WriteAsync(@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <title>Home - Team Site</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; margin: 0; padding: 0; background-color: #f3f2f1; color: #323130; }
        .header { background-color: #0072c6; color: white; padding: 15px 20px; display: flex; align-items: center; }
        .header h1 { margin: 0; font-size: 22px; font-weight: 400; }
        .nav-bar { background-color: #f4f4f4; border-bottom: 1px solid #c8c8c8; padding: 10px 20px; font-size: 13px; color: #666; }
        .container { display: flex; margin: 20px 40px; height: calc(100vh - 120px); }
        .sidebar { width: 220px; padding-right: 20px; }
        .sidebar ul { list-style: none; padding: 0; margin: 0; }
        .sidebar li { padding: 12px 10px; color: #0078d4; cursor: pointer; font-size: 14px; }
        .sidebar li:hover { background-color: #edebe9; }
        .sidebar .title { font-weight: 600; color: #333; padding-bottom: 5px; cursor: default; }
        .content { flex: 1; padding: 10px 40px; background: white; border: 1px solid #eaeaea; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .content h2 { font-weight: 300; font-size: 28px; color: #323130; margin-top: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
        .alert { background-color: #fff4ce; border-left: 4px solid #f2c811; padding: 15px; margin-top: 20px; font-size: 14px; color: #333; }
        .file-list { margin-top: 20px; border-collapse: collapse; width: 100%; font-size: 14px; }
        .file-list th { text-align: left; padding: 10px; border-bottom: 1px solid #ccc; font-weight: 600; }
        .file-list td { padding: 10px; border-bottom: 1px solid #eee; color: #0078d4; }
    </style>
</head>
<body>
    <div class='header'><h1>SharePoint</h1></div>
    <div class='nav-bar'>SharePoint > Sites > Vulnerable Lab > Home</div>
    <div class='container'>
        <div class='sidebar'>
            <ul>
                <li class='title'>Quick Launch</li>
                <li>Documents</li>
                <li>Site Contents</li>
                <li>Site Settings</li>
                <li>Recycle Bin</li>
            </ul>
        </div>
        <div class='content'>
            <h2>Welcome to your Team Site</h2>
            <div class='alert'>
                <strong>[Lab Status]</strong> Server is online. Endpoint listening on <code>/_layouts/15/ToolPane.aspx</code> (POST).
            </div>
            <p style='margin-top: 25px; color: #666;'>Shared Documents</p>
            <table class='file-list'>
                <tr><th>Name</th><th>Modified</th><th>Modified By</th></tr>
                <tr><td>Q3_Financial_Report.xlsx</td><td>Yesterday at 4:30 PM</td><td>System Account</td></tr>
                <tr><td>Employee_Handbook_v2.docx</td><td>October 12</td><td>Admin</td></tr>
                <tr><td>Project_Vanda</td><td>October 05</td><td>System Account</td></tr>
            </table>
        </div>
    </div>
</body>
</html>");
});

// 4. POST 취약점 엔드포인트
app.MapPost("/_layouts/15/ToolPane.aspx", async (context) => {
    context.Request.Cookies.TryGetValue("SP_SESSION", out string userCookie);
    bool isAuthValid = (userCookie == expectedCookie);
    
    string referer = context.Request.Headers["Referer"].ToString();
    bool isRefererBypass = !string.IsNullOrEmpty(referer) && referer.Contains("/_layouts/SignOut.aspx");

    // 올바른 쿠키가 있거나, Referer 우회 기법을 썼을 때만 통과
    if (!isAuthValid && !isRefererBypass) {
        context.Response.Redirect("/login");
        return;
    }

    var form = await context.Request.ReadFormAsync();
    string dwp = form["MSOTlPn_DWP"];
    if (!string.IsNullOrEmpty(dwp)) {
        var match = System.Text.RegularExpressions.Regex.Match(dwp, "Command=\"([^\"]+)\"");
        if (match.Success) {
            string cmd = match.Groups[1].Value;
            var process = new Process {
                StartInfo = new ProcessStartInfo {
                    FileName = "/bin/bash",
                    Arguments = $"-c \"{cmd}\"",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                }
            };
            process.Start();
            string output = await process.StandardOutput.ReadToEndAsync();
            await context.Response.WriteAsync($"<html><body>[RCE_OUTPUT]: {output}</body></html>");
        }
    }
});

app.Run();