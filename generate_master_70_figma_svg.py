import os
import html
import subprocess
import shutil

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

def render_auth_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    w_left = 580
    res.append(r(24, top_y, w_left, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(r(50, top_y + 40, 72, 72, rx=16, fill=s["color"], opacity=0.2, stroke=s["color"], stroke_width=2))
    res.append(t(86, top_y + 83, "UNI", size=20, weight=900, color=s["color"], anchor="middle"))
    res.append(t(140, top_y + 68, "KWARA STATE UNIVERSITY, MALETE", size=18, weight=800, color="#FFFFFF"))
    res.append(t(140, top_y + 92, "Office of Academic Planning & Systems Integration", size=13, weight=500, color="#94A3B8"))
    res.append(t(50, top_y + 160, s.get("auth_headline", "Institutional Portal Workstation"), size=24, weight=800, color="#FFFFFF"))
    res.append(t(50, top_y + 190, s.get("auth_description", "Authorized portal for verified academic scholars and university officers."), size=13, weight=400, color="#94A3B8"))
    
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
    
    w_right = FRAME_W - 48 - w_left - 24
    rx_pos = 24 + w_left + 24
    res.append(r(rx_pos, top_y, w_right, h, rx=14, fill="#111827", stroke="#1F2937"))
    form_y = top_y + 40
    res.append(t(rx_pos + 40, form_y, s.get("form_title", "Sign in to your Account"), size=22, weight=800, color="#FFFFFF"))
    res.append(t(rx_pos + 40, form_y + 24, s.get("form_subtitle", "Enter your credentials to access your session."), size=13, weight=400, color="#94A3B8"))
    
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
        
    res.append(r(rx_pos + 40, inp_y + 6, 16, 16, rx=4, fill=s["color"]))
    res.append(t(rx_pos + 66, inp_y + 19, "Remember my institutional session on this device", size=12, color="#94A3B8"))
    res.append(t(rx_pos + w_right - 40, inp_y + 19, "Forgot Security PIN?", size=12, weight=600, color=s["color"], anchor="end"))
    
    res.append(btn(rx_pos + 40, inp_y + 40, w_right - 80, 50, s.get("btn_label", "Sign In to Portal Workstation"), s["color"], "#000000", rx=8))
    
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
    
    nav = s.get("nav_items", ["Overview", "Submissions", "Reviews", "Examinations", "Clearance", "Settings"])
    user = s.get("user_info", ("Prof. I. A. Bello", "Senior Academic Supervisor"))
    res.extend(render_sidebar(24, top_y, sb_w, h, s.get("active_nav", "Overview"), nav, s["portal"], user, s["color"]))
    
    main_x = 24 + sb_w + 20
    main_w = FRAME_W - 48 - sb_w - 20
    
    m_w = (main_w - 32) // 3
    for i, (lbl, val, sub) in enumerate(s.get("metrics", [("Total Load", "14 Active", "Normal"), ("Pending", "3 Drafts", "Due 48h"), ("Score Avg", "88.4%", "Distinction")])):
        mx = main_x + i * (m_w + 16)
        res.append(r(mx, top_y, m_w, 92, rx=12, fill="#0F172A", stroke="#1E293B"))
        res.append(t(mx + 20, top_y + 28, lbl, size=12, weight=600, color="#94A3B8"))
        res.append(t(mx + 20, top_y + 60, val, size=24, weight=800, color="#FFFFFF"))
        res.append(b(mx + m_w - 110, top_y + 20, sub, s["color"], s["color"], 95, 22))
        
    tbl_y = top_y + 112
    tbl_h = h - 112
    res.append(r(main_x, tbl_y, main_w, tbl_h, rx=14, fill="#111827", stroke="#1F2937"))
    
    res.append(t(main_x + 24, tbl_y + 36, s.get("table_title", "Operational Queue & Verification Registry"), size=17, weight=800, color="#FFFFFF"))
    res.append(btn(main_x + main_w - 160, tbl_y + 16, 136, 34, "+ New Entry", s["color"], "#000000", rx=6))
    
    cols = s.get("table_headers", ["Candidate / Staff", "Program / Level", "Current Milestone", "Evaluation State", "Actions"])
    c_w = (main_w - 48) // len(cols)
    res.append(r(main_x + 16, tbl_y + 60, main_w - 32, 34, rx=6, fill="#0B0F19"))
    for ci, c_name in enumerate(cols):
        res.append(t(main_x + 32 + ci * c_w, tbl_y + 81, c_name.upper(), size=11, weight=700, color="#6B7280"))
        
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
    
    doc_x = 24 + sb_w + 16
    doc_w = 680
    res.append(r(doc_x, top_y, doc_w, h, rx=12, fill="#1E293B", stroke="#334155"))
    res.append(r(doc_x, top_y, doc_w, 42, rx=12, fill="#0F172A"))
    res.append(t(doc_x + 20, top_y + 26, "Adeyemi_Bashir_MSc_Dissertation_Chapter4_v4.1.pdf   •   Page 42 of 118", size=12, weight=600, color="#94A3B8"))
    res.append(t(doc_x + doc_w - 20, top_y + 26, "ZOOM 100%   |   FIT WIDTH", size=11, weight=700, color="#64748B", anchor="end"))
    
    page_y = top_y + 54
    page_w = doc_w - 40
    page_h = h - 68
    res.append(r(doc_x + 20, page_y, page_w, page_h, rx=6, fill="#FFFFFF"))
    
    res.append(t(doc_x + 50, page_y + 40, "CHAPTER 4: EXPERIMENTAL EVALUATION & RESULTS", size=16, weight=800, color="#0F172A"))
    res.append(t(doc_x + 50, page_y + 64, "4.3 Quantitative Analysis of Multi-Agent Dispatch Latency", size=13, weight=700, color="#1E293B"))
    
    paras = [
        "In this section, the proposed autonomous agent orchestration engine was benchmarked against",
        "traditional monolithic REST dispatch architectures. As illustrated in Table 4.2, the mean query",
        "response latency under a 5,000 concurrent student load dropped significantly from 340ms to 42ms."
    ]
    for pi, pl in enumerate(paras):
        res.append(t(doc_x + 50, page_y + 95 + pi * 20, pl, size=11, color="#334155"))
        
    res.append(r(doc_x + 48, page_y + 165, page_w - 96, 44, rx=4, fill="#FEF08A"))
    res.append(t(doc_x + 52, page_y + 185, "Highlight: 'The cosine similarity matching algorithm achieved 96.4% precision when aligning", size=11, weight=700, color="#854D0E"))
    res.append(t(doc_x + 52, page_y + 202, "postgraduate research proposals with faculty supervisor publication vectors.'", size=11, weight=700, color="#854D0E"))
    
    res.append(r(doc_x + 50, page_y + 230, page_w - 100, 50, rx=4, fill="#F8FAFC", stroke="#E2E8F0"))
    res.append(t(doc_x + page_w // 2, page_y + 260, "Similarity(A, B) = cos(θ) = ( A • B ) / ( ||A|| ||B|| )", size=12, weight=700, color="#0F172A", anchor="middle", mono=True))
    
    more_paras = [
        "Furthermore, ablation studies confirm that the MS 365 Access ADODB bridge introduces zero drift",
        "across all 16 relational tables when operating under continuous background synchronization.",
        "The empirical findings strictly confirm our initial theoretical hypotheses formulated in Section 1.3."
    ]
    for pi, pl in enumerate(more_paras):
        res.append(t(doc_x + 50, page_y + 310 + pi * 20, pl, size=11, color="#334155"))
        
    comm_x = doc_x + doc_w + 16
    comm_w = FRAME_W - comm_x - 24
    res.append(r(comm_x, top_y, comm_w, h, rx=12, fill="#0F172A", stroke="#1E293B"))
    res.append(t(comm_x + 20, top_y + 36, "SUPERVISOR ANNOTATIONS", size=13, weight=800, color="#FFFFFF"))
    
    res.append(r(comm_x + 16, top_y + 60, comm_w - 32, 130, rx=10, fill="#131F37", stroke=s["color"]))
    res.append(t(comm_x + 28, top_y + 84, "Prof. I. A. Bello (Supervisor)", size=12, weight=700, color="#FFFFFF"))
    res.append(t(comm_x + 28, top_y + 102, "OCT 14, 2024 at 14:22 • Chapter 4 Passage 2", size=10, color="#94A3B8"))
    res.append(t(comm_x + 28, top_y + 126, "Please verify if the 96.4% precision was evaluated", size=11, color="#E2E8F0"))
    res.append(t(comm_x + 28, top_y + 144, "under 5-fold cross validation. Add p-values.", size=11, color="#E2E8F0"))
    res.append(b(comm_x + comm_w - 110, top_y + 72, "Action Needed", "#EF4444", "#EF4444"))
    
    res.append(r(comm_x + 16, top_y + 204, comm_w - 32, 110, rx=10, fill="#131F37", stroke="#253554"))
    res.append(t(comm_x + 28, top_y + 228, "Prof. I. A. Bello (Supervisor)", size=12, weight=700, color="#FFFFFF"))
    res.append(t(comm_x + 28, top_y + 246, "OCT 14, 2024 at 14:35 • Equation 4.1", size=10, color="#94A3B8"))
    res.append(t(comm_x + 28, top_y + 270, "Vector formulation is mathematically sound.", size=11, color="#10B981"))
    res.append(b(comm_x + comm_w - 90, top_y + 216, "Approved", "#10B981", "#10B981"))
    
    res.append(btn(comm_x + 16, top_y + h - 110, comm_w - 32, 42, "Approve Milestone Chapter", "#10B981", "#000000", rx=8))
    res.append(btn(comm_x + 16, top_y + h - 56, comm_w - 32, 42, "Request Specific Revisions", "#EF4444", "#FFFFFF", rx=8))
    return res

def render_turnitin_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    left_w = 460
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "TURNITIN SIMILARITY AUDIT", size=16, weight=800, color="#FFFFFF"))
    res.append(t(44, top_y + 56, "Academic Document Similarity Index & AI Verification", size=12, color="#94A3B8"))
    
    dial_y = top_y + 80
    res.append(r(44, dial_y, left_w - 40, 220, rx=12, fill="#131F37", stroke="#253554"))
    res.append(f'<circle cx="{44 + (left_w - 40)//2}" cy="{dial_y + 100}" r="75" stroke="#1E293B" stroke-width="16" fill="none"/>')
    res.append(f'<circle cx="{44 + (left_w - 40)//2}" cy="{dial_y + 100}" r="75" stroke="#10B981" stroke-width="16" stroke-dasharray="471" stroke-dashoffset="417" stroke-linecap="round" fill="none"/>')
    res.append(t(44 + (left_w - 40)//2, dial_y + 98, "11.4%", size=32, weight=900, color="#10B981", anchor="middle"))
    res.append(t(44 + (left_w - 40)//2, dial_y + 124, "SIMILARITY INDEX", size=11, weight=700, color="#94A3B8", anchor="middle"))
    res.append(b(44 + (left_w - 40)//2 - 60, dial_y + 175, "VERIFIED PASS (<= 15%)", "#10B981", "#10B981", 120, 26))
    
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
    
    center_x = 24 + left_w + 16
    center_w = 680
    res.append(r(center_x, top_y, center_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    
    res.append(t(center_x + 24, top_y + 34, "Block 1: Real-Time Bed Space Allocation Rack", size=16, weight=800, color="#FFFFFF"))
    res.append(r(center_x + center_w - 360, top_y + 18, 12, 12, rx=3, fill="#10B981"))
    res.append(t(center_x + center_w - 342, top_y + 28, "Available", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 260, top_y + 18, 12, 12, rx=3, fill="#EF4444"))
    res.append(t(center_x + center_w - 242, top_y + 28, "Occupied", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 160, top_y + 18, 12, 12, rx=3, fill="#38BDF8"))
    res.append(t(center_x + center_w - 142, top_y + 28, "Selected", size=11, color="#94A3B8"))
    res.append(r(center_x + center_w - 70, top_y + 18, 12, 12, rx=3, fill="#F59E0B"))
    res.append(t(center_x + center_w - 52, top_y + 28, "Reserved", size=11, color="#94A3B8"))
    
    room_y = top_y + 54
    for ri in range(6):
        rm_num = 101 + ri
        row_y = room_y + ri * 96
        res.append(r(center_x + 20, row_y, center_w - 40, 84, rx=10, fill="#0F172A", stroke="#1E293B"))
        res.append(t(center_x + 36, row_y + 48, f"ROOM {rm_num}", size=14, weight=800, color="#FFFFFF"))
        
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
            
    right_x = center_x + center_w + 16
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(right_x + 20, top_y + 36, "SELECTED BED SPACE", size=14, weight=800, color="#FFFFFF"))
    
    res.append(r(right_x + 16, top_y + 56, right_w - 32, 120, rx=10, fill="#131F37", stroke="#38BDF8"))
    res.append(t(right_x + 28, top_y + 80, "Room 104 • Bunk A Top", size=16, weight=800, color="#38BDF8"))
    res.append(t(right_x + 28, top_y + 102, "Hall of Residence A (Male Executive)", size=12, color="#E2E8F0"))
    res.append(t(right_x + 28, top_y + 124, "Bed Space Key ID: KWA-HRA-104-AT", size=11, color="#94A3B8"))
    res.append(t(right_x + 28, top_y + 150, "Reservation Lock: 23 hrs 45 mins left", size=11, weight=700, color="#F59E0B"))
    
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
    
    left_w = 280
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "SIWES TRAINEE PROFILE", size=14, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 110, rx=8, fill="#131F37", stroke="#253554"))
    res.append(t(48, top_y + 80, "Chinedu Eze", size=15, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 100, "Matric: 21/25EE/0114", size=12, color="#94A3B8"))
    res.append(t(48, top_y + 120, "Electrical Engineering (400L)", size=11, color="#CBD5E1"))
    res.append(t(48, top_y + 144, "TotalEnergies E&P Nigeria", size=11, weight=700, color="#F59E0B"))
    
    res.append(t(44, top_y + 190, "ATTACHMENT TIMELINE", size=12, weight=700, color="#94A3B8"))
    wy = top_y + 210
    for w_num in range(12, 17):
        is_cur = (w_num == 14)
        res.append(r(36, wy, left_w - 24, 38, rx=6, fill="#F59E0B" if is_cur else "#0B0F19", opacity=0.18 if is_cur else 0.5, stroke="#F59E0B" if is_cur else None))
        res.append(t(48, wy + 24, f"Week {w_num} of 24", size=12, weight=700, color="#FFFFFF" if is_cur else "#94A3B8"))
        res.append(t(left_w - 10, wy + 24, "STAMPED" if w_num < 14 else ("ACTIVE" if w_num == 14 else "PENDING"), size=10, weight=700, color="#10B981" if w_num < 14 else "#F59E0B", anchor="end"))
        wy += 46
        
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Export ITF Form 8 PDF", "#F59E0B", "#000000", rx=8))
    
    center_x = 24 + left_w + 16
    center_w = 680
    res.append(r(center_x, top_y, center_w, h, rx=14, fill="#111827", stroke="#1F2937"))
    res.append(t(center_x + 24, top_y + 36, "Week 14 Electronic Logbook: Daily Engineering Activities", size=16, weight=800, color="#FFFFFF"))
    
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
        
    res.append(r(center_x + 20, dy, center_w - 40, 70, rx=8, fill="#0B0F19", stroke="#253554"))
    res.append(t(center_x + 36, dy + 28, "Attached Engineering Schematic (SLD-Substation-33kV.png)", size=12, weight=700, color="#38BDF8"))
    res.append(t(center_x + 36, dy + 48, "Verified SHA-256 Hash: 8f4b2c1e9... • Uploaded by Trainee via Android Tablet", size=10, color="#94A3B8"))
    res.append(btn(center_x + center_w - 160, dy + 18, 120, 34, "View CAD Sheet", "#38BDF8", "#000000", rx=6))
    
    right_x = center_x + center_w + 16
    right_w = FRAME_W - right_x - 24
    res.append(r(right_x, top_y, right_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(right_x + 20, top_y + 36, "INDUSTRY SUPERVISOR SIGN-OFF", size=13, weight=800, color="#FFFFFF"))
    
    res.append(r(right_x + 16, top_y + 58, right_w - 32, 190, rx=10, fill="#131F37", stroke="#F59E0B"))
    res.append(t(right_x + 28, top_y + 84, "TotalEnergies E&P Nigeria", size=14, weight=800, color="#FFFFFF"))
    res.append(t(right_x + 28, top_y + 104, "Engr. Babatunde Williams, FNSE", size=12, weight=700, color="#F59E0B"))
    res.append(t(right_x + 28, top_y + 124, "Chief Substation Engineer", size=11, color="#94A3B8"))
    res.append(t(right_x + 28, top_y + 150, "GPS Stamp: 4.8156° N, 7.0498° E", size=11, color="#CBD5E1"))
    res.append(t(right_x + 28, top_y + 172, "Date: 18-OCT-2024 16:45:12", size=11, color="#CBD5E1"))
    res.append(b(right_x + 28, top_y + 195, "VERIFIED CORPORATE STAMP", "#10B981", "#10B981", 170, 24))
    
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
    
    left_w = 420
    res.append(r(24, top_y, left_w, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    res.append(t(44, top_y + 36, "CANDIDATE DISSERTATION PROFILE", size=15, weight=800, color="#FFFFFF"))
    
    res.append(r(36, top_y + 56, left_w - 24, 130, rx=10, fill="#131F37", stroke="#253554"))
    res.append(t(48, top_y + 80, "Adeyemi Bashir", size=16, weight=800, color="#FFFFFF"))
    res.append(t(48, top_y + 102, "Matric: 20/52CS/0084  •  MSc Computer Science", size=12, color=s["color"]))
    res.append(t(48, top_y + 128, "Topic: Autonomous Multi-Agent Orchestration for", size=12, weight=600, color="#E2E8F0"))
    res.append(t(48, top_y + 146, "Higher Education Institutional Operating Systems", size=12, weight=600, color="#E2E8F0"))
    res.append(t(48, top_y + 170, "Proposal Vetted: Senate Approved", size=11, color="#10B981"))
    
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
        
    res.append(t(44, top_y + 340, "DEPARTMENT SUPERVISORY CAPACITY", size=12, weight=700, color="#94A3B8"))
    res.append(r(36, top_y + 360, left_w - 24, 110, rx=8, fill="#0B0F19", stroke="#1E293B"))
    res.append(t(48, top_y + 384, "Total Faculty Supervisors: 14 Professors / Doctors", size=11, color="#E2E8F0"))
    res.append(t(48, top_y + 406, "Senate Cap: Maximum 5 Supervisees Per Staff", size=11, color="#E2E8F0"))
    res.append(t(48, top_y + 428, "Current Active Load: 46 / 70 Slots Filled (65.7%)", size=11, weight=700, color="#10B981"))
    res.append(t(48, top_y + 450, "Unassigned Candidates Queue: 1 Remaining", size=11, weight=700, color="#F59E0B"))
    
    res.append(btn(36, top_y + h - 56, left_w - 24, 42, "Run Full AI Vector Optimization", s["color"], "#000000", rx=8))
    
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
        
    res.append(r(right_x + 20, cy, right_w - 40, 90, rx=10, fill="#0F172A", stroke="#10B981"))
    res.append(t(right_x + 36, cy + 34, "TOTAL AGGREGATED SCORE", size=13, weight=800, color="#94A3B8"))
    res.append(t(right_x + 36, cy + 68, "93.0 / 100 (GRADE A - PASS WITH DISTINCTION)", size=20, weight=900, color="#10B981"))
    res.append(btn(right_x + right_w - 200, cy + 26, 160, 42, "Submit Final Senate Award", "#10B981", "#000000", rx=8))
    return res

def render_clean_slate_layout(s):
    res = render_frame_base(s)
    top_y = 126
    h = FRAME_H - top_y - 64
    
    res.append(r(24, top_y, FRAME_W - 48, h, rx=14, fill="#0F172A", stroke="#1E293B"))
    center_y = top_y + 50
    res.append(r(FRAME_W//2 - 60, center_y, 120, 120, rx=24, fill=s["color"], opacity=0.15, stroke=s["color"], stroke_width=2))
    res.append(t(FRAME_W//2, center_y + 70, "0", size=48, weight=900, color=s["color"], anchor="middle"))
    
    res.append(t(FRAME_W//2, center_y + 160, "Clean-Slate Database State: Ready for Pioneer Institution Onboarding", size=24, weight=800, color="#FFFFFF", anchor="middle"))
    res.append(t(FRAME_W//2, center_y + 190, "No higher institutions are currently registered in tbl_Institutions. The multi-tenant database is primed.", size=14, color="#94A3B8", anchor="middle"))
    
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

# ─────────────────────────────────────────────────────────────────────────────
# 70 SCREENS METADATA SPECIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_complete_70_screens():
    screens = []
    
    # Category 1: Front Door & Onboarding (1 - 6)
    screens.append({
        "id": "CS-01", "title": "Main Landing Page Hero", "portal": "CampusSphere", "role": "Public Visitor", "route": "/",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "NUC Accreditation Baseline §1.0", "archetype": "dashboard",
        "subtitle": "Unified Higher Education Operating System Front-Door",
        "metrics": [("Active Universities", "42 Verified", "+8 this term"), ("Enrolled Scholars", "85,420 Active", "99.8% Uptime"), ("Research Throughput", "₦4.8B Managed", "TETFund Compliant")],
        "table_title": "Accredited Higher Institution Network (Active Gateways)",
        "table_headers": ["Institution", "State", "Active Portals", "Accreditation", "Actions"],
        "table_rows": [
            ["Kwara State University (KWASU)", "Kwara", "SPSEMS • SIWES • HOSTEL", "NUC Full 2024", "Enter Portal →"],
            ["University of Ilorin (UNILORIN)", "Kwara", "SPSEMS • SIWES", "NUC Full 2024", "Enter Portal →"],
            ["Federal University Lokoja (FUL)", "Kogi", "SPSEMS Only", "NUC Full 2023", "Enter Portal →"],
            ["Landmark University (LU)", "Kwara", "HOSTEL • SIWES", "NUC Full 2024", "Provisioning →"]
        ]
    })
    screens.append({
        "id": "CS-02", "title": "Institutional Directory Side Panel", "portal": "CampusSphere", "role": "Public Visitor", "route": "/directory",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "Federal Education Registry Audit §2.4", "archetype": "dashboard",
        "subtitle": "Accredited University Subdomain Directory & Search",
        "metrics": [("Federal Campuses", "18 Connected", "NUC Validated"), ("State Campuses", "16 Connected", "Full Compliance"), ("Private Campuses", "8 Connected", "ISO Certified")],
        "table_title": "Directory Search & Filtering Index",
        "table_headers": ["Code", "Institution Name", "Vice-Chancellor / Contact", "Domain Route", "Actions"],
        "table_rows": [
            ["KWASU", "Kwara State University, Malete", "Prof. M. M. Akanbi (VC)", "kwasu.campussphere.edu.ng", "Select Tenant →"],
            ["UNILORIN", "University of Ilorin", "Prof. W. O. Egbewole (VC)", "unilorin.campussphere.edu.ng", "Select Tenant →"],
            ["OAU", "Obafemi Awolowo University", "Prof. A. S. Bamire (VC)", "oau.campussphere.edu.ng", "Select Tenant →"],
            ["ABU", "Ahmadu Bello University", "Prof. K. Bala (VC)", "abu.campussphere.edu.ng", "Select Tenant →"]
        ]
    })
    screens.append({
        "id": "CS-03", "title": "Clean-Slate Zero State", "portal": "CampusSphere", "role": "System Admin", "route": "/directory/clean-slate",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "Zero-Tenant Isolation Initial State", "archetype": "clean_slate",
        "subtitle": "Pioneer Institution Onboarding Launchpad (0 Institutions Registered)"
    })
    screens.append({
        "id": "CS-04", "title": "Onboarding Step 1: Profile & Domain", "portal": "Onboarding", "role": "University Registrar", "route": "/onboard/step-1",
        "db": "tbl_Institutions", "color": "#8B5CF6", "compliance": "NUC Identity Gazette Validation", "archetype": "auth",
        "subtitle": "University Identity, Official Emblem & DNS Subdomain Reservation",
        "auth_headline": "Pioneer Institution Onboarding",
        "auth_description": "Establish your university identity on the national higher education operating system.",
        "form_title": "Register University Profile",
        "form_subtitle": "Step 1 of 4: Primary Identity & Subdomain Allocation",
        "form_inputs": [
            ("Official University Name (Gazette)", "Kwara State University, Malete"),
            ("Institutional Acronym & Subdomain Slug", "kwasu (.campussphere.edu.ng)"),
            ("Registrar Official Verification Email", "registrar@kwasu.edu.ng")
        ],
        "btn_label": "Save Profile & Proceed to Step 2 →"
    })
    screens.append({
        "id": "CS-05", "title": "Onboarding Step 2: Academic Hierarchy", "portal": "Onboarding", "role": "Academic Planning", "route": "/onboard/step-2",
        "db": "tbl_Faculties", "color": "#8B5CF6", "compliance": "NUC Benchmark Minimum Academic Standards (BMAS)", "archetype": "dashboard",
        "subtitle": "Faculties, Departments & Postgraduate Degree Program Seeding",
        "metrics": [("Faculties Seeded", "8 Faculties", "BMAS Aligned"), ("Departments", "42 Departments", "Postgrad Active"), ("Degree Programs", "18 MSc / 12 PhD", "NUC Approved")],
        "table_title": "Configured Academic Faculties & Quotas",
        "table_headers": ["Faculty Name", "Departments Count", "Postgraduate Degrees", "Dean of Faculty", "Actions"],
        "table_rows": [
            ["Faculty of Information & Comm. Tech", "4 Departments", "MSc CS, PhD CS, MSc Cyber", "Prof. I. A. Bello", "Configure Depts →"],
            ["Faculty of Engineering & Technology", "6 Departments", "MEng Mechanical, Civil, Electrical", "Prof. K. A. Adeleke", "Configure Depts →"],
            ["Faculty of Pure & Applied Sciences", "8 Departments", "MSc Biochemistry, Microbiology", "Prof. H. O. Salami", "Configure Depts →"],
            ["Faculty of Management & Social Sciences", "7 Departments", "MSc Accounting, MBA, PhD Econ", "Prof. S. O. Balogun", "Configure Depts →"]
        ]
    })
    screens.append({
        "id": "CS-06", "title": "Onboarding Step 3 & 4: Policies & Portals", "portal": "Onboarding", "role": "University Registrar", "route": "/onboard/step-3",
        "db": "tbl_InstitutionSettings", "color": "#8B5CF6", "compliance": "Senate Regulations & Multi-Portal Licensure", "archetype": "dashboard",
        "subtitle": "Turnitin Cutoff Limits, Supervisor Quotas & Portal Activation Toggles",
        "metrics": [("SPSEMS Portal", "ACTIVATED (Tier 1)", "Dissertations Active"), ("SIWES Portal", "PENDING INTEGRATION", "Beta License"), ("HOSTEL Portal", "PENDING INTEGRATION", "Staging Matrix")],
        "table_title": "Enforced Academic Policy Thresholds",
        "table_headers": ["Parameter", "Configured Limit", "Regulatory Baseline", "Enforcement Engine", "Actions"],
        "table_rows": [
            ["Turnitin Similarity Limit", "15% Maximum Overlap", "NUC Guideline <= 20%", "Automated Document Lock", "Adjust Limit"],
            ["Max Supervisees Per Professor", "5 Postgraduate Scholars", "Senate Policy 2024", "AI Quota Enforcement", "Adjust Quota"],
            ["Defense Grading Rubric", "100-Point Standard", "Postgraduate Board", "Digital Examination Panel", "Edit Rubric"],
            ["Plagiarism Action Threshold", "Auto-Reject on 3rd Submission", "Academic Integrity Council", "Disciplinary Committee Flag", "View Policy"]
        ]
    })

    # Category 2: Gateways (7 - 10)
    screens.append({
        "id": "GW-01", "title": "University Multi-Portal Selection Hub", "portal": "Gateway", "role": "Institutional Member", "route": "/login/:slug",
        "db": "tbl_Institutions", "color": "#3B82F6", "compliance": "Federated Multi-Portal Routing Framework", "archetype": "dashboard",
        "subtitle": "Kwara State University Central Access Hub & Gateway Selector",
        "metrics": [("Active Session", "2024/2025 Harmattan", "Live"), ("Campus Users", "18,420 Enrolled", "SSO Active"), ("Security Tier", "ISO 27001 Certified", "MFA Enforced")],
        "table_title": "Available University Portals & Service Workstations",
        "table_headers": ["Portal Designation", "Service Domain", "Target Demographics", "Access Clearance", "Actions"],
        "table_rows": [
            ["PORTAL 01: SPSEMS", "Postgraduate Dissertation & Thesis Defense", "PG Students, Supervisors, Dean", "ACTIVE & INTEGRATED", "Enter SPSEMS Gateway →"],
            ["PORTAL 02: SIWES", "Industrial Attachment & Placement Logbook", "Undergraduates, Industry Staff, Coord.", "ACTIVE & INTEGRATED", "Enter SIWES Gateway →"],
            ["PORTAL 03: HOSTEL", "Hall Accommodation & 3D Bed Matrix", "All Students, Wardens, Housing Dir.", "ACTIVE & INTEGRATED", "Enter HOSTEL Gateway →"],
            ["CENTRAL SSO", "Unified Identity & Active Directory", "All University Staff & Students", "ACTIVE & VERIFIED", "Manage Profile →"]
        ]
    })
    screens.append({
        "id": "GW-02", "title": "University Single-Sign-On Gateway", "portal": "Gateway", "role": "All Users", "route": "/login/:slug/sso",
        "db": "tbl_Users", "color": "#3B82F6", "compliance": "OAuth 2.0 / OpenID Connect Enterprise Protocol", "archetype": "auth",
        "subtitle": "Centralized Active Directory & Microsoft 365 Authentication",
        "auth_headline": "University Central SSO Gateway",
        "auth_description": "Sign in once with your official university credentials to access SPSEMS, SIWES, and HOSTEL.",
        "form_title": "Institutional Single Sign-On",
        "form_subtitle": "Microsoft 365 & Google Workspace Unified Authentication",
        "form_inputs": [
            ("Institutional Email Address", "username@kwasu.edu.ng"),
            ("Campus Password", "••••••••••••••••"),
            ("Two-Factor Authentication Code", "481 920")
        ],
        "btn_label": "Authenticate Session →"
    })
    screens.append({
        "id": "GW-03", "title": "Institution Portal Provisioning Hub", "portal": "Gateway", "role": "ICT Director", "route": "/admin/:slug/portals",
        "db": "tbl_InstitutionSettings", "color": "#3B82F6", "compliance": "Semester Lifecycle & Module Governance", "archetype": "dashboard",
        "subtitle": "Tenant Licensing & Semester-by-Semester Portal Enablement",
        "metrics": [("Active Modules", "3 / 3 Portals Live", "All Verified"), ("API Latency", "14 ms Mean", "Zero Drift"), ("Database Health", "16 Tables Synced", "ADODB Bridge")],
        "table_title": "Campus Portal Enablement & Module Lifecycle",
        "table_headers": ["Module Name", "License Tier", "Concurrency Limit", "Health Telemetry", "Actions"],
        "table_rows": [
            ["SPSEMS Dissertation Supervision", "Enterprise Unlimited", "1,500 Concurrent Defenses", "Healthy (11ms)", "Module Settings →"],
            ["SIWES Industrial Work Scheme", "Campus Enterprise", "3,500 Active Trainees", "Healthy (14ms)", "Module Settings →"],
            ["HOSTEL Smart Residential Matrix", "Campus Enterprise", "8,500 Managed Beds", "Healthy (9ms)", "Module Settings →"],
            ["Access ADODB Two-Way Sync Engine", "Core Background Worker", "16 Relational Tables", "100% Consistent", "Force Resync →"]
        ]
    })
    screens.append({
        "id": "GW-04", "title": "Cross-Portal Identity Switcher", "portal": "Gateway", "role": "Student / Staff", "route": "/user/account-switcher",
        "db": "tbl_Users", "color": "#3B82F6", "compliance": "Identity Token Federation (JWT RSA-256)", "archetype": "dashboard",
        "subtitle": "Seamless Session Switching Across SPSEMS, SIWES, and HOSTEL",
        "metrics": [("Active Identities", "2 Connected Profiles", "Single Sign-On"), ("Current Token", "JWT RSA-256", "Valid 8h"), ("Security Posture", "Fingerprint Verified", "Malete, Nigeria")],
        "table_title": "Active Federated Portal Workspaces",
        "table_headers": ["Portal Designation", "Associated Identity", "Primary Role", "Department / Unit", "Actions"],
        "table_rows": [
            ["SPSEMS Dissertation Portal", "Adeyemi Bashir (20/52CS/0084)", "MSc Candidate", "Computer Science", "Switch Workspace →"],
            ["HOSTEL Accommodation Portal", "Adeyemi Bashir (20/52CS/0084)", "Resident Scholar", "Hall A, Room 104, Bunk A", "Switch Workspace →"],
            ["SIWES Industrial Portal (Archive)", "Adeyemi Bashir (18/52CS/0012)", "Completed Trainee", "TotalEnergies Placement", "View Logbook →"],
            ["University Bursary Account", "Adeyemi Bashir (Student Account)", "Tuition Verified", "University Bursary", "View Receipts →"]
        ]
    })

    # Category 3: SPSEMS (11 - 28)
    screens.append({
        "id": "SP-ST-01", "title": "Student SPSEMS Login", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/:slug/login/student",
        "db": "tbl_Students", "color": "#10B981", "compliance": "Postgraduate Matriculation Authentication Standard", "archetype": "auth",
        "subtitle": "Postgraduate Scholar Dissertation Workstation Access",
        "auth_headline": "SPSEMS Scholar Workstation",
        "auth_description": "Access your dissertation draft, split-screen feedback, Turnitin reports, and defense scheduling.",
        "form_title": "Sign in as Postgraduate Scholar",
        "form_subtitle": "Enter your Postgraduate Matriculation Number & Security PIN",
        "form_inputs": [
            ("Postgraduate Matriculation Number", "20/52CS/0084"),
            ("Dissertation Security Key / PIN", "••••••••••••••••"),
            ("Current Academic Session", "2024/2025 Harmattan Semester")
        ],
        "btn_label": "Enter Dissertation Workspace →"
    })
    screens.append({
        "id": "SP-ST-02", "title": "Dissertation Command Center", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/dashboard",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "NUC 5-Stage Dissertation Progression Framework", "archetype": "dashboard",
        "subtitle": "5-Stage Milestone Tracker, Supervisor Allocation & Turnitin Telemetry",
        "metrics": [("Milestone Progress", "Stage 4 of 5", "Results & Discussion"), ("Turnitin Similarity", "11.4% Overlap", "Threshold <= 15%"), ("Assigned Supervisor", "Prof. I. A. Bello", "Feedback Logged")],
        "table_title": "Dissertation Milestone Progression Tracker",
        "table_headers": ["Milestone Stage", "Deliverable Scope", "Submission Date", "Review State", "Actions"],
        "table_rows": [
            ["Stage 1: Proposal & Concept Note", "Problem formulation and research domain", "12-JAN-2024", "Senate Approved", "View Certificate →"],
            ["Stage 2: Literature Synthesis", "Chapter 2 theoretical review & prior art", "15-APR-2024", "Approved by Supervisor", "View Diffs →"],
            ["Stage 3: Research Methodology", "Chapter 3 mathematical formulation & design", "02-JUL-2024", "Approved by Supervisor", "View Diffs →"],
            ["Stage 4: Experimental Results", "Chapter 4 benchmark evaluation & data", "14-OCT-2024", "Under Active Review", "Open Annotator →"],
            ["Stage 5: Oral Viva Defense", "Final dissertation defense before external panel", "PENDING", "Awaiting Clearance", "Pre-Defense Prep →"]
        ]
    })
    screens.append({
        "id": "SP-ST-03", "title": "Topic & Concept Note Studio", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/proposal",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "Postgraduate Board Research Vetting Policy", "archetype": "dashboard",
        "subtitle": "Research Title Registration, Abstract Submission & Keyword Vector Tagging",
        "metrics": [("Topic Status", "APPROVED BY HOD", "Computer Science"), ("Research Domain", "Artificial Intelligence", "Multi-Agent Systems"), ("Vector Match Score", "96.4% Cosine", "Supervisor Aligned")],
        "table_title": "Submitted Research Proposals & Revision History",
        "table_headers": ["Submission Ref", "Proposed Research Topic", "Submission Date", "Committee Verdict", "Actions"],
        "table_rows": [
            ["PROP-2024-0084-v2", "Autonomous Multi-Agent Orchestration for Higher Education Systems", "12-JAN-2024", "APPROVED AS SUBMITTED", "View Approval Form →"],
            ["PROP-2024-0084-v1", "Multi-Agent Systems in University Management", "10-DEC-2023", "REVISE & RESUBMIT", "View Comments →"]
        ]
    })
    screens.append({
        "id": "SP-ST-04", "title": "Chapter Vault & Version Diffs", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/chapters",
        "db": "tbl_Submissions", "color": "#10B981", "compliance": "Document Immutability & Git-Style Differential Tracking", "archetype": "annotator",
        "subtitle": "Chapter 1 to 5 Digital Repository with Cryptographic Hash History"
    })
    screens.append({
        "id": "SP-ST-05", "title": "Split-Screen Thesis Annotator", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/feedback",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Double-Blind Digital Thesis Annotation Standard", "archetype": "annotator",
        "subtitle": "Interactive PDF Reader with Real-Time Supervisor Comments & Revision Threads"
    })
    screens.append({
        "id": "SP-ST-06", "title": "Plagiarism Similarity Audit", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/plagiarism",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "NUC 15% Maximum Similarity Threshold Mandate", "archetype": "turnitin",
        "subtitle": "Turnitin Integration Engine, Matched Source Repositories & Excerpt Highlighter"
    })
    screens.append({
        "id": "SP-ST-07", "title": "Defense Timetable & Panel", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/defense",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "Senate Postgraduate Examination Regulations", "archetype": "defense_rubric",
        "subtitle": "Final Oral Viva Timetable, Examination Panel & Slide Presentation Uploader"
    })
    screens.append({
        "id": "SP-ST-08", "title": "Final Archival & Clearance", "portal": "SPSEMS", "role": "Postgraduate Scholar", "route": "/spsems/student/clearance",
        "db": "tbl_Projects", "color": "#10B981", "compliance": "University Senate Final Degree Award Policy", "archetype": "dashboard",
        "subtitle": "Final Hardbound Copy Deposition, Library Clearance & Graduation Pass-List",
        "metrics": [("Defense Result", "PASSED (DISTINCTION)", "Grade A (93.0)"), ("Library Deposition", "VERIFIED (ARCHIVE)", "e-Library ID #8841"), ("Senate Approval", "RECOMMENDED", "Order Paper Ready")],
        "table_title": "Institutional Graduation Clearance Stations",
        "table_headers": ["Clearance Unit", "Required Verification", "Certifying Officer", "Status", "Actions"],
        "table_rows": [
            ["Departmental Clearance", "All revisions completed and certified", "Dr. A. M. Jimoh (HOD)", "PASSED & SIGNED", "View Endorsement →"],
            ["Postgraduate School", "Turnitin <=15% and defense rubric verified", "Dean PG School", "PASSED & SIGNED", "View Endorsement →"],
            ["University Library", "Final bound dissertation deposited", "University Librarian", "PASSED & SIGNED", "View Receipt →"],
            ["University Bursary", "All postgraduate tuition and defense fees cleared", "University Bursar", "PASSED & SIGNED", "View Receipt →"]
        ]
    })
    screens.append({
        "id": "SP-SV-01", "title": "Supervisor Authentication", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/:slug/login/supervisor",
        "db": "tbl_Supervisors", "color": "#10B981", "compliance": "Staff Multi-Factor Authentication Protocol", "archetype": "auth",
        "subtitle": "Senior Academic Supervisor & Professorial Workstation Sign-In",
        "auth_headline": "Academic Supervisor Portal",
        "auth_description": "Review candidate chapter submissions, annotate drafts, and issue cryptographic milestone sign-offs.",
        "form_title": "Sign in as Academic Supervisor",
        "form_subtitle": "Enter your University Staff ID & Faculty Token",
        "form_inputs": [
            ("University Staff ID Number", "STAFF/KWASU/CS/042"),
            ("Faculty Security Token / PIN", "••••••••••••••••"),
            ("Selected Academic Session", "2024/2025 Harmattan Semester")
        ],
        "btn_label": "Enter Supervisory Workstation →"
    })
    screens.append({
        "id": "SP-SV-02", "title": "Supervision Caseload Radar", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/dashboard",
        "db": "tbl_Supervisors", "color": "#10B981", "compliance": "Senate Workload Ratio (Max 5 Supervisees)", "archetype": "dashboard",
        "subtitle": "Active Candidates Overview, Pending Chapter Reviews & Quota Health",
        "metrics": [("Active Supervisees", "4 Active Scholars", "Senate Quota: 5 Max"), ("Pending Chapter Drafts", "2 Drafts Awaiting Review", "Average Turnaround 3d"), ("Milestones Signed", "12 Approved", "Cryptographic Sign-Off")],
        "table_title": "Assigned Postgraduate Supervisees Caseload",
        "table_headers": ["Candidate Name", "Degree Program", "Current Milestone", "Submission Date", "Actions"],
        "table_rows": [
            ["Adeyemi Bashir (20/52CS/0084)", "MSc Computer Science", "Chapter 4: Results & Discussion", "14-OCT-2024", "Review Draft →"],
            ["Fatima Garba (21/52CS/0012)", "PhD Cyber Security", "Chapter 3: Methodology", "10-OCT-2024", "Review Draft →"],
            ["Chukwuma Obi (20/52CS/0091)", "MSc Data Science", "Chapter 2: Lit Review", "05-OCT-2024", "Review Draft →"],
            ["Zainab Aliyu (21/52CS/0034)", "MSc Artificial Intelligence", "Concept Proposal", "01-OCT-2024", "Approved →"]
        ]
    })
    screens.append({
        "id": "SP-SV-03", "title": "Document Annotation Studio", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/review/:id",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Digital Thesis Annotation & Revision Mandate", "archetype": "annotator",
        "subtitle": "In-Depth PDF Markup, Inline Sticky Notes & Correction Guidance Studio"
    })
    screens.append({
        "id": "SP-SV-04", "title": "Milestone Sign-Off Studio", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/milestones",
        "db": "tbl_Milestones", "color": "#10B981", "compliance": "Cryptographic Non-Repudiation Electronic Sign-Off", "archetype": "dashboard",
        "subtitle": "Digital Approval Keys & Progression Authorization for Senate Pass-List",
        "metrics": [("Awaiting Sign-Off", "1 Candidate Ready", "Chapter 4 Certified"), ("Signed This Semester", "8 Milestones", "100% On Time"), ("Average Turnaround", "3.2 Days", "Benchmark < 5d")],
        "table_title": "Milestones Ready for Formal Supervisory Endorsement",
        "table_headers": ["Candidate", "Milestone Stage", "Turnitin Index", "Supervisor Verdict", "Actions"],
        "table_rows": [
            ["Adeyemi Bashir (20/52CS/0084)", "Stage 4: Results & Discussion", "11.4% (Passed)", "REVISIONS CERTIFIED", "Affix Digital Key →"],
            ["Fatima Garba (21/52CS/0012)", "Stage 3: Formal Methodology", "8.9% (Passed)", "APPROVED FOR DEFENSE", "Affix Digital Key →"]
        ]
    })
    screens.append({
        "id": "SP-SV-05", "title": "Pre-Defense Evaluation Rubric", "portal": "SPSEMS", "role": "Academic Supervisor", "route": "/spsems/supervisor/defense-grading",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "Postgraduate Examination Board Standard 100-Point Rubric", "archetype": "defense_rubric",
        "subtitle": "Methodology Rigor, Originality, Literature Mastery & Viva Readiness Grading"
    })
    screens.append({
        "id": "SP-AD-01", "title": "PG School Command Center", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/dashboard",
        "db": "tbl_Institutions", "color": "#10B981", "compliance": "Institutional Research Governance & Quality Assurance", "archetype": "dashboard",
        "subtitle": "University-Wide Dissertation Velocity, Defense Radar & Faculty Analytics",
        "metrics": [("Total Dissertations", "184 Active", "Across 8 Faculties"), ("Average Turnitin", "11.8% Clean", "Threshold <= 15%"), ("Scheduled Defenses", "28 Defenses", "This Quarter")],
        "table_title": "Faculty Postgraduate Research Overview",
        "table_headers": ["Faculty", "Active Dissertations", "Supervisors Engaged", "Mean Turnitin %", "Actions"],
        "table_rows": [
            ["Information & Comm. Technology", "42 Dissertations", "14 Supervisors", "10.4%", "View Faculty →"],
            ["Engineering & Technology", "54 Dissertations", "18 Supervisors", "11.2%", "View Faculty →"],
            ["Pure & Applied Sciences", "48 Dissertations", "16 Supervisors", "12.1%", "View Faculty →"],
            ["Management & Social Sciences", "40 Dissertations", "12 Supervisors", "13.4%", "View Faculty →"]
        ]
    })
    screens.append({
        "id": "SP-AD-02", "title": "AI Supervisor Allocation Engine", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/allocation",
        "db": "tbl_AllocationHistory", "color": "#10B981", "compliance": "Algorithmic Fairness & Workload Distribution Directive", "archetype": "ai_allocation",
        "subtitle": "Cosine Similarity Vector Matching & Supervisee Quota Optimization Engine"
    })
    screens.append({
        "id": "SP-AD-03", "title": "Defense Board & Panel Builder", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/defense-panels",
        "db": "tbl_Evaluations", "color": "#10B981", "compliance": "External Examiner Accreditation Criteria", "archetype": "defense_rubric",
        "subtitle": "External & Internal Examiner Assignment, Zoom Integration & Timetabling"
    })
    screens.append({
        "id": "SP-AD-04", "title": "Academic Policy Configuration", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/settings",
        "db": "tbl_InstitutionSettings", "color": "#10B981", "compliance": "Senate Regulations Update Authority", "archetype": "dashboard",
        "subtitle": "Turnitin Cutoff (15%), Supervisor Load (5:1) & Resubmission Penalties",
        "metrics": [("Plagiarism Limit", "15% Max Overlap", "Enforced Strict"), ("Supervisor Ratio", "5 Supervisees Max", "Enforced Strict"), ("Turnaround SLA", "5 Business Days", "Automated Alerts")],
        "table_title": "Senate Policy Parameters Registry",
        "table_headers": ["Policy Directive", "Configured Baseline", "Enforcement Rule", "Audit Status", "Actions"],
        "table_rows": [
            ["Turnitin Maximum Similarity Limit", "15% Maximum", "Block defense booking if > 15%", "VERIFIED SENATE 2024", "Modify Value →"],
            ["Faculty Supervisor Quota", "5 Candidates Max", "AI engine skips staff with 5 loads", "VERIFIED SENATE 2024", "Modify Value →"],
            ["External Examiner Honorarium", "Approved Scale", "Bursary Remita automated disbursement", "VERIFIED SENATE 2024", "Modify Value →"]
        ]
    })
    screens.append({
        "id": "SP-AD-05", "title": "SPSEMS System Audit Trail", "portal": "SPSEMS", "role": "Dean PG School", "route": "/spsems/admin/audit",
        "db": "tbl_AuditLog", "color": "#10B981", "compliance": "Tamper-Evident SHA-256 Ledger Requirement", "archetype": "dashboard",
        "subtitle": "Cryptographic Event Log of Submissions, Reviews, Scores & Endorsements",
        "metrics": [("Total Audited Events", "148,200 Events", "Zero Gaps"), ("Cryptographic Integrity", "SHA-256 Verified", "100% Immutable"), ("Failed Auth Attempts", "0 Security Breaches", "Firewall Active")],
        "table_title": "Real-Time Telemetry & Event Audit Ledger",
        "table_headers": ["Timestamp", "Officer / User", "Event Description", "Cryptographic Hash", "Actions"],
        "table_rows": [
            ["14-OCT-2024 14:35:12", "Prof. I. A. Bello", "Approved Chapter 4 Milestone for Adeyemi Bashir", "sha256:7f8a9b2...", "Verify Signature →"],
            ["14-OCT-2024 11:20:05", "Turnitin Engine", "Generated 11.4% Similarity Report for Draft v4.1", "sha256:3c4d5e6...", "Inspect Hash →"],
            ["12-OCT-2024 09:15:44", "Dean PG School", "Ratified External Examiner for Oral Defense Panel", "sha256:1a2b3c4...", "Inspect Hash →"]
        ]
    })

    # Category 4: SIWES (29 - 46)
    screens.append({
        "id": "SW-ST-01", "title": "SIWES Trainee Login", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/:slug/login/student",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "ITF National Training Scheme Framework", "archetype": "auth",
        "subtitle": "Industrial Attachment Electronic Logbook Sign-In",
        "auth_headline": "SIWES Trainee Portal",
        "auth_description": "Record daily engineering tasks, log machinery handled, upload CAD sketches, and obtain corporate stamps.",
        "form_title": "Trainee Workstation Sign-In",
        "form_subtitle": "Authenticate with your Undergraduate Matriculation Number",
        "form_inputs": [
            ("Undergraduate Matriculation Number", "21/25EE/0114"),
            ("Industrial Training Access PIN", "••••••••••••••••"),
            ("Host Employer Placement", "TotalEnergies E&P Nigeria")
        ],
        "btn_label": "Enter SIWES Logbook →"
    })
    screens.append({
        "id": "SW-ST-02", "title": "SIWES Attachment Hub", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/student/dashboard",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "ITF 24-Week Industrial Training Regulation", "archetype": "dashboard",
        "subtitle": "Weeks Elapsed Meter, Weekly Submission Rate & Industry Sign-Off Status",
        "metrics": [("Attachment Progress", "Week 14 of 24", "58% Completed"), ("Verified Logbooks", "13 Weeks Signed", "Industry Stamped"), ("Host Employer", "TotalEnergies E&P", "Port Harcourt Substation")],
        "table_title": "Weekly Logbook Submission & Verification Status",
        "table_headers": ["Week Ref", "Core Training Focus", "Logged Hours", "Industry Supervisor", "Actions"],
        "table_rows": [
            ["Week 14 (Current)", "Substation Transformer Overhaul & Dielectric Tests", "35.0 Hours", "UNDER REVIEW", "Open Logbook →"],
            ["Week 13 (Passed)", "High-Voltage Switchgear Testing & Relay Calibration", "40.0 Hours", "STAMPED & VERIFIED", "View Stamp →"],
            ["Week 12 (Passed)", "Underground Cable Fault Location & Thumping", "38.5 Hours", "STAMPED & VERIFIED", "View Stamp →"],
            ["Week 11 (Passed)", "SCADA Remote Terminal Unit (RTU) Configuration", "40.0 Hours", "STAMPED & VERIFIED", "View Stamp →"]
        ]
    })
    screens.append({
        "id": "SW-ST-03", "title": "Employer Placement Registry", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/student/placement",
        "db": "tbl_SIWESPlacements", "color": "#F59E0B", "compliance": "ITF Form 8 Employer Acceptance Mandate", "archetype": "dashboard",
        "subtitle": "Acceptance Letter PDF Upload, GPS Geotagging & Industry Mentor Assignment",
        "metrics": [("Placement Status", "APPROVED & ACTIVE", "Grade A Corporate Host"), ("Verified GPS Fix", "4.8156° N, 7.0498° E", "Port Harcourt Site"), ("ITF Subvention", "ELIGIBLE", "Form 8 Endorsed")],
        "table_title": "Corporate Placement Documentation Registry",
        "table_headers": ["Document Name", "Issuing Authority", "Submission Date", "Verification State", "Actions"],
        "table_rows": [
            ["Official Acceptance Letter", "TotalEnergies Human Resources", "15-MAY-2024", "VERIFIED VALID", "View Document →"],
            ["Workplace Induction Certificate", "TotalEnergies Safety Directorate", "20-MAY-2024", "VERIFIED VALID", "View Document →"]
        ]
    })
    screens.append({
        "id": "SW-ST-04", "title": "Weekly E-Logbook Entry", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/student/logbook",
        "db": "tbl_SIWESLogbook", "color": "#F59E0B", "compliance": "Daily Logbook Verification Requirement §3.2", "archetype": "siwes_logbook",
        "subtitle": "Daily Mon–Fri Activities, Equipment Logged, CAD Sketch Upload & Digital Stamp"
    })
    screens.append({
        "id": "SW-ST-05", "title": "Monthly Technical Synthesis", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/student/monthly-report",
        "db": "tbl_SIWESMonthlyReports", "color": "#F59E0B", "compliance": "ITF Monthly Synthesis Directive", "archetype": "annotator",
        "subtitle": "In-Depth Synthesis of Industrial Competencies & Engineering Problem Solving"
    })
    screens.append({
        "id": "SW-ST-06", "title": "Final SIWES Technical Defense", "portal": "SIWES", "role": "Industrial Trainee", "route": "/siwes/student/final-report",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "Departmental SIWES Defense Board Assessment", "archetype": "defense_rubric",
        "subtitle": "Comprehensive Bound Report Submission, Presentation Slides & Viva Defense"
    })
    screens.append({
        "id": "SW-IS-01", "title": "Industry Supervisor Gateway", "portal": "SIWES", "role": "External Industry Mentor", "route": "/siwes/industry/login",
        "db": "tbl_SIWESSupervisors", "color": "#F59E0B", "compliance": "Corporate Digital Signature Security Standard", "archetype": "auth",
        "subtitle": "Corporate Industry Supervisor Workstation Access",
        "auth_headline": "Corporate Industry Supervisor Portal",
        "auth_description": "Validate trainee attendance, review daily technical logs, and stamp weekly ITF reports.",
        "form_title": "Sign in as Industry Supervisor",
        "form_subtitle": "Authenticate using your Corporate Email & Access PIN",
        "form_inputs": [
            ("Corporate Work Email Address", "babatunde.williams@totalenergies.com"),
            ("Secure Supervisor Access PIN", "••••••••••••••••"),
            ("Host Organization", "TotalEnergies E&P Nigeria")
        ],
        "btn_label": "Enter Corporate Review Station →"
    })
    screens.append({
        "id": "SW-IS-02", "title": "Supervised Trainees Roster", "portal": "SIWES", "role": "External Industry Mentor", "route": "/siwes/industry/dashboard",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "Workplace Supervision Standard Ratio", "archetype": "dashboard",
        "subtitle": "Active University Trainees, Attendance Records & Pending Logbook Stamps",
        "metrics": [("Assigned Trainees", "3 Under Mentorship", "KWASU Electrical Eng"), ("Pending Logbooks", "1 Week Awaiting Stamp", "Due This Friday"), ("Average Attendance", "98.2% Punctuality", "Exemplary Record")],
        "table_title": "Active Supervised University Trainees",
        "table_headers": ["Trainee Name", "University & Dept", "Current Week", "Attendance Rate", "Actions"],
        "table_rows": [
            ["Chinedu Eze (21/25EE/0114)", "KWASU Electrical Engineering", "Week 14 (Mon-Fri)", "100% Present", "Review Logbook →"],
            ["Blessing Adams (21/25ME/0088)", "KWASU Mechanical Engineering", "Week 14 (Mon-Fri)", "96.5% Present", "Review Logbook →"],
            ["Usman Bello (21/25CE/0042)", "KWASU Civil Engineering", "Week 13 (Mon-Fri)", "98.0% Present", "Review Logbook →"]
        ]
    })
    screens.append({
        "id": "SW-IS-03", "title": "Weekly Logbook Digital Stamp", "portal": "SIWES", "role": "External Industry Mentor", "route": "/siwes/industry/verify-logbook",
        "db": "tbl_SIWESLogbook", "color": "#F59E0B", "compliance": "ITF Non-Repudiation Corporate Endorsement Standard", "archetype": "siwes_logbook",
        "subtitle": "Digital Approval Stamp, Weekly Competency Rating & Workplace Safety Scoring"
    })
    screens.append({
        "id": "SW-IS-04", "title": "ITF Form 8 Evaluation Form", "portal": "SIWES", "role": "External Industry Mentor", "route": "/siwes/industry/assessment",
        "db": "tbl_SIWESEvaluations", "color": "#F59E0B", "compliance": "Federal Republic of Nigeria ITF Form 8 Mandatory Scoring", "archetype": "defense_rubric",
        "subtitle": "Official End-of-Attachment Corporate Performance & Competence Appraisal"
    })
    screens.append({
        "id": "SW-IS-05", "title": "Completion Letter Generator", "portal": "SIWES", "role": "External Industry Mentor", "route": "/siwes/industry/completion-letter",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "Corporate Human Resources Certification Standard", "archetype": "dashboard",
        "subtitle": "Automated Generation of Formal Company Letter of Industrial Training Completion",
        "metrics": [("Trainee Completed", "Chinedu Eze", "24 Weeks Full"), ("Hours Completed", "960 Total Hours", "Exceeds 800h Min"), ("Recommendation", "EMPLOYMENT READY", "Grade A Trainee")],
        "table_title": "Certified Industrial Skills & Competency Matrix",
        "table_headers": ["Competency Domain", "Specific Skill Acquired", "Proficiency Level", "Corporate Endorsement", "Actions"],
        "table_rows": [
            ["High Voltage Engineering", "33kV Substation Maintenance & Safety", "Advanced (Level 4)", "CERTIFIED", "View Details →"],
            ["Protection & Control", "Overcurrent & Earth Fault Relay Injection", "Proficient (Level 3)", "CERTIFIED", "View Details →"],
            ["Industrial SCADA", "Modbus Protocol Wiring & Telemetry Testing", "Proficient (Level 3)", "CERTIFIED", "View Details →"]
        ]
    })
    screens.append({
        "id": "SW-CO-01", "title": "SIWES Directorate Center", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/dashboard",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "University Industrial Training Directorate Policy", "archetype": "dashboard",
        "subtitle": "Campus-Wide Industrial Placement Radar, Employer Registry & Subvention Pools",
        "metrics": [("Deployed Trainees", "412 Active", "Across 14 States"), ("Accredited Companies", "86 Corporate Hosts", "Grade A Listed"), ("ITF Subvention Pool", "₦98.8M Allocated", "Federal Scheme")],
        "table_title": "Departmental Industrial Deployment Overview",
        "table_headers": ["Department", "Trainees Deployed", "Placement Verification", "Site Visits Completed", "Actions"],
        "table_rows": [
            ["Electrical Engineering", "84 Trainees", "100% Placed", "78 / 84 Visited", "Inspect Dept →"],
            ["Mechanical Engineering", "92 Trainees", "100% Placed", "85 / 92 Visited", "Inspect Dept →"],
            ["Civil Engineering", "76 Trainees", "100% Placed", "70 / 76 Visited", "Inspect Dept →"],
            ["Computer Science", "160 Trainees", "100% Placed", "150 / 160 Visited", "Inspect Dept →"]
        ]
    })
    screens.append({
        "id": "SW-CO-02", "title": "Company Accreditation Directory", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/companies",
        "db": "tbl_SIWESCompanies", "color": "#F59E0B", "compliance": "ITF Corporate Partner Vetting Guidelines", "archetype": "dashboard",
        "subtitle": "Accredited Industrial Training Hosts, Health & Safety Audits & Blacklist Control",
        "metrics": [("Accredited Firms", "86 Active Hosts", "Full Compliance"), ("Pending Reviews", "4 New Companies", "Vetting In Progress"), ("Safety Violations", "0 Blacklisted", "Zero Incidents")],
        "table_title": "Accredited Corporate Industrial Host Registry",
        "table_headers": ["Company Name", "Industry Sector", "Capacity Limit", "Accreditation Tier", "Actions"],
        "table_rows": [
            ["TotalEnergies E&P Nigeria", "Energy & Oil / Gas", "25 Trainees Max", "GRADE A PREMIER", "View Agreement →"],
            ["Dangote Refinery & Petrochemicals", "Manufacturing & Energy", "40 Trainees Max", "GRADE A PREMIER", "View Agreement →"],
            ["Julius Berger Nigeria Plc", "Civil & Construction", "30 Trainees Max", "GRADE A PREMIER", "View Agreement →"],
            ["Interswitch Group, Lagos", "Fintech & Software Engineering", "35 Trainees Max", "GRADE A PREMIER", "View Agreement →"]
        ]
    })
    screens.append({
        "id": "SW-CO-03", "title": "Lecturer Site Visit Planner", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/supervision-trips",
        "db": "tbl_SIWESSiteVisits", "color": "#F59E0B", "compliance": "NUC Institutional Supervisory Visit Mandate", "archetype": "dashboard",
        "subtitle": "Zonal Itinerary Optimization, Lecturer Field Assignment & Expense Batching",
        "metrics": [("Supervision Zones", "6 Zonal Clusters", "Lagos, PH, Abuja, etc."), ("Assigned Lecturers", "28 Academic Staff", "On Field Duty"), ("Site Visit Coverage", "92.4% Completed", "Target 100%")],
        "table_title": "Institutional Field Supervisory Itineraries",
        "table_headers": ["Cluster Zone", "Corporate Hosts", "Trainees on Site", "Assigned Visiting Lecturer", "Actions"],
        "table_rows": [
            ["Zone A: Port Harcourt Layout", "TotalEnergies, Shell, NLNG", "42 Trainees", "Engr. Dr. K. A. Adeleke", "View Itinerary →"],
            ["Zone B: Lagos Island / Lekki", "Interswitch, Dangote, Chevron", "68 Trainees", "Prof. I. A. Bello", "View Itinerary →"],
            ["Zone C: Abuja FCT / Central", "Julius Berger, Galaxy Backbone", "38 Trainees", "Dr. H. O. Salami", "View Itinerary →"]
        ]
    })
    screens.append({
        "id": "SW-CO-04", "title": "On-Site Inspection Scoring", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/site-visit",
        "db": "tbl_SIWESEvaluations", "color": "#F59E0B", "compliance": "Visiting Academic Lecturer Evaluation Standard", "archetype": "defense_rubric",
        "subtitle": "Lecturer Physical Inspection Grading, Logbook Review & Mentor Interview"
    })
    screens.append({
        "id": "SW-CO-05", "title": "SIWES Viva Examination Board", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/viva-grading",
        "db": "tbl_SIWESEvaluations", "color": "#F59E0B", "compliance": "Departmental Academic Board Viva Regulations", "archetype": "defense_rubric",
        "subtitle": "Final Institutional Gradebook: Logbook (30%) + Visit (20%) + Viva Defense (50%)"
    })
    screens.append({
        "id": "SW-CO-06", "title": "ITF Master Disbursement Report", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/itf-report",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "Federal Republic of Nigeria ITF Form 8 Subvention Audit", "archetype": "dashboard",
        "subtitle": "Audited Schedules for Student Allowance & Supervisory Mileage Claims",
        "metrics": [("Trainees Certified", "412 Trainees", "100% Verified"), ("Total Student Allowance", "₦61.8M Expected", "₦15,000 / Month"), ("Lecturer Travel Claims", "₦14.2M Reconciled", "Remita Disbursed")],
        "table_title": "ITF Master Subvention Federal Claim Batch",
        "table_headers": ["Trainee Ref", "Full Name", "Discipline", "Attachment Duration", "Subvention Entitlement", "Actions"],
        "table_rows": [
            ["KWASU-SW-001", "Chinedu Eze", "Electrical Engineering", "24 Weeks (Full)", "₦90,000.00", "Include in Batch →"],
            ["KWASU-SW-002", "Blessing Adams", "Mechanical Engineering", "24 Weeks (Full)", "₦90,000.00", "Include in Batch →"],
            ["KWASU-SW-003", "Usman Bello", "Civil Engineering", "24 Weeks (Full)", "₦90,000.00", "Include in Batch →"],
            ["KWASU-SW-004", "Folake Adeleke", "Computer Science", "24 Weeks (Full)", "₦90,000.00", "Include in Batch →"]
        ]
    })
    screens.append({
        "id": "SW-CO-07", "title": "Digital SIWES Certificate", "portal": "SIWES", "role": "University Coordinator", "route": "/siwes/coordinator/clearance",
        "db": "tbl_SIWESTrainees", "color": "#F59E0B", "compliance": "Tamper-Proof National SIWES Certification Standard", "archetype": "dashboard",
        "subtitle": "Official Institutional Clearance Certificate with Dynamic Verification QR Code",
        "metrics": [("Certificate Status", "ISSUED & SIGNED", "Tamper-Evident"), ("Verification QR", "sha256:9a8b7c6...", "Publicly Scannable"), ("Grade Awarded", "GRADE A (DISTINCTION)", "Score: 91.5 / 100")],
        "table_title": "Official SIWES Clearance Endorsement Chain",
        "table_headers": ["Authority", "Officer Name", "Endorsement Date", "Status", "Actions"],
        "table_rows": [
            ["Host Corporate Mentor", "Engr. Babatunde Williams, FNSE", "18-OCT-2024", "CERTIFIED EXCELLENT", "View Endorsement →"],
            ["Visiting University Lecturer", "Engr. Dr. K. A. Adeleke", "20-OCT-2024", "CERTIFIED EXCELLENT", "View Endorsement →"],
            ["Departmental HOD", "Prof. S. O. Balogun", "24-OCT-2024", "SENATE RATIFIED", "View Endorsement →"],
            ["Director of SIWES", "Director Academic Planning", "26-OCT-2024", "FINAL CLEARANCE ISSUED", "Print Certificate →"]
        ]
    })

    # Category 5: HOSTEL (47 - 65)
    screens.append({
        "id": "HS-ST-01", "title": "Student Hostel Login", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/:slug/login/student",
        "db": "tbl_HostelStudents", "color": "#0EA5E9", "compliance": "University Student Life Housing Authentication", "archetype": "auth",
        "subtitle": "Campus Accommodation Workstation & Bed Space Picker Access",
        "auth_headline": "Smart Campus Accommodation Portal",
        "auth_description": "Browse available residence halls, select room bunks via interactive 3D rack, and obtain digital gate passes.",
        "form_title": "Student Accommodation Login",
        "form_subtitle": "Sign in using your University Matriculation Number",
        "form_inputs": [
            ("University Matriculation Number", "20/52CS/0084"),
            ("Hostel Portal Security PIN", "••••••••••••••••"),
            ("Accommodation Session", "2024/2025 Academic Year")
        ],
        "btn_label": "Enter Accommodation Hub →"
    })
    screens.append({
        "id": "HS-ST-02", "title": "Accommodation Command Center", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/student/dashboard",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Institutional Residential Governance Policy", "archetype": "dashboard",
        "subtitle": "Assigned Hall, Room Number, Bed Slot Status, Roommates & Digital Pass",
        "metrics": [("Assigned Bed Space", "Room 104 • Bunk A Top", "Hall of Residence A"), ("Payment Status", "REMITA VERIFIED", "₦60,000 Reconciled"), ("Gate Pass Status", "ACTIVE & CLEAR", "QR Pass #8841")],
        "table_title": "Assigned Room Residents & Amenities Check",
        "table_headers": ["Bunk Slot", "Resident Scholar", "Program / Level", "Contact Phone", "Actions"],
        "table_rows": [
            ["Bunk A (Top) - YOUR BED", "Adeyemi Bashir (20/52CS/0084)", "MSc Computer Science", "+234 803 123 4567", "View My Pass →"],
            ["Bunk A (Bottom)", "Michael Danladi (21/15AC/0019)", "BSc Accounting (400L)", "+234 802 987 6543", "Roommate Profile →"],
            ["Bunk B (Top)", "Chukwuma Eze (22/25EE/0088)", "BEng Electrical (300L)", "+234 814 555 1212", "Roommate Profile →"],
            ["Bunk B (Bottom)", "Usman Bello (23/30CE/0042)", "BEng Civil (200L)", "+234 805 444 3322", "Roommate Profile →"]
        ]
    })
    screens.append({
        "id": "HS-ST-03", "title": "Hall & Room Category Explorer", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/student/browse",
        "db": "tbl_Hostels", "color": "#0EA5E9", "compliance": "Gender & Academic Level Housing Quotas", "archetype": "dashboard",
        "subtitle": "Hall Facilities, Photographs, Power/Water Backup, Wi-Fi & Pricing Tiers",
        "metrics": [("Total Residence Halls", "8 Campus Halls", "4 Male / 4 Female"), ("Total Available Beds", "1,240 Spaces", "Live Availability"), ("Power Availability", "24/7 Solar + Grid", "Uninterrupted")],
        "table_title": "Accredited University Residence Halls",
        "table_headers": ["Residence Hall", "Designated Gender", "Room Types", "Annual Fee", "Actions"],
        "table_rows": [
            ["Hall of Residence A (Executive)", "Male (Postgrad & Finalists)", "4-Person Bunk Suite", "₦60,000.00", "Select Hall →"],
            ["Alhaja Sanni Hall of Residence", "Female (Undergraduate)", "4-Person Bunk Suite", "₦55,000.00", "Select Hall →"],
            ["Prof. Ibrahim Gambari Suites", "Male & Female (Postgrad)", "Single Private Room", "₦120,000.00", "Select Hall →"],
            ["Silver Crest Executive Hall", "Female (Freshers & Finalists)", "2-Person Luxury Suite", "₦95,000.00", "Select Hall →"]
        ]
    })
    screens.append({
        "id": "HS-ST-04", "title": "Interactive Bed Space Matrix", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/student/bed-picker",
        "db": "tbl_HostelBeds", "color": "#0EA5E9", "compliance": "Real-Time Anti-Squatting Bed Space Lock Framework", "archetype": "hostel_matrix",
        "subtitle": "Live 3D Room Grid, Available Bunks, Instant Lock & Remita RRR Checkout"
    })
    screens.append({
        "id": "HS-ST-05", "title": "Fee Payment & Gate Pass Slip", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/student/payment",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Treasury Single Account (TSA) Remita Direct Integration", "archetype": "dashboard",
        "subtitle": "Official Bursary Receipt & Security Checkpoint QR Gate Pass Slip",
        "metrics": [("Remita RRR Code", "2408-9912-4410", "TSA Verified"), ("Amount Paid", "₦60,000.00", "Full Settlement"), ("Gate Clearance", "QR PASS GENERATED", "Valid for Harmattan")],
        "table_title": "Official Bursary Fee Settlement Record",
        "table_headers": ["Item Description", "Official Account Code", "Paid Amount", "Remita Batch Ref", "Actions"],
        "table_rows": [
            ["Hall of Residence A Accommodation", "BUR-ACC-2024-HRA", "₦45,000.00", "REM-BATCH-88412", "View Invoice →"],
            ["Caution & Property Damage Deposit", "BUR-DEP-2024-CAUT", "₦10,000.00", "REM-BATCH-88412", "View Invoice →"],
            ["Hall Executive & Welfare Dues", "BUR-DUES-2024-WEL", "₦5,000.00", "REM-BATCH-88412", "View Invoice →"]
        ]
    })
    screens.append({
        "id": "HS-ST-06", "title": "Room Maintenance Desk", "portal": "HOSTEL", "role": "Resident Student", "route": "/hostel/student/maintenance",
        "db": "tbl_HostelMaintenance", "color": "#0EA5E9", "compliance": "Student Affairs Facility Service Level Agreement (SLA < 24h)", "archetype": "dashboard",
        "subtitle": "Report Plumbing, Electrical & Carpentry Issues with Photo Evidence",
        "metrics": [("Active Tickets", "1 Ticket Logged", "Electrical Repair"), ("Resolved This Term", "2 Tickets Completed", "Plumbing & Fan"), ("SLA Turnaround", "14 Hours Mean", "Within Target")],
        "table_title": "Room Maintenance Incident Tracker",
        "table_headers": ["Ticket ID", "Issue Category", "Reported Description", "Dispatched Artisan", "Actions"],
        "table_rows": [
            ["TICK-2024-042", "Electrical / Lighting", "Reading lamp socket voltage fluctuation in Room 104", "Works Dept (Electrician)", "Track Ticket →"],
            ["TICK-2024-018", "Plumbing / Sanitary", "Water heater valve gasket replacement completed", "Works Dept (Plumber)", "Resolved Closed →"]
        ]
    })
    screens.append({
        "id": "HS-WD-01", "title": "Hall Warden Gateway", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/:slug/login/warden",
        "db": "tbl_HostelWardens", "color": "#0EA5E9", "compliance": "Campus Security & Hall Porterage Governance", "archetype": "auth",
        "subtitle": "Hall Warden & Security Porter Workstation Access",
        "auth_headline": "Hall Warden & Porterage Portal",
        "auth_description": "Verify student gate passes, issue physical room keys, conduct property audits, and log curfew incidents.",
        "form_title": "Sign in as Hall Warden / Porter",
        "form_subtitle": "Enter your Warden Badge ID & Security Passcode",
        "form_inputs": [
            ("Hall Warden Badge ID", "WARDEN/KWASU/HRA/007"),
            ("Security Passcode", "••••••••••••••••"),
            ("Assigned Residence Hall", "Hall of Residence A (Male Executive)")
        ],
        "btn_label": "Enter Warden Console →"
    })
    screens.append({
        "id": "HS-WD-02", "title": "Warden Command Center", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/warden/dashboard",
        "db": "tbl_Hostels", "color": "#0EA5E9", "compliance": "Hall Occupancy Safety Code (Max 480 Beds)", "archetype": "dashboard",
        "subtitle": "Hall Occupancy Radar (412/480 Beds), Check-In Queues & Incident Alerts",
        "metrics": [("Hall Occupancy", "412 / 480 Beds", "85.8% Capacity"), ("Today Check-Ins", "18 Verified", "Keys Handed Over"), ("Active Repairs", "3 Plumbing / Elec", "Works Dispatched")],
        "table_title": "Daily Student Arrivals & Key Handover Queue",
        "table_headers": ["Student Name", "Matric Number", "Assigned Room & Bunk", "Bursary Remita Status", "Actions"],
        "table_rows": [
            ["Adeyemi Bashir", "20/52CS/0084", "Room 104 • Bunk A Top", "100% PAID (VERIFIED)", "Verify & Issue Key →"],
            ["Michael Danladi", "21/15AC/0019", "Room 104 • Bunk A Bottom", "100% PAID (VERIFIED)", "Checked In (Key Issued)"],
            ["Chukwuma Eze", "22/25EE/0088", "Room 104 • Bunk B Top", "100% PAID (VERIFIED)", "Checked In (Key Issued)"],
            ["Amina Garba", "23/10BIO/0034", "Room 208 • Bunk B Top", "AWAITING CLEARANCE", "Hold Key →"]
        ]
    })
    screens.append({
        "id": "HS-WD-03", "title": "Live Bed Space Inventory", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/warden/inventory",
        "db": "tbl_HostelBeds", "color": "#0EA5E9", "compliance": "Hostel Asset & Bed Inventory Mandate", "archetype": "hostel_matrix",
        "subtitle": "Block-by-Block Bed Grid: Occupied, Vacant, Maintenance & Squatter Citations"
    })
    screens.append({
        "id": "HS-WD-04", "title": "Key Handover & Check-In Desk", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/warden/check-in",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Physical Asset Custody Handshake Protocol", "archetype": "dashboard",
        "subtitle": "Barcode / QR Pass Scanner, Mattress Inspection Sign-Off & Key Handover",
        "metrics": [("Keys in Custody", "68 Keys in Rack", "Available Rooms"), ("Keys Issued", "412 Keys with Students", "Properly Logged"), ("Lost Key Reports", "0 Incidents", "Zero Re-keying Needed")],
        "table_title": "Student Check-In Handshake Ledger",
        "table_headers": ["Matric Ref", "Student Name", "Issued Key ID", "Handover Timestamp", "Actions"],
        "table_rows": [
            ["20/52CS/0084", "Adeyemi Bashir", "KEY-HRA-104-AT", "14-OCT-2024 10:14:02", "View Signed Slip →"],
            ["21/15AC/0019", "Michael Danladi", "KEY-HRA-104-AB", "14-OCT-2024 09:30:15", "View Signed Slip →"],
            ["22/25EE/0088", "Chukwuma Eze", "KEY-HRA-104-BT", "13-OCT-2024 16:45:10", "View Signed Slip →"]
        ]
    })
    screens.append({
        "id": "HS-WD-05", "title": "Room Condition Inspection", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/warden/inspection",
        "db": "tbl_HostelMaintenance", "color": "#0EA5E9", "compliance": "Caution Deposit Refund & Damage Assessment Directive", "archetype": "dashboard",
        "subtitle": "Pre-Check-In & Post-Check-Out Damage Audits for Caution Deposit Clearance",
        "metrics": [("Rooms Inspected", "120 Rooms Audited", "100% Certified"), ("Damage Citations", "2 Broken Louvres", "Deposit Deducted"), ("Cleanliness Score", "94.6% Grade A", "Sanitary Approved")],
        "table_title": "Room Asset Condition Audit Registry",
        "table_headers": ["Room Ref", "Wardrobe Condition", "Window / Mosquito Net", "Electrical Fittings", "Actions"],
        "table_rows": [
            ["Room 104 (Block 1)", "Intact (4 Units Clean)", "All Louvres Intact", "All Sockets Working", "Certify Room →"],
            ["Room 105 (Block 1)", "Intact (4 Units Clean)", "Minor Net Tear", "Ceiling Fan Repaired", "Certify Room →"],
            ["Room 106 (Block 1)", "Intact (4 Units Clean)", "All Louvres Intact", "All Sockets Working", "Certify Room →"]
        ]
    })
    screens.append({
        "id": "HS-WD-06", "title": "Curfew & Incident Log", "portal": "HOSTEL", "role": "Hall Warden", "route": "/hostel/warden/incidents",
        "db": "tbl_HostelIncidents", "color": "#0EA5E9", "compliance": "Senate Student Disciplinary Code Enforcement", "archetype": "dashboard",
        "subtitle": "Late Entry Logs, Squatting Citations, Boiling Ring Bans & Noise Warnings",
        "metrics": [("Curfew Incidents", "2 Late Entries", "Documented"), ("Squatting Citations", "0 Unauthorized Persons", "Full Zero Tolerance"), ("Boiling Ring Seizures", "1 Prohibited Appliance", "Confiscated Works")],
        "table_title": "Hall Disciplinary & Security Incident Registry",
        "table_headers": ["Incident Date", "Student Name / Matric", "Incident Category", "Warden Action", "Actions"],
        "table_rows": [
            ["14-OCT-2024 23:45", "T. Okon (22/10EC/0014)", "Late Entry Past 22:00 Curfew", "Official Caution Warning", "View Citation →"],
            ["12-OCT-2024 14:10", "Room 205 Occupants", "Prohibited Electrical Coil (Boiling Ring)", "Appliance Seized & Fined", "View Citation →"]
        ]
    })
    screens.append({
        "id": "HS-AD-01", "title": "Campus Housing Directorate", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/dashboard",
        "db": "tbl_Hostels", "color": "#0EA5E9", "compliance": "University Council Student Welfare Strategy", "archetype": "dashboard",
        "subtitle": "8,500 Total Beds Overview, Revenue Collected & Demographic Occupancy %",
        "metrics": [("Total Campus Beds", "8,500 Spaces", "8 Residence Halls"), ("Revenue Reconciled", "₦1.24B Collected", "Remita TSA Direct"), ("Occupancy Rate", "88.4% Overall", "Normal Capacity")],
        "table_title": "Campus Residence Halls Financial & Occupancy Summary",
        "table_headers": ["Residence Hall", "Capacity (Beds)", "Allocated (Beds)", "Revenue Generated", "Actions"],
        "table_rows": [
            ["Hall of Residence A (Male)", "1,200 Beds", "1,080 Allocated", "₦72,000,000.00", "Manage Hall →"],
            ["Alhaja Sanni Hall (Female)", "1,500 Beds", "1,420 Allocated", "₦78,100,000.00", "Manage Hall →"],
            ["Prof. Gambari Suites (PG)", "400 Suites", "320 Allocated", "₦38,400,000.00", "Manage Hall →"],
            ["Silver Crest Executive Hall", "1,000 Beds", "920 Allocated", "₦87,400,000.00", "Manage Hall →"]
        ]
    })
    screens.append({
        "id": "HS-AD-02", "title": "Automated Allocation Engine", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/allocation-engine",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Senate Quota Directive: Freshers (40%), Finalists (30%), Special Needs (10%)", "archetype": "hostel_matrix",
        "subtitle": "Demographic Quota Slicing, Merit Allotment & Automated Reservation Timer"
    })
    screens.append({
        "id": "HS-AD-03", "title": "Hall & Room Master Studio", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/halls",
        "db": "tbl_Hostels", "color": "#0EA5E9", "compliance": "University Physical Planning Infrastructure Registry", "archetype": "dashboard",
        "subtitle": "Add New Blocks, Define Room Capacities, Bed Pricing Tiers & Facilities",
        "metrics": [("Hostel Blocks", "24 Blocks Active", "Across Campus"), ("Bed Space Inventory", "8,500 Managed", "Zero Ghost Beds"), ("Maintenance Reserves", "₦124M Funded", "Bursary Reserve")],
        "table_title": "Master Residential Infrastructure Catalog",
        "table_headers": ["Block Ref", "Hall Associated", "Floor Levels", "Room Count", "Actions"],
        "table_rows": [
            ["Block 1 (Ground Floor)", "Hall of Residence A", "Ground Floor", "8 Quad Rooms (32 Beds)", "Edit Block →"],
            ["Block 2 (First Floor)", "Hall of Residence A", "First Floor", "8 Quad Rooms (32 Beds)", "Edit Block →"],
            ["Block 3 (Second Floor)", "Hall of Residence A", "Second Floor", "8 Quad Rooms (32 Beds)", "Edit Block →"]
        ]
    })
    screens.append({
        "id": "HS-AD-04", "title": "Hostel Revenue Reconciliation", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/finance",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Bursary Financial Regulations & TSA Reconciliation", "archetype": "dashboard",
        "subtitle": "Remita Batch Audits, Caution Deposit Escrow & Refund Approvals",
        "metrics": [("Total Accommodation", "₦1.02B Reconciled", "100% Cleared"), ("Caution Escrow Pool", "₦170M in Escrow", "Refund Ready"), ("Executive Hall Dues", "₦50M Disbursed", "Hall Wardens")],
        "table_title": "Daily Remita TSA Inflow Settlement Batches",
        "table_headers": ["Batch Date", "Settlement RRR Ref", "Transaction Count", "Total Batch Inflow", "Actions"],
        "table_rows": [
            ["14-OCT-2024", "RRR-BATCH-2024-1014", "142 Student Payments", "₦8,520,000.00", "Download Schedule →"],
            ["13-OCT-2024", "RRR-BATCH-2024-1013", "180 Student Payments", "₦10,800,000.00", "Download Schedule →"],
            ["12-OCT-2024", "RRR-BATCH-2024-1012", "110 Student Payments", "₦6,600,000.00", "Download Schedule →"]
        ]
    })
    screens.append({
        "id": "HS-AD-05", "title": "Facility Maintenance Dispatch", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/maintenance-dispatch",
        "db": "tbl_HostelMaintenance", "color": "#0EA5E9", "compliance": "Physical Works & Maintenance Service Standard", "archetype": "dashboard",
        "subtitle": "Contractor Work Orders, Water Borehole Repairs, Solar Generator Maintenance",
        "metrics": [("Active Work Orders", "4 Dispatched", "Civil & Electrical"), ("Budget Spent", "₦4.2M This Month", "Within Maintenance Cap"), ("Pumps & Generators", "100% Operational", "Backup Ready")],
        "table_title": "Capital Works & Ongoing Maintenance Contracts",
        "table_headers": ["Order Ref", "Facility Target", "Contractor Assigned", "Expenditure", "Actions"],
        "table_rows": [
            ["WO-2024-084", "Hall A Solar Inverter Bank Maintenance", "SunPower Engineering Ltd", "₦850,000.00", "Inspect Job →"],
            ["WO-2024-085", "Borehole Water Filtration Pump Overhaul", "Apex Hydraulic Services", "₦620,000.00", "Inspect Job →"]
        ]
    })
    screens.append({
        "id": "HS-AD-06", "title": "Medical Room Relocation Hub", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/reallocations",
        "db": "tbl_HostelAllocations", "color": "#0EA5E9", "compliance": "Special Needs & Health Services Priority Mandate", "archetype": "dashboard",
        "subtitle": "Ground-Floor Medical Swaps, Special Needs Allocations & Eviction Orders",
        "metrics": [("Special Needs Beds", "42 Ground Floor Spaces", "Reserved Priority"), ("Medical Swaps Granted", "8 Swaps Completed", "Health Services Cert."), ("Emergency Isolation", "4 Rooms Available", "Medical Buffer")],
        "table_title": "Medical & Special Needs Bed Relocation Ledger",
        "table_headers": ["Candidate", "Initial Bed", "Relocated Ground Bed", "Medical Reason", "Actions"],
        "table_rows": [
            ["Kemi Balogun (23/15AC/0091)", "Room 304 Bunk B Top", "Room 102 Bunk A Bottom", "Asthma & Reduced Mobility", "Authorize Swap →"],
            ["Tunde Adams (22/20CS/0014)", "Room 208 Bunk A Top", "Room 101 Bunk A Bottom", "Post-Surgery Convalescence", "Authorize Swap →"]
        ]
    })
    screens.append({
        "id": "HS-AD-07", "title": "Annual Renovation Planner", "portal": "HOSTEL", "role": "Director Student Housing", "route": "/hostel/admin/audit",
        "db": "tbl_Hostels", "color": "#0EA5E9", "compliance": "Summer Recess Facility Refresh Standards", "archetype": "dashboard",
        "subtitle": "Deep Sanitization, Wall Repainting, Mattress Replacement & Plumbing Overhaul",
        "metrics": [("Renovation Scope", "8 Residence Halls", "Summer Recess"), ("Mattress Refresh", "1,500 New Mattresses", "High-Density Foam"), ("Total Budget", "₦45M Approved", "Council Ratified")],
        "table_title": "Summer Recess Facility Renovation Schedule",
        "table_headers": ["Hall Target", "Primary Renovation Task", "Target Completion Date", "Budget Allocation", "Actions"],
        "table_rows": [
            ["Hall of Residence A", "Deep sanitization, wall repainting & plumbing", "15-DEC-2024", "₦12,000,000.00", "View Progress →"],
            ["Alhaja Sanni Hall", "Roof waterproofing & electrical rewiring", "20-DEC-2024", "₦14,500,000.00", "View Progress →"]
        ]
    })

    # Category 6: Continuous Background Engines & System Ops (66 - 70)
    screens.append({
        "id": "ENG-01", "title": "AI/ML Retraining Telemetry", "portal": "ENGINES", "role": "MLOps Engineer", "route": "/admin/ai-engine",
        "db": "tbl_MLPipelineRuns", "color": "#EC4899", "compliance": "Model Governance, Precision & Drift Prevention Framework", "archetype": "ai_allocation",
        "subtitle": "Continuous Feature Extraction, Cosine Similarity Weights & Accuracy Radar"
    })
    screens.append({
        "id": "ENG-02", "title": "MS 365 Access Two-Way Sync", "portal": "ENGINES", "role": "Database Administrator", "route": "/admin/ms-access-sync",
        "db": "tbl_AllTables", "color": "#EC4899", "compliance": "ADODB OleDB 16-Table Bidirectional Replication Standard", "archetype": "sync",
        "subtitle": "Real-Time SQLite ↔ MS Access Two-Way Synchronization Bridge"
    })
    screens.append({
        "id": "ENG-03", "title": "Multi-Tenant Domain Console", "portal": "ENGINES", "role": "SuperAdmin", "route": "/admin/tenants",
        "db": "tbl_Institutions", "color": "#EC4899", "compliance": "Wildcard DNS Routing & Subdomain Isolation", "archetype": "dashboard",
        "subtitle": "Subdomain Routing (*.campussphere.edu.ng), SSL Certificates & Ingress Health",
        "metrics": [("Active Ingress Domains", "42 University Subdomains", "All SSL Active"), ("Certificate Renewal", "Let's Encrypt Wildcard", "Auto-Renewed 90d"), ("DNS Lookup Time", "4.2 ms Mean", "Cloudflare DNS")],
        "table_title": "Multi-Tenant Subdomain Routing Registry",
        "table_headers": ["Subdomain Slug", "Target University", "SSL Certificate State", "Ingress Latency", "Actions"],
        "table_rows": [
            ["kwasu.campussphere.edu.ng", "Kwara State University, Malete", "TLS 1.3 ACTIVE", "4.1 ms", "Inspect DNS →"],
            ["unilorin.campussphere.edu.ng", "University of Ilorin", "TLS 1.3 ACTIVE", "3.9 ms", "Inspect DNS →"],
            ["ful.campussphere.edu.ng", "Federal University Lokoja", "TLS 1.3 ACTIVE", "4.5 ms", "Inspect DNS →"]
        ]
    })
    screens.append({
        "id": "ENG-04", "title": "Global Platform Health", "portal": "ENGINES", "role": "SuperAdmin", "route": "/admin/health",
        "db": "tbl_AuditLog", "color": "#EC4899", "compliance": "High Availability 99.9% SLA Operational Guarantee", "archetype": "dashboard",
        "subtitle": "API Latency, Active WebSocket Connections, SQLite Connection Pool & CPU/RAM",
        "metrics": [("System Uptime", "99.98% Past 90 Days", "Zero Downtime"), ("API Latency", "12 ms Global Mean", "Optimal Performance"), ("Active WebSockets", "1,840 Connected", "Real-Time Events")],
        "table_title": "Microservice Health & Container Telemetry",
        "table_headers": ["Subsystem Component", "Instance Type", "Memory Footprint", "CPU Utilization", "Health State"],
        "table_rows": [
            ["SPSEMS Dissertation Core", "FastAPI / Python 3.11", "240 MB", "2.4%", "HEALTHY OPTIMAL"],
            ["SIWES Electronic Logbook", "FastAPI / Python 3.11", "180 MB", "1.8%", "HEALTHY OPTIMAL"],
            ["HOSTEL 3D Matrix Allocator", "FastAPI / Python 3.11", "210 MB", "3.1%", "HEALTHY OPTIMAL"],
            ["MS Access ADODB Sync Daemon", "Python Windows COM Worker", "145 MB", "1.2%", "HEALTHY OPTIMAL"]
        ]
    })
    screens.append({
        "id": "ENG-05", "title": "Master Security & Audit Trail", "portal": "ENGINES", "role": "Chief Information Security Officer", "route": "/admin/security",
        "db": "tbl_AuditLog", "color": "#EC4899", "compliance": "ISO 27001 & NDPR National Data Protection Regulation", "archetype": "dashboard",
        "subtitle": "Role-Based Access Control (RBAC), Multi-Factor Enforcement & Vulnerability Shield",
        "metrics": [("Security Rating", "A+ Grade (ISO 27001)", "NDPR Certified"), ("MFA Enforcement", "100% Mandatory Staff", "FIDO2 / TOTP"), ("Intrusion Blocks", "42 Suspicious IPs Blocked", "Automated WAF")],
        "table_title": "Security Incident Telemetry & Audit Stream",
        "table_headers": ["Event Time", "Originating IP & Country", "User Identifier", "Security Action Taken", "Actions"],
        "table_rows": [
            ["14-OCT-2024 18:12:04", "197.210.44.12 (Nigeria)", "20/52CS/0084 (Adeyemi B.)", "MFA Verification Successful", "View Session →"],
            ["14-OCT-2024 16:40:15", "102.89.22.88 (Nigeria)", "Prof. I. A. Bello", "Digital Key Sign-Off Ratified", "View Session →"],
            ["14-OCT-2024 14:02:11", "45.134.22.10 (Unknown)", "root_admin (Attempted)", "Blocked by Ingress WAF", "Inspect Threat →"]
        ]
    })

    return screens

# ─────────────────────────────────────────────────────────────────────────────
# SVG COMPILER & DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

def build_master_svg():
    screens = get_complete_70_screens()
    print(f"Loaded {len(screens)} screens. Compiling master SVG canvas...")
    
    CANVAS_W = COLS * (FRAME_W + GAP_X) + GAP_X
    CANVAS_H = 10 * (FRAME_H + GAP_Y) + GAP_Y + 140
    
    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" fill="none">')
    svg_parts.append(f'  <!-- Canvas Background -->')
    svg_parts.append(f'  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#0A0D14"/>')
    
    # Master Title Header Block
    svg_parts.append(f'  <g id="Master Title Block" transform="translate(160, 80)">')
    svg_parts.append(f'    <rect width="{CANVAS_W - 320}" height="140" rx="16" fill="#111624" stroke="#253046" stroke-width="2"/>')
    svg_parts.append(f'    <text x="40" y="55" fill="#FFFFFF" font-family="Inter, -apple-system, sans-serif" font-size="36" font-weight="900">CampusSphere Higher Education Operating System</text>')
    svg_parts.append(f'    <text x="40" y="95" fill="#38BDF8" font-family="Inter, -apple-system, sans-serif" font-size="20" font-weight="700">Master Enterprise Prototype Dossier: All 70 Screens Bespoke Designed for University Senate &amp; Stakeholder Approval</text>')
    svg_parts.append(f'    <rect x="{CANVAS_W - 760}" y="42" width="400" height="54" rx="12" fill="#10B981" fill-opacity="0.15" stroke="#10B981" stroke-width="2"/>')
    svg_parts.append(f'    <text x="{CANVAS_W - 560}" y="76" fill="#10B981" font-family="Inter, -apple-system, sans-serif" font-size="18" font-weight="900" text-anchor="middle">STAKEHOLDER SIGN-OFF READY (70/70 BESPOKE)</text>')
    svg_parts.append(f'  </g>')
    
    # Dispatch all 70 screens
    for idx, s in enumerate(screens):
        col = idx % COLS
        row = idx // COLS
        x = GAP_X + col * (FRAME_W + GAP_X)
        y = 280 + row * (FRAME_H + GAP_Y)
        
        arch = s.get("archetype", "dashboard")
        if arch == "auth":
            fr_parts = render_auth_layout(s)
        elif arch == "annotator":
            fr_parts = render_annotator_layout(s)
        elif arch == "turnitin":
            fr_parts = render_turnitin_layout(s)
        elif arch == "hostel_matrix":
            fr_parts = render_hostel_matrix_layout(s)
        elif arch == "siwes_logbook":
            fr_parts = render_siwes_logbook_layout(s)
        elif arch == "ai_allocation":
            fr_parts = render_ai_allocation_layout(s)
        elif arch == "defense_rubric":
            fr_parts = render_defense_rubric_layout(s)
        elif arch == "clean_slate":
            fr_parts = render_clean_slate_layout(s)
        elif arch == "sync":
            fr_parts = render_sync_layout(s)
        else:
            fr_parts = render_dashboard_layout(s)
            
        svg_parts.append(f'  <!-- ================= FRAME {idx+1}: {s["id"]} ================= -->')
        svg_parts.append(f'  <g id="{s["id"]} - {s["title"]}" transform="translate({x}, {y})">')
        svg_parts.extend([f"    {p}" for p in fr_parts])
        svg_parts.append(f'  </g>')
        
    svg_parts.append('</svg>')
    
    full_svg = "\n".join(svg_parts)
    print(f"Generated complete bespoke SVG: {len(full_svg):,} bytes.")
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_svg)
        
    with open(ARTIFACT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_svg)
        
    print(f"Saved to: {OUTPUT_PATH}")
    print(f"Saved to artifact: {ARTIFACT_OUTPUT_PATH}")
    
    # Copy to clipboard via powershell
    try:
        ps_cmd = f'Set-Clipboard -Path "{OUTPUT_PATH}"'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        print("Successfully loaded file into Windows clipboard.")
    except Exception as e:
        print(f"Notice: Clipboard copy: {e}")

if __name__ == "__main__":
    build_master_svg()
