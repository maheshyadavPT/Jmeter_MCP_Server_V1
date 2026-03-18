"""
tools/generate_plan.py
======================
Converts a plain-English description into a valid JMeter .jmx XML file
and saves it inside the test_plans/ directory.

How it works
────────────
1. Parse the description with regex to extract:
   - URL / host / path
   - HTTP method (GET, POST, PUT, DELETE)
   - Number of users (threads)
   - Duration or loop count
   - Ramp-up time
2. Build JMX XML as a Python string (no external XML library needed).
3. Write the file to test_plans/<name>.jmx.
4. Return a human-readable summary string.
"""

import os           # file path operations
import re           # regular expressions for parsing description
import datetime     # timestamp for default filename
from config import PLANS_DIR


def generate_test_plan(description: str, output_file: str = None) -> str:
    """
    Parse a plain-English 'description' and produce a .jmx test plan.

    Parameters
    ----------
    description : str
        Natural language, e.g.:
        "Test POST https://api.example.com/login with 50 users for 2 minutes"
    output_file : str, optional
        Filename for the .jmx (without directory).  Auto-generated if None.

    Returns
    -------
    str
        Summary message with the file path and parsed parameters.
    """

    # ── Ensure the output directory exists ───────────────────────────
    os.makedirs(PLANS_DIR, exist_ok=True)

    # ── Parse the description ─────────────────────────────────────────
    params = _parse_description(description)

    # ── Build the JMX XML content ─────────────────────────────────────
    jmx_content = _build_jmx(params)

    # ── Decide on the filename ────────────────────────────────────────
    if not output_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_plan_{timestamp}.jmx"

    # Ensure it ends with .jmx
    if not output_file.endswith(".jmx"):
        output_file += ".jmx"

    file_path = os.path.join(PLANS_DIR, output_file)

    # ── Write to disk ─────────────────────────────────────────────────
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(jmx_content)

    # ── Return readable summary ───────────────────────────────────────
    return (
        f"✅ Test plan generated: {file_path}\n\n"
        f"📋 Configuration:\n"
        f"  • Name        : {params['test_name']}\n"
        f"  • URL         : {params['protocol']}://{params['host']}{params['path']}\n"
        f"  • Method      : {params['method']}\n"
        f"  • Threads     : {params['threads']} concurrent users\n"
        f"  • Ramp-up     : {params['ramp_up']} seconds\n"
        f"  • Duration    : {params['duration']} seconds "
        f"({'time-based' if params['use_duration'] else 'loop-based'})\n"
        f"  • Loops       : {params['loops']}\n\n"
        f"▶ Run it with: run_test('{output_file}')"
    )


# ─────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────────────

def _parse_description(description: str) -> dict:
    """
    Extract test parameters from the natural-language description.
    Falls back to safe defaults when a value is not found.
    """
    desc_lower = description.lower()

    # ── HTTP Method ───────────────────────────────────────────────────
    method = "GET"
    for m in ["POST", "PUT", "DELETE", "PATCH", "GET"]:
        if m.lower() in desc_lower:
            method = m
            break

    # ── URL (look for http:// or https://) ───────────────────────────
    url_match = re.search(r'https?://[^\s,]+', description, re.IGNORECASE)
    if url_match:
        raw_url = url_match.group(0).rstrip(".,;)")
        # Split into protocol, host, path
        if raw_url.startswith("https"):
            protocol = "https"
            port = 443
        else:
            protocol = "http"
            port = 80

        no_proto = raw_url.split("://", 1)[1]   # strip protocol
        parts = no_proto.split("/", 1)
        host = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
    else:
        # Default values when no URL found
        protocol = "https"
        host = "localhost"
        path = "/"
        port = 443

    # ── Number of concurrent users / threads ─────────────────────────
    thread_match = re.search(r'(\d+)\s*(concurrent\s*)?(users?|threads?|vusers?)', desc_lower)
    threads = int(thread_match.group(1)) if thread_match else 10

    # ── Duration in seconds ───────────────────────────────────────────
    duration = 60          # default 60 seconds
    use_duration = False

    dur_match = re.search(r'(\d+)\s*(minutes?|mins?|seconds?|secs?)', desc_lower)
    if dur_match:
        value = int(dur_match.group(1))
        unit = dur_match.group(2)
        duration = value * 60 if "min" in unit else value
        use_duration = True

    # ── Loop count ────────────────────────────────────────────────────
    loop_match = re.search(r'(\d+)\s*(loops?|times?|iterations?)', desc_lower)
    loops = int(loop_match.group(1)) if loop_match else -1  # -1 = forever when duration-based

    # ── Ramp-up time (how long to reach full thread count) ────────────
    ramp_match = re.search(r'ramp.?up\s*(\d+)', desc_lower)
    ramp_up = int(ramp_match.group(1)) if ramp_match else min(threads, 30)

    # ── Derive a human-readable test name ────────────────────────────
    test_name = f"{method} {host} Performance Test"

    return {
        "test_name": test_name,
        "protocol":  protocol,
        "host":      host,
        "path":      path,
        "port":      port,
        "method":    method,
        "threads":   threads,
        "ramp_up":   ramp_up,
        "duration":  duration,
        "loops":     loops if not use_duration else -1,
        "use_duration": use_duration,
    }


