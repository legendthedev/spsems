import os
import html
import subprocess

OUTPUT_PATH = r"C:\Users\legen\Downloads\CampusSphere_All_70_Screens_Figma_Master.svg"
ARTIFACT_OUTPUT_PATH = r"C:\Users\legen\.gemini\antigravity\brain\c66d0107-dc84-4fee-878b-e068d68b438e\CampusSphere_All_70_Screens_Figma_Master.svg"

FRAME_W = 1440
FRAME_H = 900
GAP_X = 160
GAP_Y = 220
COLS = 7

def esc(text):
    return html.escape(str(text))

def r(x, y, w, h, rx=0, fill="none", stroke=None, stroke_width=1, opacity=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
    if rx: s += f' rx="{rx}"'
    if fill: s += f' fill="{fill}"'
    if stroke: s += f' stroke="{stroke}" stroke-width="{stroke_width}"'
    if opacity is not None: s += f' fill-opacity="{opacity}"'
    s += '/>'
    return s

def t(x, y, content, size=12, weight=400, color="#FFFFFF", anchor="start", mono=False):
    ff = "Inter, -apple-system, sans-serif" if not mono else "Menlo, Monaco, monospace"
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{ff}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{esc(content)}</text>'

def b(x, y, label, bg, color, w=None, h=24):
    if w is None:
        w = len(label) * 7.5 + 16
    return f'{r(x, y, w, h, rx=6, fill=bg, stroke=color, stroke_width=1, opacity=0.18)}{t(x + w/2, y + 16, label, size=10, weight=700, color=color, anchor="middle")}'

def btn(x, y, w, h, label, bg, color="#FFFFFF", rx=8):
    return f'{r(x, y, w, h, rx=rx, fill=bg)}{t(x + w/2, y + h/2 + 5, label, size=12, weight=700, color=color, anchor="middle")}'

def render_frame_base(s):
    res = []
    res.append(r(0, 0, FRAME_W, FRAME_H, rx=16, fill="#0B0F19", stroke=s["color"], stroke_width=2.5))
    res.append(r(0, 0, FRAME_W, 64, rx=16, fill="#111827"))
    res.append(r(0, 62, FRAME_W, 2, fill=s["color"], opacity=0.6))
    
    # ID & Title
    res.append(r(24, 16, 110, 32, rx=8, fill=s["color"], stroke=s["color"], stroke_width=1.5, opacity=0.15))
    res.append(t(79, 37, s["id"], size=13, weight=800, color=s["color"], anchor="middle"))
    res.append(t(150, 39, s["title"], size=18, weight=800, color="#FFFFFF"))
    
    # Breadcrumbs & Role
    res.append(r(FRAME_W - 520, 16, 496, 32, rx=8, fill="#080C14", stroke="#1F2937", stroke_width=1))
    meta_str = f"{s['portal']}  |  Role: {s['role']}  |  Route: {s['route']}"
    res.append(t(FRAME_W - 272, 37, meta_str, size=12, weight=600, color="#9CA3AF", anchor="middle"))
    
    # Sub-header bar
    res.append(r(24, 76, FRAME_W - 48, 38, rx=8, fill="#0F172A", stroke="#1E293B"))
    res.append(t(40, 100, f"{s['subtitle']}   •   Relational Table: ", size=12, weight=500, color="#94A3B8"))
    res.append(t(410, 100, s["db"], size=12, weight=700, color=s["color"]))
    res.append(t(FRAME_W - 40, 100, "SESSION: 2024/2025 HARMATTAN  |  STATUS: SENATE VERIFIED", size=11, weight=700, color="#10B981", anchor="end"))
    
    # Bottom Governance bar
    res.append(r(24, FRAME_H - 52, FRAME_W - 48, 38, rx=8, fill="#0A0E17", stroke="#1E293B"))
    res.append(t(40, FRAME_H - 28, f"GOVERNANCE COMPLIANCE: {s['compliance']}", size=11, weight=600, color="#64748B"))
    res.append(t(FRAME_W - 40, FRAME_H - 28, "IMMUTABLE AUDIT TRAIL: SHA-256 SIGNED • NUC ACCREDITED", size=11, weight=700, color=s["color"], anchor="end"))
    return res

def render_sidebar(x, y, w, h, active_item, nav_items, portal_name, user_info, color):
    res = []
    res.append(r(x, y, w, h, rx=12, fill="#0F172A", stroke="#1E293B"))
    res.append(r(x + 16, y + 16, w - 32, 40, rx=8, fill=color, opacity=0.15))
    res.append(t(x + w/2, y + 41, portal_name.upper(), size=13, weight=800, color=color, anchor="middle"))
    
    cur_y = y + 72
    for item in nav_items:
        is_active = (item == active_item)
        if is_active:
            res.append(r(x + 12, cur_y, w - 24, 36, rx=8, fill=color, opacity=0.2, stroke=color, stroke_width=1))
            res.append(t(x + 32, cur_y + 23, item, size=12, weight=700, color="#FFFFFF"))
        else:
            res.append(t(x + 32, cur_y + 23, item, size=12, weight=500, color="#94A3B8"))
        cur_y += 40
        
    user_y = y + h - 68
    res.append(r(x + 12, user_y, w - 24, 54, rx=8, fill="#090D16", stroke="#1E293B"))
    res.append(r(x + 22, user_y + 12, 30, 30, rx=15, fill=color, opacity=0.3))
    res.append(t(x + 37, user_y + 31, user_info[0][:1], size=13, weight=800, color="#FFFFFF", anchor="middle"))
    res.append(t(x + 62, user_y + 27, user_info[0], size=11, weight=700, color="#FFFFFF"))
    res.append(t(x + 62, user_y + 43, user_info[1], size=10, weight=500, color="#94A3B8"))
    return res

# ─────────────────────────────────────────────────────────────────────────────
# SPECIALIZED SCREEN LAYOUT RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

def render_auth_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Hero Banner
    w_left = 580
    res.append(r(24, top_y, w_left, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    # University Crest Emblem Mock
    res.append(r(50, top_y + 40, 72, 72, rx=16, fill=s["color"], opacity=0.2, stroke=s["color"], stroke_width=2))
    res.append(t(86, top_y + 83, "UNI", size=20, weight=900, color=s["color"], anchor="middle"))
    res.append(t(140, top_y + 68, "KWARA STATE UNIVERSITY, MALETE", size=18, weight=800, color="#FFFFFF"))
    res.append(t(140, top_y + 92, "Office of Academic Planning & Systems Integration", size=13, weight=500, color="#94A3B8"))
    
    res.append(t(50, top_y + 160, s["auth_headline"], size=24, weight=800, color="#FFFFFF"))
    res.append(t(50, top_y + 190, s["auth_description"], size=13, weight=400, color="#94A3B8"))
    
    # 3 Feature Pills
    pills = s.get("auth_highlights", [
        ("NUC Accredited Gateway", "National compliance standard"),
        ("Single Sign-On (SSO)", "Active Directory & Google Workspace"),
        ("End-to-End Cryptography", "SHA-256 and AES-GCM 256-bit encrypted")
    ])
    p_y = top_y + 240
    for title, desc in pills:
        res.append(r(50, p_y, w_left - 100, 64, rx=10, fill="#131F37", stroke="#253554"))
        res.append(t(70, p_y + 28, f"✓  {title}", size=13, weight=700, color="#FFFFFF"))
        res.append(t(70, p_y + 48, desc, size=11, weight=400, color="#94A3B8"))
        p_y += 76
        
    res.append(t(50, top_y + h - 30, "Protected by Federal Ministry of Education Cyber Security Framework", size=11, color="#64748B"))
    
    # Right Authentication Card
    w_right = FRAME_W - 48 - w_left - 24
    rx_pos = 24 + w_left + 24
    res.append(r(rx_pos, top_y, w_right, h, rx=14, fill="#111827", stroke="#1F2937"))
    
    form_y = top_y + 40
    res.append(t(rx_pos + 40, form_y, s["form_title"], size=22, weight=800, color="#FFFFFF"))
    res.append(t(rx_pos + 40, form_y + 24, s["form_subtitle"], size=13, weight=400, color="#94A3B8"))
    
    # Form Inputs
    inputs = s.get("form_inputs", [
        ("Institutional Identifier (Matric / Staff ID)", "e.g. 20/52CS/0084 or STAFF/042"),
        ("Password or Access PIN", "••••••••••••••••"),
        ("Selected Academic Session", "2024/2025 Harmattan Semester")
    ])
    inp_y = form_y + 60
    for lbl, val in inputs:
        res.append(t(rx_pos + 40, inp_y, lbl, size=12, weight=600, color="#E2E8F0"))
        res.append(r(rx_pos + 40, inp_y + 10, w_right - 80, 48, rx=8, fill="#0B0F19", stroke="#374151"))
        res.append(t(rx_pos + 56, inp_y + 40, val, size=13, weight=500, color="#9CA3AF"))
        inp_y += 74
        
    # Remember & Forgot
    res.append(r(rx_pos + 40, inp_y + 6, 16, 16, rx=4, fill=s["color"]))
    res.append(t(rx_pos + 66, inp_y + 19, "Remember my institutional session on this device", size=12, color="#94A3B8"))
    res.append(t(rx_pos + w_right - 40, inp_y + 19, "Forgot Security PIN?", size=12, weight=600, color=s["color"], anchor="end"))
    
    # Sign-in Button
    res.append(btn(rx_pos + 40, inp_y + 40, w_right - 80, 50, s.get("btn_label", "Sign In to Portal Workstation"), s["color"], "#000000", rx=8))
    
    # SSO Divider & Button
    res.append(r(rx_pos + 40, inp_y + 115, (w_right - 80 - 140) // 2, 1, fill="#374151"))
    res.append(t(rx_pos + w_right // 2, inp_y + 119, "OR AUTHENTICATE WITH", size=10, weight=700, color="#6B7280", anchor="middle"))
    res.append(r(rx_pos + w_right // 2 + 80, inp_y + 115, (w_right - 80 - 140) // 2, 1, fill="#374151"))
    
    res.append(r(rx_pos + 40, inp_y + 135, w_right - 80, 46, rx=8, fill="#1F2937", stroke="#374151"))
    res.append(t(rx_pos + w_right // 2, inp_y + 163, "Sign in with Microsoft 365 Azure AD", size=12, weight=700, color="#FFFFFF", anchor="middle"))
    
    return res

def render_dashboard_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    sb_w = 260
    
    # Sidebar
    nav = s.get("nav_items", ["Overview", "Submissions", "Reviews", "Examinations", "Clearance", "Settings"])
    user = s.get("user_info", ("Prof. I. A. Bello", "Senior Academic Supervisor"))
    res.extend(render_sidebar(24, top_y, sb_w, h, s.get("active_nav", "Overview"), nav, s["portal"], user, s["color"]))
    
    # Main Content Area
    main_x = 24 + sb_w + 20
    main_w = FRAME_W - 48 - sb_w - 20
    
    # Top 3 Metrics
    m_w = (main_w - 32) // 3
    for i, (lbl, val, sub) in enumerate(s.get("metrics", [("Total Load", "14 Active", "Normal"), ("Pending", "3 Drafts", "Due 48h"), ("Score Avg", "88.4%", "Distinction")])):
        mx = main_x + i * (m_w + 16)
        res.append(r(mx, top_y, m_w, 92, rx=12, fill="#0F172A", stroke="#1E293B"))
        res.append(t(mx + 20, top_y + 28, lbl, size=12, weight=600, color="#94A3B8"))
        res.append(t(mx + 20, top_y + 60, val, size=24, weight=800, color="#FFFFFF"))
        res.append(b(mx + m_w - 110, top_y + 20, sub, s["color"], s["color"], 95, 22))
        
    # Main Data Table Card
    tbl_y = top_y + 112
    tbl_h = h - 112
    res.append(r(main_x, tbl_y, main_w, tbl_h, rx=14, fill="#111827", stroke="#1F2937"))
    
    # Table Header
    res.append(t(main_x + 24, tbl_y + 36, s.get("table_title", "Operational Queue & Verification Registry"), size=17, weight=800, color="#FFFFFF"))
    res.append(btn(main_x + main_w - 160, tbl_y + 16, 136, 34, "+ New Entry", s["color"], "#000000", rx=6))
    
    # Column headers
    cols = s.get("table_headers", ["Candidate / Staff", "Program / Level", "Current Milestone", "Evaluation State", "Actions"])
    c_w = (main_w - 48) // len(cols)
    res.append(r(main_x + 16, tbl_y + 60, main_w - 32, 34, rx=6, fill="#0B0F19"))
    for ci, c_name in enumerate(cols):
        res.append(t(main_x + 32 + ci * c_w, tbl_y + 81, c_name.upper(), size=11, weight=700, color="#6B7280"))
        
    # Table rows
    rows = s.get("table_rows", [
        ["Adeyemi Bashir (20/52CS/0084)", "MSc Computer Science", "Chapter 4: Results & Discussion", "Turnitin Verified (11.4%)", "Open Annotator →"],
        ["Fatima Garba (21/52CS/0012)", "PhD Cyber Security", "Chapter 3: Formal Methodology", "Approved by Supervisor", "View Clearance"],
        ["Chukwuma Obi (20/52CS/0091)", "MSc Data Engineering", "Concept Note & Proposal", "Awaiting Panel Verdict", "Review Rubric"],
        ["Zainab Aliyu (21/52CS/0034)", "MSc Artificial Intelligence", "Pre-Defense Readiness Viva", "Defense Board Assigned", "Print Timetable"],
        ["Usman Danladi (20/52CS/0077)", "MSc Software Systems", "Chapter 2: Literature Synthesis", "Revision Requested", "View Notes"]
    ])
    for ri, r_data in enumerate(rows):
        ry = tbl_y + 104 + ri * 48
        bg_col = "#151F32" if ri % 2 == 0 else "#0F172A"
        res.append(r(main_x + 16, ry, main_w - 32, 42, rx=6, fill=bg_col))
        for ci, val in enumerate(r_data):
            cx = main_x + 32 + ci * c_w
            if ci == 0:
                res.append(t(cx, ry + 26, val, size=12, weight=700, color="#FFFFFF"))
            elif ci == len(r_data) - 1:
                res.append(btn(cx, ry + 8, 130, 26, val, s["color"], "#000000", rx=4))
            elif ci == len(r_data) - 2:
                res.append(b(cx, ry + 9, val, s["color"], s["color"]))
            else:
                res.append(t(cx, ry + 26, val, size=12, weight=400, color="#94A3B8"))
                
    return res

def render_annotator_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    sb_w = 240
    
    # Left Document Outline
    res.append(r(24, top_y, sb_w, h, rx=12, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "DOCUMENT VAULT", size=13, weight=800, color=s["color"]))
    chapters = [
        ("Chapter 1: Introduction", "Approved (v2.1)"),
        ("Chapter 2: Lit Review", "Approved (v3.0)"),
        ("Chapter 3: Methodology", "Approved (v2.4)"),
        ("Chapter 4: Results & Eval", "ACTIVE REVIEW (v4.1)"),
        ("Chapter 5: Conclusion", "Draft Staged")
    ]
    cy = top_y + 64
    for ch_title, ch_st in chapters:
        is_act = "ACTIVE" in ch_st
        bg_c = s["color"] if is_act else "#1E293B"
        res.append(r(36, cy, sb_w - 24, 52, rx=8, fill=bg_c, opacity=0.15 if is_act else 0.5, stroke=s["color"] if is_act else None))
        res.append(t(48, cy + 22, ch_title, size=12, weight=700, color="#FFFFFF" if is_act else "#CBD5E1"))
        res.append(t(48, cy + 40, ch_st, size=10, weight=600, color=s["color"] if is_act else "#64748B"))
        cy += 60
        
    res.append(btn(36, top_y + h - 56, sb_w - 24, 40, "↑ Upload New Version", s["color"], "#000000", rx=8))
    
    # Center Document Reader (PDF Emulation)
    doc_x = 24 + sb_w + 16
    doc_w = 680
    res.append(r(doc_x, top_y, doc_w, h, rx=12, fill="#1E293B", stroke="#334155"))
    # PDF Header Bar
    res.append(r(doc_x, top_y, doc_w, 42, rx=12, fill="#0F172A"))
    res.append(t(doc_x + 20, top_y + 26, "Adeyemi_Bashir_MSc_Dissertation_Chapter4_v4.1.pdf   •   Page 42 of 118", size=12, weight=600, color="#94A3B8"))
    res.append(t(doc_x + doc_w - 20, top_y + 26, "ZOOM 100%   |   FIT WIDTH", size=11, weight=700, color="#64748B", anchor="end"))
    
    # Document Page Canvas
    page_y = top_y + 54
    page_w = doc_w - 40
    page_h = h - 68
    res.append(r(doc_x + 20, page_y, page_w, page_h, rx=6, fill="#FFFFFF"))
    
    # Page Academic Content
    res.append(t(doc_x + 50, page_y + 40, "CHAPTER 4: EXPERIMENTAL EVALUATION & RESULTS", size=16, weight=800, color="#0F172A"))
    res.append(t(doc_x + 50, page_y + 64, "4.3 Quantitative Analysis of Multi-Agent Dispatch Latency", size=13, weight=700, color="#1E293B"))
    
    paras = [
        "In this section, the proposed autonomous agent orchestration engine was benchmarked against",
        "traditional monolithic REST dispatch architectures. As illustrated in Table 4.2, the mean query",
        "response latency under a 5,000 concurrent student load dropped significantly from 340ms to 42ms."
    ]
    for pi, pl in enumerate(paras):
        res.append(t(doc_x + 50, page_y + 95 + pi * 20, pl, size=11, color="#334155"))
        
    # Yellow Highlight Passage
    res.append(r(doc_x + 48, page_y + 165, page_w - 96, 44, rx=4, fill="#FEF08A"))
    res.append(t(doc_x + 52, page_y + 185, "Highlight: \"The cosine similarity matching algorithm achieved 96.4% precision when aligning", size=11, weight=700, color="#854D0E"))
    res.append(t(doc_x + 52, page_y + 202, "postgraduate research proposals with faculty supervisor publication vectors.\"", size=11, weight=700, color="#854D0E"))
    
    # Formula Mock
    res.append(r(doc_x + 50, page_y + 230, page_w - 100, 50, rx=4, fill="#F8FAFC", stroke="#E2E8F0"))
    res.append(t(doc_x + page_w // 2, page_y + 260, "Similarity(A, B) = cos(θ) = ( A • B ) / ( ||A|| ||B|| )", size=12, weight=700, color="#0F172A", anchor="middle", mono=True))
    
    more_paras = [
        "Furthermore, ablation studies confirm that the MS 365 Access ADODB bridge introduces zero drift",
        "across all 16 relational tables when operating under continuous background synchronization.",
        "The empirical findings strictly confirm our initial theoretical hypotheses formulated in Section 1.3."
    ]
    for pi, pl in enumerate(more_paras):
        res.append(t(doc_x + 50, page_y + 310 + pi * 20, pl, size=11, color="#334155"))
        
    # Right Annotation Thread Sidebar
    comm_x = doc_x + doc_w + 16
    comm_w = FRAME_W - comm_x - 24
    res.append(r(comm_x, top_y, comm_w, h, rx=12, fill="#0F172A", stroke="#1E293B"))
    res.append(t(comm_x + 20, top_y + 36, "SUPERVISOR ANNOTATIONS", size=13, weight=800, color="#FFFFFF"))
    
    # Comment Card 1
    res.append(r(comm_x + 16, top_y + 60, comm_w - 32, 130, rx=10, fill="#131F37", stroke=s["color"]))
    res.append(t(comm_x + 28, top_y + 84, "Prof. I. A. Bello (Supervisor)", size=12, weight=700, color="#FFFFFF"))
    res.append(t(comm_x + 28, top_y + 102, "OCT 14, 2024 at 14:22 • Chapter 4 Passage 2", size=10, color="#94A3B8"))
    res.append(t(comm_x + 28, top_y + 126, "Please verify if the 96.4% precision was evaluated", size=11, color="#E2E8F0"))
    res.append(t(comm_x + 28, top_y + 144, "under 5-fold cross validation. Add p-values.", size=11, color="#E2E8F0"))
    res.append(b(comm_x + comm_w - 110, top_y + 72, "Action Needed", "#EF4444", "#EF4444"))
    
    # Comment Card 2
    res.append(r(comm_x + 16, top_y + 204, comm_w - 32, 110, rx=10, fill="#131F37", stroke="#253554"))
    res.append(t(comm_x + 28, top_y + 228, "Prof. I. A. Bello (Supervisor)", size=12, weight=700, color="#FFFFFF"))
    res.append(t(comm_x + 28, top_y + 246, "OCT 14, 2024 at 14:35 • Equation 4.1", size=10, color="#94A3B8"))
    res.append(t(comm_x + 28, top_y + 270, "Vector formulation is mathematically sound.", size=11, color="#10B981"))
    res.append(b(comm_x + comm_w - 90, top_y + 216, "Approved", "#10B981", "#10B981"))
    
    # Action Buttons at Bottom of Thread
    res.append(btn(comm_x + 16, top_y + h - 110, comm_w - 32, 42, "Approve Milestone Chapter", "#10B981", "#000000", rx=8))
    res.append(btn(comm_x + 16, top_y + h - 56, comm_w - 32, 42, "Request Specific Revisions", "#EF4444", "#FFFFFF", rx=8))
    
    return res

def render_turnitin_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Gauge & Overview Card
    left_w = 460
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "TURNITIN SIMILARITY AUDIT", size=16, weight=800, color="#FFFFFF"))
    res.append(t(44, top_y + 56, "Academic Document Similarity Index & AI Verification", size=12, color="#94A3B8"))
    
    # Big Dial Container
    dial_y = top_y + 80
    res.append(r(44, dial_y, left_w - 40, 220, rx=12, fill="#131F37", stroke="#253554"))
    # Dial Circle
    res.append(f'<circle cx="{44 + (left_w - 40)//2}" cy="{dial_y + 100}" r="75" stroke="#1E293B" stroke-width="16" fill="none"/>')
    res.append(f'<circle cx="{44 + (left_w - 40)//2}" cy="{dial_y + 100}" r="75" stroke="#10B981" stroke-width="16" stroke-dasharray="471" stroke-dashoffset="417" stroke-linecap="round" fill="none"/>')
    res.append(t(44 + (left_w - 40)//2, dial_y + 98, "11.4%", size=32, weight=900, color="#10B981", anchor="middle"))
    res.append(t(44 + (left_w - 40)//2, dial_y + 124, "SIMILARITY INDEX", size=11, weight=700, color="#94A3B8", anchor="middle"))
    res.append(b(44 + (left_w - 40)//2 - 60, dial_y + 175, "VERIFIED PASS (<= 15%)", "#10B981", "#10B981", 120, 26))
    
    # Breakdown Metrics
    metrics_list = [
        ("Internet Sources Overlap", "5.2%", "#38BDF8"),
        ("Publications & Journals", "4.1%", "#F59E0B"),
        ("Student Papers Cross-Match", "2.1%", "#A855F7"),
        ("AI-Generated Anomaly Score", "0.4% (Clean)", "#10B981")
    ]
    my = dial_y + 240
    for lbl, val, c in metrics_list:
        res.append(r(44, my, left_w - 40, 44, rx=8, fill="#0B0F19", stroke="#1E293B"))
        res.append(t(60, my + 27, lbl, size=12, weight=600, color="#E2E8F0"))
        res.append(t(left_w - 20, my + 27, val, size=13, weight=800, color=c, anchor="end"))
        my += 54
        
    res.append(btn(44, top_y + h - 56, left_w - 40, 42, "Download Official Senate Certificate", "#10B981", "#000000", rx=8))
    
    # Right Matched Source Registry
    right_x = 24 + left_w + 20
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    res.append(t(right_x + 24, top_y + 36, "Primary Matched Repositories & Excerpts", size=16, weight=800, color="#FFFFFF"))
    
    sources = [
        ("1", "IEEE Xplore Digital Library", "4.2%", "Multi-Agent System Orchestration in Distributed Educational Frameworks", "Internet Publication 2023"),
        ("2", "ScienceDirect / Elsevier Journal", "3.1%", "Relational Database Sharding & Active Directory Identity Federation", "Journal of Systems & Software 2022"),
        ("3", "University of Ilorin Institutional Archive", "2.3%", "Postgraduate Dissertations in Department of Computer Science", "Institutional Repository"),
        ("4", "ArXiv.org Preprints", "1.8%", "Cosine Similarity Word Vector Embeddings for Academic Supervision Allocation", "Preprint CS.AI 2024")
    ]
    sy = top_y + 60
    for rank, name, match_pct, paper_title, source_type in sources:
        res.append(r(right_x + 20, sy, right_w - 40, 102, rx=10, fill="#141E33", stroke="#253554"))
        res.append(r(right_x + 36, sy + 16, 28, 28, rx=6, fill=s["color"], opacity=0.2))
        res.append(t(right_x + 50, sy + 35, rank, size=13, weight=800, color=s["color"], anchor="middle"))
        res.append(t(right_x + 76, sy + 34, name, size=14, weight=700, color="#FFFFFF"))
        res.append(b(right_x + right_w - 110, sy + 18, f"{match_pct} Overlap", s["color"], s["color"], 80, 24))
        res.append(t(right_x + 76, sy + 62, paper_title, size=12, weight=500, color="#CBD5E1"))
        res.append(t(right_x + 76, sy + 84, f"Source Type: {source_type}   •   Status: Excluded Valid Citation", size=11, color="#64748B"))
        sy += 114
        
    # Text Diff Preview Box
    res.append(r(right_x + 20, sy, right_w - 40, h - (sy - top_y) - 20, rx=10, fill="#0B0F19", stroke="#1E293B"))
    res.append(t(right_x + 36, sy + 28, "Flagged Excerpt In Dissertation (Chapter 2, Page 19):", size=12, weight=700, color="#F59E0B"))
    res.append(r(right_x + 36, sy + 40, right_w - 72, 38, rx=4, fill="#FEF08A"))
    res.append(t(right_x + 46, sy + 64, "...the agentic paradigm allows multiple autonomous actors to collaborate on decentralized tasks...", size=11, weight=700, color="#854D0E"))
    res.append(t(right_x + 36, sy + 96, "Action Taken: Properly paraphrased and formal IEEE citation appended by candidate.", size=11, color="#10B981"))
    
    return res

def render_hostel_matrix_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Hall Selector & Filter
    left_w = 280
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "CAMPUS RESIDENCE", size=16, weight=800, color="#FFFFFF"))
    
    halls = [
        ("Hall of Residence A", "Male Executive", "92% Full"),
        ("Alhaja Sanni Hall", "Female Undergraduate", "88% Full"),
        ("Prof. Gambari Hall", "Postgraduate Suites", "64% Full"),
        ("Silver Crest Hall", "Private Partnered", "75% Full")
    ]
    hy = top_y + 60
    for h_name, h_type, h_cap in halls:
        is_sel = "Hall of Residence A" in h_name
        res.append(r(36, hy, left_w - 24, 64, rx=8, fill="#1E293B" if is_sel else "#0B0F19", stroke=s["color"] if is_sel else None))
        res.append(t(48, hy + 26, h_name, size=12, weight=700, color="#FFFFFF"))
        res.append(t(48, hy + 46, f"{h_type} • {h_cap}", size=11, color=s["color"] if is_sel else "#64748B"))
        hy += 74
        
    res.append(t(44, hy + 20, "BLOCK & FLOOR SELECTOR", size=12, weight=700, color="#94A3B8"))
    res.append(r(36, hy + 35, left_w - 24, 40, rx=6, fill="#0B0F19", stroke="#374151"))
    res.append(t(48, hy + 60, "Block 1 (Ground Floor - Rooms 101-108)", size=11, color="#E2E8F0"))
    
    # Center Interactive Bed Matrix Grid
    center_x = 24 + left_w + 16
    center_w = 680
    res.append(r(center_x, top_y, center_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    
    # Legend Bar
    res.append(t(center_x + 24, top_y + 34, "Block 1: Real-Time Bed Space Allocation Rack", size=16, weight=800, color="#FFFFFF"))
    res.append(r(center_x + center_w - 360, top_y + 18, 12, 12, rx=3, fill="#10B981"))
    res.append(t(center_x + center_w - 342, top_y + 28, "Available", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 260, top_y + 18, 12, 12, rx=3, fill="#EF4444"))
    res.append(t(center_x + center_w - 242, top_y + 28, "Occupied", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 160, top_y + 18, 12, 12, rx=3, fill="#38BDF8"))
    res.append(t(center_x + center_w - 142, top_y + 28, "Selected", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 70, top_y + 18, 12, 12, rx=3, fill="#F59E0B"))
    res.append(t(center_x + center_w - 52, top_y + 28, "Reserved", size=11, color="#94A3B8"))
    
    # Rooms Grid (Rooms 101 to 106)
    room_y = top_y + 54
    for ri in range(6):
        rm_num = 101 + ri
        row_y = room_y + ri * 96
        res.append(r(center_x + 20, row_y, center_w - 40, 84, rx=10, fill="#0F172A", stroke="#1E293B"))
        res.append(t(center_x + 36, row_y + 48, f"ROOM {rm_num}", size=14, weight=800, color="#FFFFFF"))
        
        # 4 Bunks
        bunks = [
            ("Bunk A (Top)", "#EF4444" if rm_num != 104 else "#38BDF8", "Occupied" if rm_num != 104 else "SELECTED (YOU)"),
            ("Bunk A (Btm)", "#EF4444", "Occupied"),
            ("Bunk B (Top)", "#10B981" if rm_num in [102, 105] else "#EF4444", "Available" if rm_num in [102, 105] else "Occupied"),
            ("Bunk B (Btm)", "#10B981" if rm_num in [103, 106] else "#F59E0B", "Available" if rm_num in [103, 106] else "Reserved")
        ]
        for bi, (b_name, b_col, b_status) in enumerate(bunks):
            bx = center_x + 130 + bi * 126
            is_target = (rm_num == 104 and bi == 0)
            res.append(r(bx, row_y + 12, 116, 60, rx=6, fill=b_col, opacity=0.18, stroke=b_col, stroke_width=2 if is_target else 1))
            res.append(t(bx + 12, row_y + 32, b_name, size=11, weight=700, color="#FFFFFF"))
            res.append(t(bx + 12, row_y + 54, b_status, size=10, weight=700, color=b_col))
            
    # Right Bed Checkout & Payment Panel
    right_x = center_x + center_w + 16
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(right_x + 20, top_y + 36, "SELECTED BED SPACE", size=14, weight=800, color="#FFFFFF"))
    
    # Bed Info Card
    res.append(r(right_x + 16, top_y + 56, right_w - 32, 120, rx=10, fill="#131F37", stroke="#38BDF8"))
    res.append(t(right_x + 28, top_y + 80, "Room 104 • Bunk A Top", size=16, weight=800, color="#38BDF8"))
    res.append(t(right_x + 28, top_y + 102, "Hall of Residence A (Male Executive)", size=12, color="#E2E8F0"))
    res.append(t(right_x + 28, top_y + 124, "Bed Space Key ID: KWA-HRA-104-AT", size=11, color="#94A3B8"))
    res.append(t(right_x + 28, top_y + 150, "Reservation Lock: 23 hrs 45 mins left", size=11, weight=700, color="#F59E0B"))
    
    # Fee Breakdown
    res.append(t(right_x + 20, top_y + 200, "Bursary Fee Breakdown", size=13, weight=700, color="#FFFFFF"))
    fees = [
        ("Accommodation Fee", "₦45,000.00"),
        ("Caution & Maintenance Deposit", "₦10,000.00"),
        ("Hall Executive Dues", "₦5,000.00")
    ]
    fy = top_y + 220
    for f_lbl, f_val in fees:
        res.append(t(right_x + 20, fy + 16, f_lbl, size=11, color="#94A3B8"))
        res.append(t(right_x + right_w - 20, fy + 16, f_val, size=11, weight=600, color="#FFFFFF", anchor="end"))
        fy += 26
        
    res.append(r(right_x + 16, fy + 10, right_w - 32, 1, fill="#334155"))
    res.append(t(right_x + 20, fy + 36, "TOTAL DUE", size=14, weight=800, color="#FFFFFF"))
    res.append(t(right_x + right_w - 20, fy + 36, "₦60,000.00", size=16, weight=900, color="#10B981", anchor="end"))
    
    res.append(r(right_x + 16, fy + 60, right_w - 32, 70, rx=8, fill="#0B0F19", stroke="#1E293B"))
    res.append(t(right_x + 28, fy + 82, "Remita RRR: 2408-9912-4410", size=11, weight=700, color="#38BDF8"))
    res.append(t(right_x + 28, fy + 104, "Verified by University Bursary Gateway", size=10, color="#10B981"))
    
    res.append(btn(right_x + 16, top_y + h - 56, right_w - 32, 42, "Confirm Bed & Generate Gate Pass", s["color"], "#000000", rx=8))
    
    return res

def render_siwes_logbook_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Profile Card
    left_w = 280
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "SIWES TRAINEE PROFILE", size=14, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 110, rx=8, fill="#131F37", stroke="#253554"))
    res.append(t(48, top_y + 80, "Chinedu Eze", size=15, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 100, "Matric: 21/25EE/0114", size=12, color="#94A3B8"))
    res.append(t(48, top_y + 120, "Electrical Engineering (400L)", size=11, color="#CBD5E1"))
    res.append(t(48, top_y + 144, "TotalEnergies E&P Nigeria", size=11, weight=700, color="#F59E0B"))
    
    # Weeks selector
    res.append(t(44, top_y + 190, "ATTACHMENT TIMELINE", size=12, weight=700, color="#94A3B8"))
    wy = top_y + 210
    for w_num in range(12, 17):
        is_cur = (w_num == 14)
        res.append(r(36, wy, left_w - 24, 38, rx=6, fill="#F59E0B" if is_cur else "#0B0F19", opacity=0.18 if is_cur else 0.5, stroke="#F59E0B" if is_cur else None))
        res.append(t(48, wy + 24, f"Week {w_num} of 24", size=12, weight=700, color="#FFFFFF" if is_cur else "#94A3B8"))
        res.append(t(left_w - 10, wy + 24, "STAMPED" if w_num < 14 else ("ACTIVE" if w_num == 14 else "PENDING"), size=10, weight=700, color="#10B981" if w_num < 14 else "#F59E0B", anchor="end"))
        wy += 46
        
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Export ITF Form 8 PDF", "#F59E0B", "#000000", rx=8))
    
    # Center Daily Work Log
    center_x = 24 + left_w + 16
    center_w = 680
    res.append(r(center_x, top_y, center_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    
    res.append(t(center_x + 24, top_y + 36, "Week 14 Electronic Logbook: Daily Engineering Activities", size=16, weight=800, color="#FFFFFF"))
    
    # Days Mon to Fri
    days = [
        ("Monday, Oct 14", "Substation Transformer Overhaul & Dielectric Oil Breakdown Test", "6.5 hrs", "Megger MIT515, Oil Tester"),
        ("Tuesday, Oct 15", "Secondary Injection Testing of Overcurrent and Earth Fault Relays", "8.0 hrs", "Omicron CMC 356, Multimeter"),
        ("Wednesday, Oct 16", "High-Voltage Circuit Breaker Contact Resistance & Timing Analysis", "7.5 hrs", "Micro-Ohmmeter, Timing Kit"),
        ("Thursday, Oct 17", "SCADA RTU Wiring, Modbus Protocol Verification & Telemetry Ping", "8.0 hrs", "Serial Interface, Oscilloscope"),
        ("Friday, Oct 18", "Weekly Safety Toolbox Talk & Worksite Hazard Identification Audit", "5.0 hrs", "Gas Detector, Safety Harness")
    ]
    dy = top_y + 58
    for d_title, d_task, d_hrs, d_tools in days:
        res.append(r(center_x + 20, dy, center_w - 40, 84, rx=8, fill="#0F172A", stroke="#1E293B"))
        res.append(t(center_x + 36, dy + 24, d_title, size=12, weight=700, color="#F59E0B"))
        res.append(b(center_x + center_w - 120, dy + 12, d_hrs, "#F59E0B", "#F59E0B", 80, 22))
        res.append(t(center_x + 36, dy + 48, d_task, size=12, weight=500, color="#FFFFFF"))
        res.append(t(center_x + 36, dy + 68, f"Equipment Handled: {d_tools}", size=11, color="#64748B"))
        dy += 92
        
    # Technical Sketch Attachment
    res.append(r(center_x + 20, dy, center_w - 40, 70, rx=8, fill="#0B0F19", stroke="#253554"))
    res.append(t(center_x + 36, dy + 28, "Attached Engineering Schematic (SLD-Substation-33kV.png)", size=12, weight=700, color="#38BDF8"))
    res.append(t(center_x + 36, dy + 48, "Verified SHA-256 Hash: 8f4b2c1e9... • Uploaded by Trainee via Android Tablet", size=10, color="#94A3B8"))
    res.append(btn(center_x + center_w - 160, dy + 18, 120, 34, "View CAD Sheet", "#38BDF8", "#000000", rx=6))
    
    # Right Supervisor Sign-Off & Stamp
    right_x = center_x + center_w + 16
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(right_x + 20, top_y + 36, "INDUSTRY SUPERVISOR SIGN-OFF", size=13, weight=800, color="#FFFFFF"))
    
    # Corporate Stamp Box
    res.append(r(right_x + 16, top_y + 58, right_w - 32, 190, rx=10, fill="#131F37", stroke="#F59E0B"))
    res.append(t(right_x + 28, top_y + 84, "TotalEnergies E&P Nigeria", size=14, weight=800, color="#FFFFFF"))
    res.append(t(right_x + 28, top_y + 104, "Engr. Babatunde Williams, FNSE", size=12, weight=700, color="#F59E0B"))
    res.append(t(right_x + 28, top_y + 124, "Chief Substation Engineer", size=11, color="#94A3B8"))
    res.append(t(right_x + 28, top_y + 150, "GPS Stamp: 4.8156° N, 7.0498° E", size=11, color="#CBD5E1"))
    res.append(t(right_x + 28, top_y + 172, "Date: 18-OCT-2024 16:45:12", size=11, color="#CBD5E1"))
    res.append(b(right_x + 28, top_y + 195, "VERIFIED CORPORATE STAMP", "#10B981", "#10B981", 170, 24))
    
    # ITF Grading Rating
    res.append(t(right_x + 20, top_y + 270, "Weekly Performance Assessment", size=12, weight=700, color="#FFFFFF"))
    scores = [
        ("Punctuality & Safety", "Excellent (5/5)"),
        ("Technical Competence", "Very Good (4.5/5)"),
        ("Initiative & Attitude", "Outstanding (5/5)")
    ]
    sy = top_y + 290
    for s_lbl, s_val in scores:
        res.append(t(right_x + 20, sy + 16, s_lbl, size=11, color="#94A3B8"))
        res.append(t(right_x + right_w - 20, sy + 16, s_val, size=11, weight=700, color="#10B981", anchor="end"))
        sy += 28
        
    res.append(btn(right_x + 16, top_y + h - 56, right_w - 32, 42, "Affix Digital Signature Key", "#F59E0B", "#000000", rx=8))
    
    return res

def render_ai_allocation_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Candidate Context
    left_w = 420
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "CANDIDATE DISSERTATION PROFILE", size=15, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 130, rx=10, fill="#131F37", stroke="#253554"))
    res.append(t(48, top_y + 80, "Adeyemi Bashir", size=16, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 102, "Matric: 20/52CS/0084  •  MSc Computer Science", size=12, color=s["color"]))
    res.append(t(48, top_y + 128, "Topic: Autonomous Multi-Agent Orchestration for", size=12, weight=600, color="#E2E8F0"))
    res.append(t(48, top_y + 146, "Higher Education Institutional Operating Systems", size=12, weight=600, color="#E2E8F0"))
    res.append(t(48, top_y + 170, "Proposal Vetted: Senate Approved", size=11, color="#10B981"))
    
    # Research Feature Vector Tags
    res.append(t(44, top_y + 208, "EXTRACTED RESEARCH KEYWORDS (TF-IDF)", size=12, weight=700, color="#94A3B8"))
    tags = ["Multi-Agent Systems", "LLM Orchestration", "Database Sharding", "Higher Ed", "Turnitin Compliance", "Access ADODB"]
    ty = top_y + 225
    tx = 36
    for tag in tags:
        tw = len(tag) * 7.5 + 20
        if tx + tw > left_w + 10:
            tx = 36
            ty += 34
        res.append(b(tx, ty, tag, s["color"], s["color"], tw, 26))
        tx += tw + 10
        
    # Departmental Capacity Radar
    res.append(t(44, top_y + 340, "DEPARTMENT SUPERVISORY CAPACITY", size=12, weight=700, color="#94A3B8"))
    res.append(r(36, top_y + 360, left_w - 24, 110, rx=8, fill="#0B0F19", stroke="#1E293B"))
    res.append(t(48, top_y + 384, "Total Faculty Supervisors: 14 Professors / Doctors", size=11, color="#E2E8F0"))
    res.append(t(48, top_y + 406, "Senate Cap: Maximum 5 Supervisees Per Staff", size=11, color="#E2E8F0"))
    res.append(t(48, top_y + 428, "Current Active Load: 46 / 70 Slots Filled (65.7%)", size=11, weight=700, color="#10B981"))
    res.append(t(48, top_y + 450, "Unassigned Candidates Queue: 1 Remaining", size=11, weight=700, color="#F59E0B"))
    
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Run Full AI Vector Optimization", s["color"], "#000000", rx=8))
    
    # Right AI Vector Matched Recommendations
    right_x = 24 + left_w + 20
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    res.append(t(right_x + 24, top_y + 36, "AI Vector Cosine Similarity Recommendations", size=16, weight=800, color="#FFFFFF"))
    
    matches = [
        ("1", "Prof. I. A. Bello", "96.4% Match", "Distributed AI, Multi-Agent Systems, Educational Technologies", "3 / 5 Candidates (Capacity OK)", "#10B981", "Primary Recommendation"),
        ("2", "Dr. H. O. Salami", "88.7% Match", "Database Systems, Relational Architecture, Cloud Systems", "4 / 5 Candidates (Capacity OK)", "#38BDF8", "Co-Supervisor Match"),
        ("3", "Dr. K. A. Adeleke", "81.2% Match", "Machine Learning, Software Engineering, Telemetry Pipelines", "2 / 5 Candidates (Capacity OK)", "#F59E0B", "Alternative Match")
    ]
    my = top_y + 60
    for rank, name, match_score, expertise, load, col, note in matches:
        res.append(r(right_x + 20, my, right_w - 40, 140, rx=10, fill="#141E33", stroke=col))
        res.append(r(right_x + 36, my + 16, 32, 32, rx=8, fill=col, opacity=0.2))
        res.append(t(right_x + 52, my + 38, rank, size=15, weight=800, color=col, anchor="middle"))
        res.append(t(right_x + 80, my + 36, name, size=16, weight=800, color="#FFFFFF"))
        res.append(b(right_x + right_w - 150, my + 16, match_score, col, col, 110, 26))
        res.append(t(right_x + 80, my + 64, f"Domain Expertise: {expertise}", size=12, color="#CBD5E1"))
        res.append(t(right_x + 80, my + 86, f"Current Supervision Load: {load}", size=12, weight=600, color="#E2E8F0"))
        res.append(t(right_x + 80, my + 112, f"Recommendation Note: {note}", size=11, weight=700, color=col))
        res.append(btn(right_x + right_w - 170, my + 80, 130, 36, "Assign Supervisor", col, "#000000", rx=6))
        my += 156
        
    return res

def render_defense_rubric_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Defense Details & Panel Roster
    left_w = 400
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "EXAMINATION BOARD PANEL", size=15, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 96, rx=8, fill="#131F37", stroke="#253554"))
    res.append(t(48, top_y + 80, "Adeyemi Bashir (20/52CS/0084)", size=14, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 100, "MSc Dissertation Final Oral Defense", size=12, color=s["color"]))
    res.append(t(48, top_y + 120, "Date: Nov 14, 2024 at 10:00 AM • Senate Chamber", size=11, color="#CBD5E1"))
    res.append(t(48, top_y + 138, "Mode: Hybrid Physical & Zoom Teleconference", size=11, color="#10B981"))
    
    panel = [
        ("Dean of Postgraduate Studies", "Chief Examiner & Chair"),
        ("Prof. O. K. Lawal (UNILAG)", "External Examiner"),
        ("Prof. S. O. Balogun", "Internal Examiner"),
        ("Dr. A. M. Jimoh", "Head of Department (Moderator)"),
        ("Prof. I. A. Bello", "Primary Supervisor")
    ]
    py = top_y + 168
    for p_name, p_role in panel:
        res.append(r(36, py, left_w - 24, 46, rx=6, fill="#0B0F19", stroke="#1E293B"))
        res.append(t(48, py + 22, p_name, size=11, weight=700, color="#FFFFFF"))
        res.append(t(48, py + 38, p_role, size=10, color="#94A3B8"))
        py += 52
        
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Affix Committee Electronic Signatures", s["color"], "#000000", rx=8))
    
    # Right Scoring Rubric
    right_x = 24 + left_w + 20
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    res.append(t(right_x + 24, top_y + 36, "NUC Postgraduate 100-Point Scoring Rubric", size=16, weight=800, color="#FFFFFF"))
    
    criteria = [
        ("1. Originality & Formulation of Research Problem", 20, 18, "Clearly articulates gaps in modern institutional operating systems."),
        ("2. Literature Review & Theoretical Foundation", 15, 14, "Comprehensive grasp of multi-agent systems and academic governance."),
        ("3. Research Methodology & System Implementation", 25, 24, "Rigorous software architecture, two-way database sync, robust testing."),
        ("4. Experimental Results, Validation & Discussion", 25, 23, "Statistically validated latency drops and cosine vector precision."),
        ("5. Oral Defense Presentation & Q&A Mastery", 15, 14, "Eloquent defense with authoritative command of technical inquiry.")
    ]
    cy = top_y + 60
    for crit_name, max_pts, awarded_pts, remarks in criteria:
        res.append(r(right_x + 20, cy, right_w - 40, 78, rx=8, fill="#141E33", stroke="#253554"))
        res.append(t(right_x + 36, cy + 24, crit_name, size=12, weight=700, color="#FFFFFF"))
        res.append(b(right_x + right_w - 140, cy + 12, f"{awarded_pts} / {max_pts} Points", s["color"], s["color"], 100, 24))
        res.append(t(right_x + 36, cy + 50, f"Committee Remark: {remarks}", size=11, color="#94A3B8"))
        cy += 88
        
    # Total Score & Verdict Box
    res.append(r(right_x + 20, cy, right_w - 40, 90, rx=10, fill="#0F172A", stroke="#10B981"))
    res.append(t(right_x + 36, cy + 34, "TOTAL AGGREGATED SCORE", size=13, weight=800, color="#94A3B8"))
    res.append(t(right_x + 36, cy + 68, "93.0 / 100 (GRADE A - PASS WITH DISTINCTION)", size=20, weight=900, color="#10B981"))
    res.append(btn(right_x + right_w - 200, cy + 26, 160, 42, "Submit Final Senate Award", "#10B981", "#000000", rx=8))
    
    return res

def render_clean_slate_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Center Big Banner
    res.append(r(24, top_y, FRAME_W - 48, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    
    center_y = top_y + 50
    res.append(r(FRAME_W//2 - 60, center_y, 120, 120, rx=24, fill=s["color"], opacity=0.15, stroke=s["color"], stroke_width=2))
    res.append(t(FRAME_W//2, center_y + 70, "0", size=48, weight=900, color=s["color"], anchor="middle"))
    
    res.append(t(FRAME_W//2, center_y + 160, "Clean-Slate Database State: Ready for Pioneer Institution Onboarding", size=24, weight=800, color="#FFFFFF", anchor="middle"))
    res.append(t(FRAME_W//2, center_y + 190, "No higher institutions are currently registered in tbl_Institutions. The multi-tenant database is primed.", size=14, color="#94A3B8", anchor="middle"))
    
    # 4 Steps Cards
    steps = [
        ("Step 1: Institutional Profile", "Register university name, acronym, official emblem, and primary subdomain.", "Launch Step 1 →"),
        ("Step 2: Faculty Hierarchy", "Seed academic faculties, departments, degree tracks, and HODs.", "Configure Structure →"),
        ("Step 3: Governance Policies", "Define Turnitin similarity limits (<=15%) and supervisor workload caps.", "Set Thresholds →"),
        ("Step 4: Portal Licensure", "Activate SPSEMS, SIWES, and HOSTEL modules for the campus community.", "Authorize Portals →")
    ]
    card_w = (FRAME_W - 48 - 60) // 4
    for i, (st_title, st_desc, st_btn) in enumerate(steps):
        cx = 44 + i * (card_w + 16)
        cy = center_y + 230
        res.append(r(cx, cy, card_w, 240, rx=12, fill="#131F37", stroke="#253554"))
        res.append(r(cx + 20, cy + 20, 36, 36, rx=8, fill=s["color"], opacity=0.2))
        res.append(t(cx + 38, cy + 44, str(i + 1), size=16, weight=800, color=s["color"], anchor="middle"))
        res.append(t(cx + 20, cy + 84, st_title, size=14, weight=700, color="#FFFFFF"))
        res.append(t(cx + 20, cy + 112, st_desc, size=11, color="#94A3B8"))
        res.append(btn(cx + 20, cy + 180, card_w - 40, 36, st_btn, s["color"], "#000000", rx=6))
        
    return res

def render_sync_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    # Left Engine Health & Telemetry
    left_w = 400
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "MS 365 ACCESS SYNC BRIDGE", size=15, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 100, rx=8, fill="#131F37", stroke="#10B981"))
    res.append(t(48, top_y + 80, "TWO-WAY LIVE SYNC ENGINE", size=12, weight=700, color="#10B981"))
    res.append(t(48, top_y + 104, "SQLite (Local) ↔ MS Access (.accdb)", size=14, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 128, "ADODB OleDB Provider Connected (0ms Drift)", size=11, color="#94A3B8"))
    
    metrics = [
        ("Relational Tables", "16 Synchronized", "#10B981"),
        ("Sync Latency", "12 ms Roundtrip", "#38BDF8"),
        ("Total Records", "148,200 Audited", "#A855F7"),
        ("Lock Strategy", "Pessimistic Row Level", "#F59E0B")
    ]
    my = top_y + 172
    for lbl, val, col in metrics:
        res.append(r(36, my, left_w - 24, 46, rx=6, fill="#0B0F19", stroke="#1E293B"))
        res.append(t(48, my + 28, lbl, size=11, color="#94A3B8"))
        res.append(t(left_w, my + 28, val, size=12, weight=700, color=col, anchor="end"))
        my += 54
        
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Force Immediate Two-Way Resync", s["color"], "#000000", rx=8))
    
    # Right 16 Tables Status Table
    right_x = 24 + left_w + 20
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    res.append(t(right_x + 24, top_y + 36, "Relational Database Synchronized Tables (16)", size=16, weight=800, color="#FFFFFF"))
    
    tables_data = [
        ("tbl_Institutions", "Higher institution master profiles and subdomain slugs", "42 Rows", "100% Synced"),
        ("tbl_InstitutionSettings", "Thresholds, Turnitin cutoff %, and portal activations", "42 Rows", "100% Synced"),
        ("tbl_Users", "Central federated single sign-on user directory", "18,420 Rows", "100% Synced"),
        ("tbl_Faculties", "University academic faculties and dean allocations", "128 Rows", "100% Synced"),
        ("tbl_Departments", "Academic departments and program curricula", "340 Rows", "100% Synced"),
        ("tbl_Students", "Postgraduate and undergraduate student identities", "14,800 Rows", "100% Synced"),
        ("tbl_Supervisors", "Lecturers, professorial ranks, and supervisee quotas", "850 Rows", "100% Synced"),
        ("tbl_Projects", "Dissertation topics, abstracts, and milestone progression", "1,420 Rows", "100% Synced"),
        ("tbl_Submissions", "Chapter drafts, revisions, and PDF archival copies", "4,820 Rows", "100% Synced"),
        ("tbl_Evaluations", "Turnitin scores, defense rubrics, and examiner verdicts", "2,940 Rows", "100% Synced")
    ]
    ty = top_y + 56
    for t_name, t_desc, t_count, t_st in tables_data:
        res.append(r(right_x + 20, ty, right_w - 40, 48, rx=6, fill="#141E33", stroke="#253554"))
        res.append(t(right_x + 36, ty + 28, t_name, size=12, weight=700, color="#38BDF8", mono=True))
        res.append(t(right_x + 230, ty + 28, t_desc, size=11, color="#94A3B8"))
        res.append(t(right_x + right_w - 150, ty + 28, t_count, size=11, weight=600, color="#E2E8F0"))
        res.append(b(right_x + right_w - 90, ty + 12, t_st, "#10B981", "#10B981", 60, 22))
        ty += 54
        
    return res

print("Initialized all specialized layout renderers.")
