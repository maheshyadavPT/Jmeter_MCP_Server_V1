# JMeter MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects **Claude Desktop** to Apache JMeter — letting you generate test plans, run load tests, and analyse results using plain English.

---

## What it does

| Tool | Description |
|---|---|
| `generate_test_plan` | Converts a plain-English description into a `.jmx` test plan |
| `run_test` | Executes a `.jmx` plan via JMeter and saves results to `.jtl` |
| `parse_results` | Analyses a `.jtl` file — response times, error rates, failure breakdown |
| `compare_runs` | Side-by-side comparison of two runs (baseline vs new) |
| `list_test_plans` | Lists available `.jmx` files |
| `list_results` | Lists available `.jtl` result files |

**Example prompts you can use in Claude Desktop:**
```
Generate a test plan for https://api.example.com/users with 20 users and 3 loops
Run the test plan httpbin_get_10users.jmx and save results as run1.jtl
Parse run1.jtl and show me the failure analysis
Compare run1.jtl vs run2.jtl and tell me if performance improved
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Tested on 3.13 and 3.14 |
| Java | 11–21 | Required to run JMeter |
| Apache JMeter | 5.6.x | [Download here](https://jmeter.apache.org/download_jmeter.cgi) |
| Claude Desktop | Latest | Free or Pro plan |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/jmeter-mcp-server.git
cd jmeter-mcp-server
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure JMeter path

Edit `config.py` and set your JMeter installation path:

```python
JMETER_HOME = r"C:\apache-jmeter-5.6.3"   # Windows
# JMETER_HOME = "/opt/apache-jmeter-5.6.3"  # Linux/macOS
```

Or set an environment variable instead:
```powershell
# Windows PowerShell
$env:JMETER_HOME = "C:\apache-jmeter-5.6.3"
```
```bash
# Linux / macOS
export JMETER_HOME=/opt/apache-jmeter-5.6.3
```

### 4. Fix JMeter heap size (important — prevents OOM crashes)

Edit `%JMETER_HOME%\bin\jmeter.bat` (Windows) or `$JMETER_HOME/bin/jmeter` (Linux/Mac):

```bat
REM Change this line:
set HEAP=-Xms1g -Xmx1g -XX:MaxMetaspaceSize=256m

REM To this (uses less memory):
set HEAP=-Xms256m -Xmx512m -XX:MaxMetaspaceSize=128m
```

### 5. Connect to Claude Desktop

Add this to your `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jmeter": {
      "command": "python",
      "args": ["C:\\path\\to\\jmeter-mcp-server\\server.py"]
    }
  }
}
```

> Restart Claude Desktop after saving the config.

---

## Project structure

```
jmeter-mcp-server/
├── server.py           ← MCP server entry point
├── config.py           ← JMeter path & directory config
├── generate_plan.py    ← Test plan generator (JMX builder)
├── run_test.py         ← JMeter executor
├── parse_results.py    ← JTL results analyser
├── compare_runs.py     ← Run comparison tool
├── requirements.txt    ← Python dependencies
├── test_plans/         ← Generated .jmx files (committed as examples)
├── results/            ← .jtl result files (gitignored)
└── README.md
```

---

## Supported test plan features

- Single and multiple HTTP endpoints in one plan
- Multiple thread groups (different user loads running in parallel)
- Basic Authentication (auto-detected from description)
- POST/PUT with JSON body
- Configurable think time, ramp-up, loop count, and duration
- Response assertions (HTTP 2xx check)
- Per-request failure messages in results

---

## Known limitations & fixes

### OOM crash when running tests
**Symptom:** `Native memory allocation failed to map 1073741824 bytes`  
**Fix:** Reduce JMeter heap in `jmeter.bat` — see Setup step 4 above.

### HTML report generation fails
**Symptom:** `Cannot create temporary directory C:\Windows\System32\temp`  
**Fix:** Add this to `jmeter.properties`:
```
jmeter.reportgenerator.temp_dir=C:/temp/jmeter
```

### MCP timeout on long tests
**Symptom:** `MCP error -32001: Request timed out` after ~4 minutes  
**Fix:** Keep test durations under 3 minutes per run, or upgrade to Claude Pro for longer session limits.

---

## Roadmap / planned improvements

- [ ] CSV Data Set Config support (parameterised test data)
- [ ] RegEx Extractor for token correlation
- [ ] Gaussian timer for realistic think time distribution  
- [ ] Transaction Controller grouping
- [ ] Automatic retry on MCP timeout
- [ ] Web dashboard for results (HTML export)

---

## Contributing

Pull requests welcome. Please open an issue first to discuss major changes.

---

## License

MIT
