"""
fix_monitor_cell.py - Replace broken _d4_load_log with inner-function pattern.
Usage: python3 fix_monitor_cell.py path/to/aces_monitor.py
"""
import sys
import re
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text(encoding='utf-8')

# Find the entire _d4_load_log cell — from @app.cell to the next @app.cell
pattern = re.compile(
    r'@app\.cell\s*\ndef _d4_load_log\(pl\):.*?(?=@app\.cell|@app\.function)',
    re.DOTALL
)

fixed_cell = '''@app.cell
def _d4_load_log(pl):
    """Load cost_audit.log — ADR-009 + legacy. Inner function avoids top-level return."""
    import re as _re
    from pathlib import Path as _Path

    # Try WSL2 UNC path (Windows Marimo -> WSL2 log), fallback to native
    _wsl_log = _Path("\\\\\\\\wsl$\\\\Ubuntu\\\\home\\\\pheller\\\\.config\\\\fabric\\\\cost_audit.log")
    _native  = _Path.home() / ".config" / "fabric" / "cost_audit.log"
    _log     = _wsl_log if _wsl_log.exists() else _native

    _TIERS = {
        "principal_system_architect.system.md": "tier_0_elicitation",
        "requirements_identity.system.md":      "tier_0_elicitation",
        "requirements_mission.system.md":       "tier_0_elicitation",
        "requirements_authorities.system.md":   "tier_0_elicitation",
        "requirements_lifecycle.system.md":     "tier_0_elicitation",
        "requirements_cost_model.system.md":    "tier_0_elicitation",
        "requirements_data.system.md":          "tier_0_elicitation",
        "skill.system.md":                      "tier_1_source",
        "transformer.yaml.system.md":           "tier_1_source",
        "transformer.toon.system.md":           "tier_1_source",
        "skill.system.yaml":                    "tier_2_derived",
        "skill.system.toon":                    "tier_2_derived",
        "session.total":                        "tier_4_session",
    }

    def _tier(a):
        if a in _TIERS: return _TIERS[a]
        for p in ("fabric_stitch.", "langgraph.", "hook."): 
            if a.startswith(p): return "tier_3_execution"
        return "tier_unknown"

    def _adr(parts):
        if len(parts) < 6: return False
        return bool(_re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            parts[2].strip(), _re.I))

    def _i(v):
        try: return int(v.strip())
        except: return 0

    def _f(v):
        try: return float(v.strip())
        except: return 0.0

    def _run():
        if not _log.exists():
            return pl.DataFrame(), str(_log), 0, f"No log at {_log}"
        rows, skip = [], 0
        try:
            with open(_log) as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln or ln.startswith("#"): continue
                    pts = ln.split(" | ")
                    if len(pts) < 2: skip += 1; continue
                    try:
                        if _adr(pts):
                            while len(pts) < 16: pts.append("")
                            rows.append({
                                "timestamp":    pts[0].strip("[]"),
                                "component":    pts[1].strip(),
                                "run_id":       pts[2].strip(),
                                "skill":        pts[3].strip(),
                                "artifact":     pts[4].strip(),
                                "vendor":       pts[5].strip(),
                                "model":        pts[6].strip(),
                                "tokens_in":    _i(pts[7]),
                                "tokens_out":   _i(pts[8]),
                                "cost_in":      _f(pts[9]),
                                "cost_out":     _f(pts[10]),
                                "cost_total":   _f(pts[11]),
                                "elapsed_ms":   _i(pts[12]),
                                "env":          pts[13].strip(),
                                "upstream_id":  pts[14].strip() if len(pts) > 14 else "",
                                "notes":        pts[15].strip() if len(pts) > 15 else "",
                                "artifact_tier": _tier(pts[4].strip()),
                            })
                        else:
                            raw = " | ".join(pts)
                            def ex(pat, d=""):
                                m = _re.search(pat, raw)
                                return m.group(1) if m else d
                            rows.append({
                                "timestamp":    pts[0].strip("[]"),
                                "component":    pts[1].strip() if len(pts) > 1 else "unknown",
                                "run_id":       "legacy",
                                "skill":        ex(r"skill=([^\s|]+)"),
                                "artifact":     "session.total",
                                "vendor":       ex(r"vendor=([^\s|]+)"),
                                "model":        ex(r"model=([^\s|]+)"),
                                "tokens_in":    _i(ex(r"tokens_in=(\\d+)", "0")),
                                "tokens_out":   _i(ex(r"tokens_out=(\\d+)", "0")),
                                "cost_in":      0.0,
                                "cost_out":     0.0,
                                "cost_total":   _f(ex(r"cost=\\$?([0-9.]+)", "0.0")),
                                "elapsed_ms":   _i(ex(r"elapsed=(\\d+)ms", "0")),
                                "env":          ex(r"env=([^\s|]+)", "dev"),
                                "upstream_id":  "",
                                "notes":        "legacy_format",
                                "artifact_tier": "tier_4_session",
                            })
                    except Exception:
                        skip += 1
        except Exception as e:
            return pl.DataFrame(), str(_log), 0, str(e)
        if rows:
            df = pl.DataFrame(rows).with_columns([
                pl.col("tokens_in").cast(pl.Int64),
                pl.col("tokens_out").cast(pl.Int64),
                pl.col("cost_in").cast(pl.Float64),
                pl.col("cost_out").cast(pl.Float64),
                pl.col("cost_total").cast(pl.Float64),
                pl.col("elapsed_ms").cast(pl.Int64),
            ])
        else:
            df = pl.DataFrame()
        return df, str(_log), len(rows), (f"Skipped {skip} lines" if skip else "")

    d4_df, d4_log_path, d4_count, d4_error = _run()
    return d4_df, d4_log_path, d4_count, d4_error


'''

m = pattern.search(content)
if m:
    content = content[:m.start()] + fixed_cell + content[m.end():]
    print(f"✓ Replaced _d4_load_log cell ({m.end() - m.start()} chars -> {len(fixed_cell)} chars)")
else:
    print("✗ Could not find _d4_load_log cell pattern")
    # Show what we're searching in
    idx = content.find("_d4_load_log")
    if idx >= 0:
        print(f"  Found _d4_load_log at char {idx}")
        print(f"  Context: {repr(content[max(0,idx-20):idx+50])}")
    sys.exit(1)

# Syntax check before writing
import ast
try:
    ast.parse(content)
    print("✓ Syntax check passed")
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)

path.write_text(content, encoding='utf-8')
print(f"✓ Written: {path}")
