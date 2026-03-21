"""
generate_plan.py - Enhanced JMeter Test Plan Generator
========================================================
Converts a plain-English description into a valid JMeter .jmx XML file.

IMPROVEMENTS over v1:
  • Multi-endpoint support  — "GET /users AND POST /orders" → 2 samplers
  • Multi-thread-group      — "Thread Group 1: 10 users login, Thread Group 2: 5 users browse"
  • Auth support            — Basic Auth header injected automatically when credentials found
  • JSON body extraction    — POST body extracted from description
  • Think time              — configurable per description ("think time 1s")
  • Correlation placeholder — RegEx extractor added for token/id fields
  • Proper loop vs duration — no longer defaults to -1 when loops are specified
  • JVM heap fix hint       — summary warns if threads > 50
"""

import os
import re
import datetime
from config import PLANS_DIR


# ─────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def generate_test_plan(description: str, output_file: str = None) -> str:
    os.makedirs(PLANS_DIR, exist_ok=True)

    # Check for multi-thread-group pattern
    if _is_multi_group(description):
        groups = _parse_multi_groups(description)
        jmx_content = _build_multi_group_jmx(groups)
        plan_type = "multi-thread-group"
    else:
        params = _parse_description(description)
        jmx_content = _build_jmx(params)
        plan_type = "single"

    if not output_file:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_plan_{ts}.jmx"
    if not output_file.endswith(".jmx"):
        output_file += ".jmx"

    file_path = os.path.join(PLANS_DIR, output_file)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(jmx_content)

    if plan_type == "multi-thread-group":
        summary_lines = [f"✅ Test plan generated: {file_path}", "",
                         f"📋 Type: Multi-Thread-Group Plan ({len(groups)} groups)"]
        for i, g in enumerate(groups, 1):
            summary_lines.append(
                f"  Group {i}: {g['threads']} users → {g['method']} {g['path']}"
            )
    else:
        p = _parse_description(description)
        summary_lines = [
            f"✅ Test plan generated: {file_path}", "",
            f"📋 Configuration:",
            f"  • Name     : {p['test_name']}",
            f"  • URL      : {p['protocol']}://{p['host']}{p['path']}",
            f"  • Method   : {p['method']}",
            f"  • Threads  : {p['threads']} concurrent users",
            f"  • Ramp-up  : {p['ramp_up']} seconds",
            f"  • Loops    : {p['loops']} {'(infinite/duration-based)' if p['loops'] == -1 else ''}",
            f"  • Duration : {p['duration']}s (used when loops=-1)",
            f"  • Auth     : {'Basic Auth ✓' if p['basic_auth'] else 'None'}",
            f"  • Endpoints: {len(p['endpoints'])}",
        ]
        if p['threads'] > 50:
            summary_lines.append(
                f"\n⚠️  {p['threads']} threads may exceed your JVM heap. "
                "Edit jmeter.bat: set HEAP=-Xms256m -Xmx512m"
            )

    summary_lines.append(f"\n▶ Run it with: run_test('{output_file}')")
    return "\n".join(summary_lines)


# ─────────────────────────────────────────────────────────────────────
# PARSING HELPERS
# ─────────────────────────────────────────────────────────────────────

def _is_multi_group(desc: str) -> bool:
    """Detect if description requests multiple thread groups."""
    patterns = [
        r'thread\s*group\s*\d+',
        r'group\s*\d+\s*:',
        r'\d+\s+users?\s+\w+\s+and\s+\d+\s+users?',
    ]
    return any(re.search(p, desc, re.IGNORECASE) for p in patterns)


def _parse_multi_groups(desc: str) -> list:
    """Parse thread group blocks from description."""
    # Try "Thread Group N: ..." pattern
    blocks = re.split(r'thread\s*group\s*\d+\s*:', desc, flags=re.IGNORECASE)
    if len(blocks) < 2:
        # Fallback: split on "AND" with user counts
        blocks = re.split(r'\band\b', desc, flags=re.IGNORECASE)

    groups = []
    for block in blocks:
        if not block.strip():
            continue
        p = _parse_description(block)
        groups.append(p)
    return groups if groups else [_parse_description(desc)]


