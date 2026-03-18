# 🎯 QUICK REFERENCE - MCP INTEGRATION

## What You Have Now

### Configuration Location
```
C:\Users\91889\AppData\Roaming\Claude\claude_desktop_config.json
```

### Server Location
```
D:\Jmeter_MCP_NEW\server.py
```

### Available Tools (After Restart)
1. **generate_test_plan** - Create JMeter test plans
2. **run_test** - Execute tests
3. **list_test_plans** - List available plans
4. **list_results** - List test results
5. **parse_results** - Analyze test results
6. **compare_runs** - Compare two test runs

---

## 5-Minute Quick Start

### 1️⃣ Close Claude Desktop
```powershell
# Or just Alt+F4
# Make sure it's fully closed
```

### 2️⃣ Wait
```
3 seconds (be patient!)
```

### 3️⃣ Open Claude Desktop
```
Double-click the icon
Wait for it to load fully
```

### 4️⃣ Ask a Question
```
"Generate a test plan for https://httpbin.org/get with 5 users"
```

### 5️⃣ Done!
Claude will automatically:
- Discover your JMeter tools
- Generate a test plan
- Show you the file path
- Ask if you want to do anything else

---

## Example Prompts to Try

### After Setup Works, Try These:

#### Test Generation
```
Generate a JMeter test plan for:
- URL: https://api.example.com/login
- Users: 50
- Duration: 2 minutes
- Ramp-up: 10 seconds
```

#### Test Execution
```
Run the test plan we just created
```

#### Results Analysis
```
Show me a summary of the test results
```

#### Comparison
```
Compare the baseline test results with the latest run
```

#### Planning
```
What test plans do we have available?
```

---

## How to Tell It's Working

✅ **Good Signs:**
- Claude mentions "using tools"
- Files appear in test_plans/ or results/ directories
- Claude shows detailed configuration
- No error messages appear
- Connection indicator shows connected

❌ **Bad Signs:**
- "Tool not available" error
- "Connection refused" error
- No files created
- Python errors in logs
- Server won't start

---

## File Locations You Need to Know

| Purpose | Location |
|---------|----------|
| MCP Server | `D:\Jmeter_MCP_NEW\server.py` |
| Config (Claude) | `C:\Users\91889\AppData\Roaming\Claude\claude_desktop_config.json` |
| Test Plans Created | `D:\Jmeter_MCP_NEW\test_plans\*.jmx` |
| Results Created | `D:\Jmeter_MCP_NEW\results\*.jtl` |
| Python Files | `D:\Jmeter_MCP_NEW\*.py` |

---

## How It Works (Simple Version)

```
You: "Generate a test"
   ↓
Claude: Reads your request
   ↓
Claude: Sends JSON-RPC message to server.py via stdin
   ↓
server.py: Routes to generate_plan.py function
   ↓
generate_plan.py: Creates .jmx file
   ↓
server.py: Returns result via stdout
   ↓
Claude: Displays result to you
   ↓
You: See "Test plan created at D:\..."
```

All MCP protocol stuff happens automatically!

---

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Server won't connect | Restart Claude Desktop, wait 5 seconds |
| Config file not found | Copy from D:\Jmeter_MCP_NEW to C:\Users\91889\AppData\Roaming\Claude\ |
| Python not found | Install Python or use `py` instead of `python` |
| Import errors | Check PYTHONPATH in config = D:\Jmeter_MCP_NEW |
| JMeter tests fail | Check JMETER_HOME = C:\apache-jmeter-5.6.3 and JMeter installed |

---

## Environment Variables (Already Set)

These are set in your config file:

```json
"env": {
  "JMETER_HOME": "C:\\apache-jmeter-5.6.3",
  "PYTHONPATH": "D:\\Jmeter_MCP_NEW"
}
```

- **JMETER_HOME**: Where JMeter is installed (for running tests)
- **PYTHONPATH**: Where Python finds your modules (for imports)

---

## What Happens On Claude Desktop Startup

1. Claude Desktop reads config
2. Finds "jmeter" server definition
3. Runs: `py D:\Jmeter_MCP_NEW\server.py`
4. Sets environment variables
5. Server starts, listens on stdin
6. Claude queries available tools
7. Claude adds them to available tools list
8. Ready for use!

---

## Testing Without Claude (Already Done)

You've already verified:
- ✅ Server starts correctly
- ✅ MCP protocol works
- ✅ Tools are callable
- ✅ Imports work
- ✅ Functions execute
- ✅ Results return properly

So it WILL work with Claude Desktop!

---

## What Each Tool Does

### generate_test_plan
- Input: Description in English
- Output: .jmx file created
- Example: "Test API with 50 users"

### run_test
- Input: Path to .jmx file
- Output: .jtl results file created
- Requires: JMeter installed

### list_test_plans
- Input: None
- Output: List of available .jmx files

### list_results
- Input: None
- Output: List of available .jtl files

### parse_results
- Input: Path to .jtl file
- Output: Human-readable summary

### compare_runs
- Input: Two .jtl file paths
- Output: Side-by-side comparison

---

## Your Config Explained

```json
{
  "mcpServers": {
    "jmeter": {                          ← Server name
      "command": "py",                   ← Python executable
      "args": [
        "D:\\Jmeter_MCP_NEW\\server.py"  ← Script to run
      ],
      "env": {
        "JMETER_HOME": "C:\\apache-jmeter-5.6.3",  ← JMeter location
        "PYTHONPATH": "D:\\Jmeter_MCP_NEW"         ← Python modules path
      }
    }
  }
}
```

---

## Before You Start

Check off these:
- [ ] Config copied to C:\Users\91889\AppData\Roaming\Claude\
- [ ] D:\Jmeter_MCP_NEW\server.py exists
- [ ] All Python files exist
- [ ] Claude Desktop installed
- [ ] Ready to restart Claude

---

## You're Ready! 

Just:
1. Close Claude
2. Wait 3 seconds
3. Open Claude
4. Ask it to generate a test plan
5. Watch it work!

**Let's go! 🚀**
