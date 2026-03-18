"""
server.py - JMeter MCP Server
==============================
Exposes JMeter capabilities as MCP tools so Claude Desktop
(or any MCP client) can generate test plans, run tests,
parse results, and compare runs — all via natural language.

Transport: stdio (standard input/output)
Usage    : python server.py
"""

import asyncio  # async/await runtime
import sys
import logging

# ─────────────────────────────────────────────
# Standard library imports
# ─────────────────────────────────────────────
import traceback  # format Python exceptions for error messages

from mcp import types  # MCP type definitions (Tool, TextContent …)
# ─────────────────────────────────────────────
# MCP SDK imports  (pip install mcp)
# ─────────────────────────────────────────────
from mcp.server import Server  # base MCP server class
from mcp.server.stdio import stdio_server  # stdio transport helper

# Setup logging to stderr (not stdout, which is used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

from compare_runs import compare_runs
# ─────────────────────────────────────────────
# Local tool modules (files inside /tools/)
# ─────────────────────────────────────────────
from generate_plan import generate_test_plan
from parse_results import parse_results
from run_test import run_test, list_test_plans, list_results

# ─────────────────────────────────────────────────────────────────────
# Tool Registry
# Each entry describes ONE tool that Claude Desktop can discover
# and call.  Claude reads the "description" and "inputSchema" to
# decide when and how to call the tool.
# ─────────────────────────────────────────────────────────────────────
TOOLS = [
    types.Tool(
        name="generate_test_plan",
        description=(
            "Generate a JMeter .jmx test plan file from a plain-English description. "
            "Supports HTTP/HTTPS endpoints, configurable thread counts, ramp-up time, "
            "loop counts, think time, and common assertions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Plain-English description of what to test. "
                                   "Example: 'Test login API at https://api.example.com/login "
                                   "with 50 concurrent users for 2 minutes'"
                },
                "output_file": {
                    "type": "string",
                    "description": "Optional filename for the .jmx file. "
                                   "Defaults to 'test_plan_<timestamp>.jmx'"
                }
            },
            "required": ["description"]   # only 'description' is mandatory
        }
    ),

    types.Tool(
        name="run_test",
        description=(
            "Execute a JMeter .jmx test plan and save results to a .jtl file. "
            "Requires JMeter to be installed and JMETER_HOME configured."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "test_plan": {
                    "type": "string",
                    "description": "Path to the .jmx file, OR the name of a plan "
                                   "listed by list_test_plans (e.g. 'my_test.jmx')"
                },
                "results_file": {
                    "type": "string",
                    "description": "Optional path for the output .jtl results file"
                }
            },
            "required": ["test_plan"]
        }
    ),

    types.Tool(
        name="list_test_plans",
        description="List all available .jmx test plan files in the test_plans directory.",
        inputSchema={"type": "object", "properties": {}}
    ),

    types.Tool(
        name="list_results",
        description="List all available .jtl result files in the results directory.",
        inputSchema={"type": "object", "properties": {}}
    ),

    types.Tool(
        name="parse_results",
        description=(
            "Parse a JMeter .jtl results file and return a human-readable summary: "
            "total requests, pass/fail counts, error rate, min/avg/max response times, "
            "throughput (req/sec), and per-label breakdowns."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "results_file": {
                    "type": "string",
                    "description": "Path to the .jtl file, OR the name of a file "
                                   "listed by list_results"
                }
            },
            "required": ["results_file"]
        }
    ),

    types.Tool(
        name="compare_runs",
        description=(
            "Compare two JMeter .jtl result files side-by-side. "
            "Shows improvements or regressions in response time, "
            "error rate, and throughput between baseline and new run."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "baseline_file": {
                    "type": "string",
                    "description": "Path or name of the BASELINE (older) .jtl file"
                },
                "new_file": {
                    "type": "string",
                    "description": "Path or name of the NEW (latest) .jtl file"
                }
            },
            "required": ["baseline_file", "new_file"]
        }
    ),
]

# ─────────────────────────────────────────────────────────────────────
# Create the MCP Server instance
# "jmeter-mcp-server" is the name Claude Desktop will see
# ─────────────────────────────────────────────────────────────────────
server = Server("jmeter-mcp-server")


# ─────────────────────────────────────────────────────────────────────
# Handler: list_tools
# Called by Claude Desktop on startup to discover what tools exist.
# Must return the TOOLS list defined above.
# ─────────────────────────────────────────────────────────────────────
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Return all available JMeter tools to the MCP client."""
    return TOOLS


# ─────────────────────────────────────────────────────────────────────
# Handler: call_tool
# Called by Claude Desktop whenever the user (or Claude) wants to
# invoke a specific tool.  We route to the correct function and
# always return a list[types.TextContent].
# ─────────────────────────────────────────────────────────────────────
@server.call_tool()
async def handle_call_tool(
    name: str,                       # tool name chosen by Claude
    arguments: dict                  # arguments from the inputSchema
) -> list[types.TextContent]:
    """
    Route an incoming tool call to the correct handler function,
    wrap the result in TextContent, and return it.
    All errors are caught and returned as readable error messages
    (never crash the server).
    """
    try:
        # ── Route to the right function ──────────────────────────────
        if name == "generate_test_plan":
            result = generate_test_plan(
                description=arguments["description"],
                output_file=arguments.get("output_file")   # optional
            )

        elif name == "run_test":
            result = run_test(
                test_plan=arguments["test_plan"],
                results_file=arguments.get("results_file") # optional
            )

        elif name == "list_test_plans":
            result = list_test_plans()

        elif name == "list_results":
            result = list_results()

        elif name == "parse_results":
            result = parse_results(
                results_file=arguments["results_file"]
            )

        elif name == "compare_runs":
            result = compare_runs(
                baseline_file=arguments["baseline_file"],
                new_file=arguments["new_file"]
            )

        else:
            # Unknown tool — should never happen if TOOLS list is correct
            result = f"❌ Unknown tool: '{name}'"

        # ── Wrap result in MCP TextContent and return ─────────────────
        return [types.TextContent(type="text", text=str(result))]

    except Exception as exc:
        # Capture full Python traceback so Claude can see what went wrong
        error_detail = traceback.format_exc()
        return [types.TextContent(
            type="text",
            text=f"❌ Error in tool '{name}':\n{str(exc)}\n\nDetails:\n{error_detail}"
        )]


# ─────────────────────────────────────────────────────────────────────
# Entry point
# asyncio.run() starts the event loop.
# stdio_server() connects MCP over stdin/stdout (required by Claude Desktop).
# ─────────────────────────────────────────────────────────────────────
async def main():
    """
    Main async function that starts the MCP server.
    
    The server listens on stdin/stdout for MCP protocol messages from Claude Desktop.
    All logging goes to stderr to avoid interfering with the protocol.
    """
    logging.info("JMeter MCP Server initializing...")
    logging.info("Tools available: generate_test_plan, run_test, list_test_plans, list_results, parse_results, compare_runs")
    
    try:
        # Create async streams for stdio-based MCP communication
        async with stdio_server() as (read_stream, write_stream):
            logging.info("MCP stdio transport initialized")
            logging.info("Waiting for client connection...")
            
            # Run the MCP server with proper initialization
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logging.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