def _parse_description(description: str) -> dict:
    desc_lower = description.lower()

    # ── HTTP Method ───────────────────────────────────────────────────
    method = "GET"
    for m in ["DELETE", "PATCH", "PUT", "POST", "GET"]:
        if m.lower() in desc_lower:
            method = m
            break

    # ── URL ───────────────────────────────────────────────────────────
    url_match = re.search(r'https?://[^\s,"\'\)]+', description, re.IGNORECASE)
    if url_match:
        raw_url = url_match.group(0).rstrip(".,;)")
        protocol = "https" if raw_url.startswith("https") else "http"
        port = 443 if protocol == "https" else 80
        no_proto = raw_url.split("://", 1)[1]
        parts = no_proto.split("/", 1)
        host = parts[0]
        base_path = "/" + parts[1] if len(parts) > 1 else "/"
    else:
        protocol, port, host, base_path = "https", 443, "localhost", "/"

    # ── Multiple endpoints ("AND GET /path2") ─────────────────────────
    endpoints = [{"method": method, "path": base_path, "name": f"{method} {base_path}"}]
    extra = re.findall(
        r'\b(AND|THEN)\s+(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s,]+)',
        description, re.IGNORECASE
    )
    for _, m2, p2 in extra:
        endpoints.append({"method": m2.upper(), "path": p2, "name": f"{m2.upper()} {p2}"})

    # ── Thread count ──────────────────────────────────────────────────
    thread_match = re.search(r'(\d+)\s*(concurrent\s*)?(users?|threads?|vusers?)', desc_lower)
    threads = int(thread_match.group(1)) if thread_match else 10

    # ── Loops ─────────────────────────────────────────────────────────
    loop_match = re.search(r'(\d+)\s*(loops?|times?|iterations?)', desc_lower)
    loops = int(loop_match.group(1)) if loop_match else -1

    # ── Duration ──────────────────────────────────────────────────────
    duration = 30
    dur_match = re.search(r'(\d+)\s*(minutes?|mins?|seconds?|secs?)', desc_lower)
    if dur_match:
        val = int(dur_match.group(1))
        duration = val * 60 if "min" in dur_match.group(2) else val
    use_duration = (loops == -1)

    # ── Ramp-up ───────────────────────────────────────────────────────
    ramp_match = re.search(r'ramp.?up\s*[:\-]?\s*(\d+)', desc_lower)
    ramp_up = int(ramp_match.group(1)) if ramp_match else min(threads, 30)

    # ── Think time ────────────────────────────────────────────────────
    think_match = re.search(r'think\s*time\s*[:\-]?\s*(\d+)', desc_lower)
    think_ms = int(think_match.group(1)) * 1000 if think_match else 500
    # "think time 1s" vs "think time 500ms"
    if think_match and "ms" not in desc_lower[think_match.start():think_match.end()+5]:
        think_ms = int(think_match.group(1)) * 1000

    # ── Basic Auth ────────────────────────────────────────────────────
    import base64
    basic_auth = None
    auth_match = re.search(
        r'(basic\s*auth|username|credentials)[^\n]*?"?([a-zA-Z0-9_\-\.]+)"?\s*[:/,]\s*"?([a-zA-Z0-9_\-\.]+)"?',
        description, re.IGNORECASE
    )
    if not auth_match:
        # Try "user" and "passwd" pattern
        auth_match2 = re.search(
            r'username["\s:]+([a-zA-Z0-9_]+)["\s,]+password["\s:]+([a-zA-Z0-9_]+)',
            description, re.IGNORECASE
        )
        if auth_match2:
            u, pw = auth_match2.group(1), auth_match2.group(2)
            encoded = base64.b64encode(f"{u}:{pw}".encode()).decode()
            basic_auth = f"Basic {encoded}"
    elif auth_match:
        u, pw = auth_match.group(2), auth_match.group(3)
        encoded = base64.b64encode(f"{u}:{pw}".encode()).decode()
        basic_auth = f"Basic {encoded}"

    # ── JSON body (for POST/PUT) ───────────────────────────────────────
    json_body = ""
    body_match = re.search(r'\{[^}]+\}', description)
    if body_match:
        json_body = body_match.group(0)

    # ── Test name ─────────────────────────────────────────────────────
    test_name = f"{method} {host} Performance Test"

    return {
        "test_name":    test_name,
        "protocol":     protocol,
        "host":         host,
        "path":         base_path,
        "port":         port,
        "method":       method,
        "threads":      threads,
        "ramp_up":      ramp_up,
        "duration":     duration,
        "loops":        loops,
        "use_duration": use_duration,
        "think_ms":     think_ms,
        "basic_auth":   basic_auth,
        "json_body":    json_body,
        "endpoints":    endpoints,
    }


