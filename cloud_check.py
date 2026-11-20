#!/usr/bin/env python3
"""
One-shot cloud check for TCU Class Search (run by GitHub Actions every ~5 min).

Checks ACCT 20653 sections 080/081 (Spring 2027). When a section goes from full
to open, sends an ntfy push to the topic in the NTFY_TOPIC environment variable
(stored as a GitHub secret, so it never appears in this public repo).

state.json remembers which sections were already open, so you get one alert per
opening instead of one every 5 minutes. The workflow commits it when it changes.
"""

import html
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://classes.tcu.edu/"
TERM_CODE = "4273"          # "27 Spring"
SUBJECT = "ACCT"
COURSE = "20653"
SECTIONS = {"080", "081"}
STATE_FILE = Path(__file__).with_name("state.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) seat-watcher"


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def fetch_sections():
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [("User-Agent", UA)]
    first = opener.open(URL, timeout=30).read().decode("utf-8", "replace")
    form = {}
    for tag in re.findall(r'<input[^>]+type="hidden"[^>]*>', first, re.I):
        name = re.search(r'name="([^"]+)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if name:
            form[name.group(1)] = html.unescape(value.group(1)) if value else ""
    form.update({
        "ddlTerm": TERM_CODE, "ddlSession": "ANY", "ddlLocation": "ANY",
        "ddlSubject": SUBJECT, "txtCrsNumber": COURSE, "txtSection": "",
        "ddlAttribute": "ANY", "ddlLevel": "ANY", "rbStatus": "rbStatusAny",
        "ddlDay": "ANY", "ddlStartTime": "ANY", "ddlEndtime": "2000",
        "btnSearch": "Search",
    })
    page = opener.open(URL, data=urllib.parse.urlencode(form).encode(),
                       timeout=30).read().decode("utf-8", "replace")
    table = re.search(r'<table class="results".*?</table>', page, re.S | re.I)
    if not table:
        raise RuntimeError("Results table not found (site layout may have changed).")

    results = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S | re.I):
        cells = [strip_tags(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]
        if len(cells) < 12:
            continue
        section = cells[3].split("\n")[0].strip()
        if section not in SECTIONS:
            continue
        nums = re.findall(r"\d+", cells[11])
        enr, cap = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (None, None)
        results[section] = {"class_nbr": cells[0], "status": cells[10],
                            "enrolled": enr, "max": cap,
                            "when": cells[9].replace("\n", " ")}
    return results


def is_open(info):
    if info["status"].lower() == "open":
        return True
    return info["enrolled"] is not None and info["enrolled"] < info["max"]


def push(title, message, priority="urgent", tags="rotating_light"):
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC not set; skipping push.")
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{urllib.parse.quote(topic)}", data=message.encode(),
        headers={"Title": title, "Priority": priority, "Tags": tags})
    urllib.request.urlopen(req, timeout=15)


def main():
    if "--test-push" in sys.argv:
        push("TCU cloud watcher test",
             "Test alert: the cloud watcher (GitHub Actions) can reach your phone.",
             priority="default", tags="white_check_mark")
        print("Test push sent.")

    prev_open = set(json.loads(STATE_FILE.read_text())) if STATE_FILE.exists() else set()
    sections = fetch_sections()
    now_open = set()
    for sec in sorted(sections):
        info = sections[sec]
        print(f"Sec {sec} (#{info['class_nbr']}, {info['when']}): "
              f"{info['status']} {info['enrolled']}/{info['max']}")
        if is_open(info):
            now_open.add(sec)
            if sec not in prev_open:
                free = info["max"] - info["enrolled"] if info["enrolled"] is not None else "?"
                push(f"ACCT {COURSE}-{sec} has a seat!",
                     f"Class #{info['class_nbr']} ({info['when']}): "
                     f"{info['enrolled']}/{info['max']}, {free} open. Register now!")
                print(f"  -> alert sent for {sec}")
    if not sections:
        print("Sections not found in results.")
    STATE_FILE.write_text(json.dumps(sorted(now_open)) + "\n")


if __name__ == "__main__":
    main()
