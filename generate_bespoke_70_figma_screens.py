import os
import html

output_path = r"C:\Users\legen\Downloads\CampusSphere_All_70_Screens_Figma_Master.svg"
artifact_output_path = r"C:\Users\legen\.gemini\antigravity\brain\c66d0107-dc84-4fee-878b-e068d68b438e\CampusSphere_All_70_Screens_Figma_Master.svg"

FRAME_W = 1440
FRAME_H = 900
GAP_X = 160
GAP_Y = 220
COLS = 7

def esc(text):
    return html.escape(str(text))

def rect(x, y, w, h, rx=0, fill="none", stroke=None, stroke_width=1, opacity=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
    if rx: s += f' rx="{rx}"'
    if fill: s += f' fill="{fill}"'
    if stroke: s += f' stroke="{stroke}" stroke-width="{stroke_width}"'
    if opacity is not None: s += f' fill-opacity="{opacity}"'
    s += '/>'
    return s

def text(x, y, content, size=12, weight=400, color="#FFFFFF", anchor="start", mono=False):
    ff = "SF Pro Display, Inter, -apple-system, sans-serif" if not mono else "SF Mono, Menlo, monospace"
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{ff}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{esc(content)}</text>'

def badge(x, y, label, bg, color, w=None, h=24):
    if w is None:
        w = len(label) * 7.5 + 18
    return f'{rect(x, y, w, h, rx=6, fill=bg, stroke=color, stroke_width=1, opacity=0.18)}{text(x + w/2, y + 16, label, size=10, weight=700, color=color, anchor="middle")}'

def button(x, y, w, h, label, bg, color="#FFFFFF", rx=8):
    return f'{rect(x, y, w, h, rx=rx, fill=bg)}{text(x + w/2, y + h/2 + 5, label, size=12, weight=700, color=color, anchor="middle")}'

def render_frame_base(s):
    res = []
    # Outer frame
    res.append(rect(0, 0, FRAME_W, FRAME_H, rx=16, fill="#0B0F19", stroke=s["color"], stroke_width=2))
    
    # Top Bar (Header)
    res.append(rect(0, 0, FRAME_W, 64, rx=16, fill="#111827"))
    res.append(rect(0, 62, FRAME_W, 2, fill=s["color"], opacity=0.6))
    
    # Screen ID badge
    res.append(rect(24, 16, 110, 32, rx=8, fill=s["color"], stroke=s["color"], stroke_width=1.5, opacity=0.15))
    res.append(text(79, 37, s["id"], size=13, weight=800, color=s["color"], anchor="middle"))
    
    # Screen Title
    res.append(text(150, 39, s["title"], size=18, weight=800, color="#FFFFFF"))
    
    # Right meta info
    res.append(rect(FRAME_W - 520, 16, 496, 32, rx=8, fill="#080C14", stroke="#1F2937", stroke_width=1))
    meta_str = f"{s['portal']}  |  Role: {s['role']}  |  Route: {s['route']}"
    res.append(text(FRAME_W - 272, 37, meta_str, size=12, weight=600, color="#9CA3AF", anchor="middle"))
    
    # Sub-header bar
    res.append(rect(24, 76, FRAME_W - 48, 38, rx=8, fill="#0F172A", stroke="#1E293B"))
    res.append(text(40, 100, f"{s['subtitle']}   •   Relational Table: ", size=12, weight=500, color="#94A3B8"))
    res.append(text(380, 100, s["db"], size=12, weight=700, color=s["color"]))
    res.append(text(FRAME_W - 40, 100, "SESSION: 2024/2025 HARMATTAN  |  STATUS: SENATE VERIFIED", size=11, weight=700, color="#10B981", anchor="end"))
    
    # Bottom Governance bar
    res.append(rect(24, FRAME_H - 54, FRAME_W - 48, 40, rx=8, fill="#0A0E17", stroke="#1E293B"))
    res.append(text(40, FRAME_H - 29, f"GOVERNANCE COMPLIANCE: {s['compliance']}", size=11, weight=600, color="#64748B"))
    res.append(text(FRAME_W - 40, FRAME_H - 29, "IMMUTABLE AUDIT TRAIL: SHA-256 SIGNED • NUC ACCREDITED", size=11, weight=700, color=s["color"], anchor="end"))
    
    return res

def render_sidebar(x, y, w, h, active_item, nav_items, portal_name, user_info, color):
    res = []
    res.append(rect(x, y, w, h, rx=12, fill="#0F172A", stroke="#1E293B"))
    
    # Portal Brand Tag
    res.append(rect(x + 16, y + 16, w - 32, 40, rx=8, fill=color, opacity=0.15))
    res.append(text(x + 28, y + 41, portal_name.upper(), size=13, weight=800, color=color))
    
    # Nav items
    cur_y = y + 72
    for item in nav_items:
        is_active = (item == active_item)
        if is_active:
            res.append(rect(x + 12, cur_y, w - 24, 36, rx=8, fill=color, opacity=0.2, stroke=color, stroke_width=1))
            res.append(text(x + 32, cur_y + 23, item, size=12, weight=700, color="#FFFFFF"))
        else:
            res.append(text(x + 32, cur_y + 23, item, size=12, weight=500, color="#94A3B8"))
        cur_y += 42
        
    # User Profile at Bottom of Sidebar
    user_y = y + h - 68
    res.append(rect(x + 12, user_y, w - 24, 54, rx=8, fill="#090D16", stroke="#1E293B"))
    res.append(rect(x + 22, user_y + 12, 30, 30, rx=15, fill=color, opacity=0.3))
    res.append(text(x + 37, user_y + 31, user_info[0][:1], size=13, weight=800, color="#FFFFFF", anchor="middle"))
    res.append(text(x + 62, user_y + 27, user_info[0], size=11, weight=700, color="#FFFFFF"))
    res.append(text(x + 62, user_y + 43, user_info[1], size=10, weight=500, color="#94A3B8"))
    
    return res

print("Initialized bespoke rendering primitives.")
