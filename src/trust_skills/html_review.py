"""Deliberately bounded static HTML checks, not an accessible-name implementation."""

from collections import Counter
from html.parser import HTMLParser

from .core import finding, report

VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.nodes = []
        self.stack = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = {
            "tag": tag,
            "attrs": dict(attrs),
            "line": self.getpos()[0],
            "text": "",
            "parents": list(self.stack),
        }
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data


def review(text: str, skill="accessible-html-review") -> dict:
    doc = Document(text)
    out = []
    by_id = {n["attrs"]["id"]: n for n in doc.nodes if n["attrs"].get("id")}
    labels = {
        n["attrs"]["for"]
        for n in doc.nodes
        if n["tag"] == "label" and n["text"].strip() and n["attrs"].get("for")
    }

    def add(code, n, message, ref):
        out.append(finding(code, f"line:{n['line']}", message, ref))

    def named(n):
        a = n["attrs"]
        refs = (a.get("aria-labelledby") or "").split()
        return bool(
            (a.get("aria-label") or "").strip()
            or (refs and all(r in by_id and by_id[r]["text"].strip() for r in refs))
        )

    if skill == "accessible-html-review":
        roots = [n for n in doc.nodes if n["tag"] == "html"]
        if not roots or not (roots[0]["attrs"].get("lang") or "").strip():
            out.append(
                finding(
                    "HTML_LANG",
                    "document",
                    "Declare the page language; verify its correctness manually.",
                    "wcag22:3.1.1",
                )
            )
        if not any(n["tag"] == "title" and n["text"].strip() for n in doc.nodes):
            out.append(
                finding(
                    "HTML_TITLE",
                    "document",
                    "Provide a descriptive document title.",
                    "wcag22:2.4.2",
                )
            )
    for n in doc.nodes:
        a, tag = n["attrs"], n["tag"]
        if skill == "accessible-html-review":
            if tag == "img" and "alt" not in a:
                add(
                    "IMAGE_ALT",
                    n,
                    "Image has no alt attribute; determine its purpose before writing text.",
                    "wcag22:1.1.1",
                )
            if tag in {"button", "a"} and not named(n) and not n["text"].strip():
                if not any(
                    child["tag"] == "img"
                    and child["attrs"].get("alt")
                    and any(p is n for p in child["parents"])
                    for child in doc.nodes
                ):
                    add(
                        "CONTROL_NAME",
                        n,
                        "No static text name found; inspect the computed accessible name.",
                        "wcag22:4.1.2",
                    )
        if skill == "accessible-forms-review" and tag in {"input", "select", "textarea"}:
            kind = (a.get("type") or "text").lower()
            exempt = tag == "input" and kind in {"hidden", "submit", "reset", "button", "image"}
            wrapped = any(p["tag"] == "label" and p["text"].strip() for p in n["parents"])
            if not exempt and not named(n) and a.get("id") not in labels and not wrapped:
                add(
                    "FORM_LABEL",
                    n,
                    "Control needs a programmatically associated label; placeholder is insufficient.",
                    "wcag22:1.3.1,3.3.2",
                )
            if kind == "image" and not (a.get("alt") or "").strip():
                add(
                    "FORM_IMAGE_NAME",
                    n,
                    "Image submit control needs an accessible name.",
                    "wcag22:1.1.1",
                )
        if skill in {"accessible-html-review", "aria-pattern-review", "accessible-forms-review"}:
            for attr in ("aria-labelledby", "aria-describedby", "aria-controls"):
                if a.get(attr) and any(x not in by_id for x in a[attr].split()):
                    add(
                        "ARIA_REFERENCE",
                        n,
                        f"{attr} contains an unresolved ID reference.",
                        "wai-aria12",
                    )
        if skill == "aria-pattern-review":
            role = a.get("role")
            checked_values = {"true", "false", "mixed"} if role == "checkbox" else {"true", "false"}
            if role in {"checkbox", "switch"} and a.get("aria-checked") not in checked_values:
                add(
                    "ARIA_STATE",
                    n,
                    "Check required checked state and role-specific allowed values.",
                    "wai-aria12",
                )
            if role == "slider" and not all(a.get(x) for x in ("aria-valuenow",)):
                add(
                    "ARIA_VALUE",
                    n,
                    "Slider requires its current value; verify range and keyboard behavior.",
                    "wai-aria12",
                )
            if role == "dialog" and not named(n):
                add(
                    "DIALOG_NAME",
                    n,
                    "Dialog needs an accessible name and manual focus management testing.",
                    "apg",
                )
        if skill == "keyboard-navigation-test":
            try:
                positive = int(a.get("tabindex", "0")) > 0
            except (ValueError, TypeError):
                positive = False
                add("TABINDEX_INVALID", n, "tabindex must be an integer.", "apg")
            if positive:
                add(
                    "TABINDEX_POSITIVE",
                    n,
                    "Positive tabindex may create an unexpected focus sequence.",
                    "wcag22:2.4.3",
                )
            if "onclick" in a and tag not in {
                "button",
                "a",
                "input",
                "select",
                "textarea",
                "summary",
            }:
                add(
                    "CLICK_ONLY",
                    n,
                    "Custom clickable element needs equivalent keyboard operation and semantics.",
                    "wcag22:2.1.1",
                )
    if skill in {"accessible-html-review", "aria-pattern-review", "accessible-forms-review"}:
        ids = Counter(n["attrs"]["id"] for n in doc.nodes if n["attrs"].get("id"))
        for _id, count in sorted(ids.items()):
            if count > 1:
                out.append(
                    finding(
                        "DUPLICATE_ID",
                        "document",
                        f"ID occurs {count} times; references may be ambiguous.",
                        "wai-aria12",
                    )
                )
    manual = {
        "accessible-html-review": [
            "Inspect computed names and semantic structure",
            "Verify alt text purpose",
            "Test zoom, reflow, contrast, and assistive technology",
        ],
        "accessible-forms-review": [
            "Trigger errors and verify error association and recovery",
            "Review instructions and autocomplete purpose",
            "Test required states with a screen reader",
        ],
        "aria-pattern-review": [
            "Choose the applicable APG pattern",
            "Test roles, states, ownership, and dynamic announcements",
            "Verify pattern keyboard interaction",
        ],
        "keyboard-navigation-test": [
            "Tab and Shift+Tab through each workflow",
            "Operate controls using Enter, Space, arrows, Escape as appropriate",
            "Record focus visibility, obscuring, traps, and focus restoration",
        ],
    }
    return report(
        skill,
        out,
        {"elements_reviewed": len(doc.nodes), "manual_checks": manual[skill]},
        [
            "Static HTML heuristics only; no CSS, JavaScript, browser DOM, or full accessible-name computation.",
            "No findings means only that these bounded checks found nothing; it does not mean WCAG conformance.",
        ],
    )