def _build_jmx(p: dict) -> str:
    """
    Build the complete JMX XML string from the parsed parameters dict.

    JMX structure:
      jmeterTestPlan
        └─ hashTree
             └─ TestPlan
                  └─ hashTree
                       ├─ ThreadGroup        ← defines virtual users
                       │    └─ hashTree
                       │         ├─ HTTPSamplerProxy   ← the actual HTTP request
                       │         │    └─ hashTree
                       │         ├─ ResponseAssertion  ← check for HTTP 200
                       │         │    └─ hashTree
                       │         └─ ResultCollector    ← saves .jtl file
                       │              └─ hashTree
                       └─ ...
    """

    # Use duration-based scheduler OR loop count
    scheduler_enabled = "true" if p["use_duration"] else "false"
    loops_value = str(p["loops"])

    jmx = f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter.version="5.6">
  <hashTree>

    <!-- ═══════════════════════════════════════════════
         TEST PLAN
         The root container for all test elements.
         serialize_threadgroups=false → run groups in parallel
    ════════════════════════════════════════════════ -->
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan"
              testname="{p['test_name']}" enabled="true">
      <stringProp name="TestPlan.comments">Generated by JMeter MCP Server</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.arguments" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>

    <hashTree>

      <!-- ═══════════════════════════════════════════════
           THREAD GROUP
           Simulates virtual users (threads).
           num_threads  = concurrent users
           ramp_time    = seconds to reach full user count
           loops / scheduler control how long the test runs
      ════════════════════════════════════════════════ -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup"
                   testname="Users - {p['threads']} Concurrent" enabled="true">

        <!-- How many virtual users to simulate -->
        <stringProp name="ThreadGroup.num_threads">{p['threads']}</stringProp>

        <!-- Seconds to ramp up to full thread count -->
        <stringProp name="ThreadGroup.ramp_time">{p['ramp_up']}</stringProp>

        <!-- Loop count: -1 means loop forever (use with scheduler) -->
        <stringProp name="ThreadGroup.num_threads">{p['threads']}</stringProp>

        <elementProp name="ThreadGroup.main_controller"
                     elementType="LoopController" guiclass="LoopControlPanel"
                     testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">{loops_value}</stringProp>
        </elementProp>

        <!-- Scheduler: when true, 'duration' controls test length in seconds -->
        <boolProp name="ThreadGroup.scheduler">{scheduler_enabled}</boolProp>
        <stringProp name="ThreadGroup.duration">{p['duration']}</stringProp>
        <stringProp name="ThreadGroup.delay">0</stringProp>

      </ThreadGroup>

      <hashTree>

        <!-- ═══════════════════════════════════════════════
             HTTP REQUEST SAMPLER
             Sends the actual HTTP/HTTPS request.
        ════════════════════════════════════════════════ -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui"
                          testclass="HTTPSamplerProxy"
                          testname="{p['method']} {p['path']}" enabled="true">
          <stringProp name="HTTPSampler.domain">{p['host']}</stringProp>
          <stringProp name="HTTPSampler.port">{p['port']}</stringProp>
          <stringProp name="HTTPSampler.protocol">{p['protocol']}</stringProp>
          <stringProp name="HTTPSampler.path">{p['path']}</stringProp>
          <stringProp name="HTTPSampler.method">{p['method']}</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>

        <!-- ═══════════════════════════════════════════════
             HTTP HEADER MANAGER
             Adds common headers to every request.
        ════════════════════════════════════════════════ -->
        <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager"
                       testname="HTTP Header Manager" enabled="true">
          <collectionProp name="HeaderManager.headers">
            <elementProp name="Content-Type" elementType="Header">
              <stringProp name="Header.name">Content-Type</stringProp>
              <stringProp name="Header.value">application/json</stringProp>
            </elementProp>
            <elementProp name="Accept" elementType="Header">
              <stringProp name="Header.name">Accept</stringProp>
              <stringProp name="Header.value">application/json</stringProp>
            </elementProp>
          </collectionProp>
        </HeaderManager>
        <hashTree/>

        <!-- ═══════════════════════════════════════════════
             RESPONSE ASSERTION
             Marks a sample as FAILED if the HTTP status
             code is not in the 2xx range.
        ════════════════════════════════════════════════ -->
        <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion"
                           testname="Assert HTTP 2xx" enabled="true">
          <collectionProp name="Asserion.test_strings">
            <stringProp name="49586">2[0-9][0-9]</stringProp>
          </collectionProp>
          <!-- TEST_TYPE 2 = "matches" (regex); 8 = "contains" -->
          <intProp name="Assertion.test_type">2</intProp>
          <!-- RESPONSE_CODE = check the HTTP status code field -->
          <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
          <boolProp name="Assertion.assume_success">false</boolProp>
        </ResponseAssertion>
        <hashTree/>

        <!-- ═══════════════════════════════════════════════
             CONSTANT TIMER  (think time)
             Adds a 500 ms pause between requests to
             simulate realistic user think time.
        ════════════════════════════════════════════════ -->
        <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer"
                       testname="Think Time 500ms" enabled="true">
          <stringProp name="ConstantTimer.delay">500</stringProp>
        </ConstantTimer>
        <hashTree/>

        <!-- ═══════════════════════════════════════════════
             SUMMARY REPORT listener
             Writes results to a .jtl CSV file.
             filename is empty here; supplied at runtime
             via -l flag or hard-coded path below.
        ════════════════════════════════════════════════ -->
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector"
                         testname="Summary Report" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>

      </hashTree><!-- end ThreadGroup hashTree -->

    </hashTree><!-- end TestPlan hashTree -->

  </hashTree><!-- end root hashTree -->
</jmeterTestPlan>
"""
    return jmx
