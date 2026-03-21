# Quick Reference - JMeter MCP Server

## Project Structure
```
D:\Jmeter_MCP_NEW/
├── Core Server Files
│   ├── server.py              Main MCP server
│   ├── config.py              Configuration
│   ├── generate_plan.py       Test plan generator
│   ├── run_test.py            Test executor
│   ├── parse_results.py       Results analyzer
│   └── compare_runs.py        Test comparator
├── Configuration
│   ├── requirements.txt       Dependencies
│   └── claude_desktop_config.json
├── Documentation
│   ├── README.md              Start here
│   └── CLAUDE_DESKTOP_SETUP_GUIDE.md
└── Data
    ├── test_plans/            Generated .jmx files
    └── results/               Test results .jtl files
```

## Installation (3 steps)

### Step 1: Install Python Dependencies
```bash
cd D:\Jmeter_MCP_NEW
pip install -r requirements.txt
```

### Step 2: Configure Claude Desktop
Add to Claude's config file (usually at `%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "jmeter-mcp-server": {
      "command": "python",
      "args": ["D:\\Jmeter_MCP_NEW\\server.py"]
    }
  }
}
```

### Step 3: Restart Claude Desktop
Close and reopen Claude Desktop to load the server.

## Available Tools

| Tool | Purpose |
|------|---------|
| `generate_test_plan` | Create JMeter .jmx files from descriptions |
| `run_test` | Execute a test plan and generate results |
| `list_test_plans` | List all available test plans |
| `list_results` | List all test results |
| `parse_results` | Analyze test results and show summary |
| `compare_runs` | Compare two test runs side-by-side |

## Usage Examples in Claude

### Example 1: Create and Run a Test
```
"Create a test plan for https://api.example.com/users 
with 50 concurrent users for 2 minutes, then run it"
```

### Example 2: Analyze Results
```
"Show me the summary of results from httpbin_50users"
```

### Example 3: Compare Runs
```
"Compare the spike_50u_2loops_results.jtl with sampleapis_spike_results.jtl"
```

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and features |
| `requirements.txt` | Python dependencies (only mcp>=1.0.0) |
| `CLAUDE_DESKTOP_SETUP_GUIDE.md` | Detailed setup instructions |
| `config.py` | Paths and configuration settings |

## Troubleshooting

### Tools not showing in Claude
1. Check `claude_desktop_config.json` is properly configured
2. Verify path to `server.py` is correct
3. Restart Claude Desktop

### Test execution fails
1. Ensure JMeter is installed
2. Set JMETER_HOME environment variable
3. Verify test_plans directory exists

### Results not found
1. Check `results/` directory exists
2. Run a test first to generate results
3. Use `list_results` tool to see available files

## Environment Setup

### Required
- Python 3.11+
- JMeter installed
- JMETER_HOME environment variable

### Install JMeter (Windows)
1. Download from https://jmeter.apache.org
2. Extract to a folder
3. Add JMETER_HOME to environment variables
4. Add %JMETER_HOME%\bin to PATH

## Support

- See `CLAUDE_DESKTOP_SETUP_GUIDE.md` for detailed setup
- Check `README.md` for feature overview
- Review tool descriptions in Claude for each tool's parameters

---

**Version:** 1.0.0 (Production Ready)
**Last Updated:** March 2026