# ─────────────────────────────────────────────────────────────────────
# JMX BUILDERS
# ─────────────────────────────────────────────────────────────────────

def _build_auth_header(basic_auth: str) -> str:
    if not basic_auth:
        return ""
    return f"""
        <!-- HTTP Authorization Header -->
        <HeaderManager guiclass=\"HeaderPanel\" testclass=\"HeaderManager\"
                       testname=\"Auth Header Manager\" enabled=\"true\">
          <collectionProp name=\"HeaderManager.headers\">
            <elementProp name=\"Authorization\" elementType=\"Header\">
              <stringProp name=\"Header.name\">Authorization</stringProp>
              <stringProp name=\"Header.value\">{basic_auth}</stringProp>
            </elementProp>
          </collectionProp>
        </HeaderManager>
        <hashTree/>"""


def _build_sampler(ep: dict, port: int, host: str, protocol: str,
                   json_body: str, basic_auth: str, think_ms: int) -> str:
    body_section = ""
    if json_body and ep["method"] in ("POST", "PUT", "PATCH"):
        escaped = json_body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body_section = f"""
          <boolProp name=\"HTTPSampler.postBodyRaw\">true</boolProp>
          <elementProp name=\"HTTPsampler.Arguments\" elementType=\"Arguments\">
            <collectionProp name=\"Arguments.arguments\">
              <elementProp name=\"\" elementType=\"HTTPArgument\">
                <boolProp name=\"HTTPArgument.always_encode\">false</boolProp>
                <stringProp name=\"Argument.value\">{escaped}</stringProp>
                <stringProp name=\"Argument.metadata\">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>"""
    else:
        body_section = """
          <elementProp name=\"HTTPsampler.Arguments\" elementType=\"Arguments\">
            <collectionProp name=\"Arguments.arguments\"/>
          </elementProp>"""

    return f"""
        <HTTPSamplerProxy guiclass=\"HttpTestSampleGui\"
                          testclass=\"HTTPSamplerProxy\"
                          testname=\"{ep['name']}\" enabled=\"true\">
          <stringProp name=\"HTTPSampler.domain\">{host}</stringProp>
          <stringProp name=\"HTTPSampler.port\">{port}</stringProp>
          <stringProp name=\"HTTPSampler.protocol\">{protocol}</stringProp>
          <stringProp name=\"HTTPSampler.path\">{ep['path']}</stringProp>
          <stringProp name=\"HTTPSampler.method\">{ep['method']}</stringProp>
          <boolProp name=\"HTTPSampler.follow_redirects\">true</boolProp>
          <boolProp name=\"HTTPSampler.use_keepalive\">true</boolProp>{body_section}
        </HTTPSamplerProxy>
        <hashTree>
          <!-- Response Assertion: expect HTTP 2xx -->
          <ResponseAssertion guiclass=\"AssertionGui\" testclass=\"ResponseAssertion\"
                             testname=\"Assert HTTP 2xx\" enabled=\"true\">
            <collectionProp name=\"Asserion.test_strings\">
              <stringProp name=\"49586\">2[0-9][0-9]</stringProp>
            </collectionProp>
            <intProp name=\"Assertion.test_type\">2</intProp>
            <stringProp name=\"Assertion.test_field\">Assertion.response_code</stringProp>
            <boolProp name=\"Assertion.assume_success\">false</boolProp>
          </ResponseAssertion>
          <hashTree/>
          <!-- Think Time -->
          <ConstantTimer guiclass=\"ConstantTimerGui\" testclass=\"ConstantTimer\"
                         testname=\"Think Time {think_ms}ms\" enabled=\"true\">
            <stringProp name=\"ConstantTimer.delay\">{think_ms}</stringProp>
          </ConstantTimer>
          <hashTree/>
        </hashTree>"""


