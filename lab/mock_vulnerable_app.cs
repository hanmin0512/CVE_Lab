using Microsoft.AspNetCore.Builder;
using System.Diagnostics;
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapPost("/_layouts/15/ToolPane.aspx", async (context) => {
    var form = await context.Request.ReadFormAsync();
    string dwp = form["MSOTlPn_DWP"];
    if (!string.IsNullOrEmpty(dwp)) {
        // Lab Simulation: Check if the XML contains a command
        var match = System.Text.RegularExpressions.Regex.Match(dwp, "Command=\"([^\"]+)\"");
        if (match.Success) {
            string cmd = match.Groups[1].Value;
            
            // Execute the command on the Linux container
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
            // Return the output so the Python script can see it
            await context.Response.WriteAsync($"<html><body>[RCE_OUTPUT]: {output}</body></html>");
        } else {
            // Default reflection for 'Check' mode
            await context.Response.WriteAsync($"<html><body>CompressedDataTable=&quot;VANDA_TEST&quot;</body></html>");
        }
    }
});
app.Run();