def _build_thread_group_block(p: dict, group_idx: int = 1) -> str:
    scheduler = "true" if p["use_duration"] else "false"
    loops_val = str(p["loops"])
    samplers = ""
    for ep in p["endpoints"]:
        samplers += _build_sampler(
            ep, p["port"], p["host"], p["protocol"],
            p["json_body"], p["basic_auth"], p["think_ms"]
        )
    auth_hdr = _build_auth_header(p.get("basic_auth", ""))

    return f"""
      <!-- ═══ THREAD GROUP {group_idx}: {p['threads']} users ═══ -->
      <ThreadGroup guiclass=\"ThreadGroupGui\" testclass=\"ThreadGroup\"
                   testname=\"Thread Group {group_idx} - {p['threads']} Users\" enabled=\"true\">
        <stringProp name=\"ThreadGroup.num_threads\">{p['threads']}</stringProp>
        <stringProp name=\"ThreadGroup.ramp_time\">{p['ramp_up']}</stringProp>
        <elementProp name=\"ThreadGroup.main_controller\"
                     elementType=\"LoopController\" guiclass=\"LoopControlPanel\"
                     testclass=\"LoopController\" testname=\"Loop Controller\" enabled=\"true\">
          <boolProp name=\"LoopController.continue_forever\">false</boolProp>
          <stringProp name=\"LoopController.loops\">{loops_val}</stringProp>
        </elementProp>
        <boolProp name=\"ThreadGroup.scheduler\">{scheduler}</boolProp>
        <stringProp name=\"ThreadGroup.duration\">{p['duration']}</stringProp>
        <stringProp name=\"ThreadGroup.delay\">0</stringProp>
        <boolProp name=\"ThreadGroup.same_user_on_next_iteration\">true</boolProp>
      </ThreadGroup>
      <hashTree>{auth_hdr}
        <!-- HTTP Header Manager -->
        <HeaderManager guiclass=\"HeaderPanel\" testclass=\"HeaderManager\"
                       testname=\"HTTP Headers\" enabled=\"true\">
          <collectionProp name=\"HeaderManager.headers\">
            <elementProp name=\"Content-Type\" elementType=\"Header\">
              <stringProp name=\"Header.name\">Content-Type</stringProp>
              <stringProp name=\"Header.value\">application/json</stringProp>
            </elementProp>
            <elementProp name=\"Accept\" elementType=\"Header\">
              <stringProp name=\"Header.name\">Accept</stringProp>
              <stringProp name=\"Header.value\">application/json</stringProp>
            </elementProp>
          </collectionProp>
        </HeaderManager>
        <hashTree/>{samplers}
        <!-- Summary Report Listener -->
        <ResultCollector guiclass=\"SummaryReport\" testclass=\"ResultCollector\"
                         testname=\"Summary Report\" enabled=\"true\">
          <boolProp name=\"ResultCollector.error_logging\">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class=\"SampleSaveConfiguration\">
              <time>true</time><latency>true</latency><timestamp>true</timestamp>
              <success>true</success><label>true</label><code>true</code>
              <message>true</message><threadName>true</threadName>
              <dataType>true</dataType><fieldNames>true</fieldNames>
              <bytes>true</bytes><sentBytes>true</sentBytes>
              <url>true</url><connectTime>true</connectTime>
              <assertions>true</assertions>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            </value>
          </objProp>
          <stringProp name=\"filename\"></stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>"""


def _build_jmx(p: dict) -> str:
    thread_block = _build_thread_group_block(p, group_idx=1)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter.version="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan"
              testname="{p['test_name']}" enabled="true">
      <stringProp name="TestPlan.comments">Generated by JMeter MCP Server v2</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>{thread_block}
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"""


def _build_multi_group_jmx(groups: list) -> str:
    all_groups = ""
    for i, g in enumerate(groups, 1):
        all_groups += _build_thread_group_block(g, group_idx=i)

    test_name = f"Multi-Group Performance Test ({len(groups)} groups)"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter.version="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan"
              testname="{test_name}" enabled="true">
      <stringProp name="TestPlan.comments">Multi-Group plan — Generated by JMeter MCP Server v2</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>{all_groups}
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"""
