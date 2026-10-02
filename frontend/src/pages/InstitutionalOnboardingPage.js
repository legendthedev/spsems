import React, { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Building2, Palette, ShieldCheck, CheckCircle2, ArrowRight, ArrowLeft,
  Upload, Sparkles, School, Globe, Mail, Phone, Lock, User, Check,
  Copy, Layers, Sliders, GraduationCap
} from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';
import ThemeToggle from '../components/ThemeToggle';
import { resolveLogoUrl } from '../utils/logoHelper';

// ── SAMPLE PRESETS FOR QUICK ONE-CLICK TESTING ───────────────────────────────
const SAMPLE_PRESETS = [
  {
    name: 'University of Lagos',
    code: 'UNILAG',
    domain: 'unilag.edu.ng',
    type: 'Federal University',
    state: 'Lagos',
    city: 'Akoka',
    primary: '#b91c1c',
    secondary: '#1e3a8a',
    admin_name: 'Prof. Folasade Ogunsola',
    admin_uname: 'unilag_admin',
    email: 'vc@unilag.edu.ng',
    session: '2025/2026',
    semester: 'First Semester',
    logo_url: '/unilag.svg',
  },
  {
    name: 'University of Ibadan',
    code: 'UI',
    domain: 'ui.edu.ng',
    type: 'Federal University',
    state: 'Oyo',
    city: 'Ibadan',
    primary: '#4c1d95',
    secondary: '#b45309',
    admin_name: 'Prof. K. A. Adebayo',
    admin_uname: 'ui_admin',
    email: 'ict.admin@ui.edu.ng',
    session: '2025/2026',
    semester: 'First Semester',
    logo_url: '',
  },
  {
    name: 'Obafemi Awolowo University',
    code: 'OAU',
    domain: 'oauife.edu.ng',
    type: 'Federal University',
    state: 'Osun',
    city: 'Ile-Ife',
    primary: '#1e3a8a',
    secondary: '#d97706',
    admin_name: 'Dr. O. M. Babatunde',
    admin_uname: 'oau_admin',
    email: 'support@oauife.edu.ng',
    session: '2025/2026',
    semester: 'First Semester',
  },
  {
    name: 'Kwara State Polytechnic',
    code: 'KWAPOLY',
    domain: 'kwarastatepolytechnic.edu.ng',
    type: 'State Polytechnic',
    state: 'Kwara',
    city: 'Ilorin',
    primary: '#047857',
    secondary: '#1e293b',
    admin_name: 'Engr. S. A. Alabi',
    admin_uname: 'kwapoly_admin',
    email: 'info@kwarastatepolytechnic.edu.ng',
    session: '2025/2026',
    semester: 'First Semester',
  },
];

export default function InstitutionalOnboardingPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Wizard Step: 1: Identity, 2: Logo & Color, 3: Governance, 4: Admin, 5: Live Success
  const [currentStep, setCurrentStep] = useState(1);
  const [busy, setBusy] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  // Form State
  const [form, setForm] = useState({
    name: '',
    code: '',
    official_domain: '',
    institution_type: 'Federal University',
    country: 'Nigeria',
    state: 'Kwara',
    city: 'Ilorin',
    contact_email: '',
    contact_phone: '',
    logo_url: '',
    primary_color: '#16a34a',
    secondary_color: '#080808',
    accent_color: '#22c55e',
    admin_fullname: '',
    admin_username: '',
    admin_password: '',
    confirm_password: '',
    admin_designation: 'Director of ICT / Dean of Faculty',
    academic_session: '2025/2026',
    current_semester: 'First Semester',
    max_supervisor_load: 10,
    dual_supervisor_for_postgrad: true,
    auto_assign_co_supervisor: true,
    enable_ai_pairing: true,
    instant_live_activation: true,
  });

  // Logo & Extracted Colors
  const [logoPreview, setLogoPreview] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [extractedPalette, setExtractedPalette] = useState([
    '#16a34a', '#15803d', '#22c55e', '#0f172a', '#1e293b', '#eab308'
  ]);
  const [analyzingLogo, setAnalyzingLogo] = useState(false);
  const [onboardResult, setOnboardResult] = useState(null);

  const update = (field, val) => setForm(prev => ({ ...prev, [field]: val }));

  // Helper to load sample preset
  const loadPreset = (preset) => {
    setForm(prev => ({
      ...prev,
      name: preset.name,
      code: preset.code,
      official_domain: preset.domain,
      institution_type: preset.type,
      state: preset.state,
      city: preset.city,
      contact_email: preset.email,
      contact_phone: '+23480' + Math.floor(10000000 + Math.random() * 90000000),
      logo_url: preset.logo_url || '',
      primary_color: preset.primary,
      secondary_color: preset.secondary,
      admin_fullname: preset.admin_name,
      admin_username: preset.admin_uname,
      admin_password: 'password123',
      confirm_password: 'password123',
    }));
    setLogoPreview(preset.logo_url || null);
    setLogoFile(null);
    setExtractedPalette([
      preset.primary,
      preset.secondary,
      adjustBrightness(preset.primary, 30),
      adjustBrightness(preset.primary, -30),
      '#0f172a',
      '#ffffff'
    ]);
    toast.success(`Loaded profile for ${preset.name}!`);
  };

  // ── AUTOMATIC COLOR EXTRACTION FROM LOGO IMAGE (CANVAS) ────────────────────
  const processImageForColors = (imgSource) => {
    setAnalyzingLogo(true);
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const sampleSize = 100;
        canvas.width = sampleSize;
        canvas.height = sampleSize;
        ctx.drawImage(img, 0, 0, sampleSize, sampleSize);

        const imgData = ctx.getImageData(0, 0, sampleSize, sampleSize).data;
        const colorBins = {};

        for (let i = 0; i < imgData.length; i += 4) {
          const r = imgData[i];
          const g = imgData[i + 1];
          const b = imgData[i + 2];
          const a = imgData[i + 3];

          // Ignore transparent and semi-transparent
          if (a < 120) continue;

          // Ignore almost pure white / background canvas
          if (r > 240 && g > 240 && b > 240) continue;

          // Ignore pitch black borders
          if (r < 20 && g < 20 && b < 20) continue;

          // Calculate saturation and luminance
          const max = Math.max(r, g, b);
          const min = Math.min(r, g, b);
          const delta = max - min;
          const sat = max === 0 ? 0 : delta / max;
          const lum = (0.299 * r + 0.587 * g + 0.114 * b);

          // Discard neutral grays unless no other vibrant colors exist
          if (sat < 0.15 && (lum > 50 && lum < 200)) continue;

          // Quantize into 16-step bins
          const qr = Math.round(r / 16) * 16;
          const qg = Math.round(g / 16) * 16;
          const qb = Math.round(b / 16) * 16;
          const hex = rgbToHex(qr, qg, qb);

          if (!colorBins[hex]) {
            colorBins[hex] = { hex, count: 0, sat, lum, r: qr, g: qg, b: qb };
          }
          // Weight vibrant colors more heavily
          colorBins[hex].count += (sat > 0.35 ? 4 : 1);
        }

        const sortedColors = Object.values(colorBins).sort((a, b) => b.count - a.count);

        if (sortedColors.length > 0) {
          // Find dominant vibrant primary
          const vibrantList = sortedColors.filter(c => c.sat >= 0.25);
          const primaryChoice = (vibrantList.length > 0 ? vibrantList[0] : sortedColors[0]).hex;

          // Find distinct secondary color (different hue or lightness)
          let secondaryChoice = '#0f172a';
          for (let i = 1; i < sortedColors.length; i++) {
            const candidate = sortedColors[i];
            const dist = Math.abs(candidate.lum - (colorBins[primaryChoice]?.lum || 128));
            if (candidate.hex !== primaryChoice && dist > 35) {
              secondaryChoice = candidate.hex;
              break;
            }
          }

          // Build top 6 palette swatches
          const palette = [primaryChoice, secondaryChoice];
          sortedColors.forEach(c => {
            if (!palette.includes(c.hex) && palette.length < 6) {
              palette.push(c.hex);
            }
          });

          // Fallbacks if logo is monochromatic
          if (palette.length < 4) {
            palette.push(adjustBrightness(primaryChoice, 35));
            palette.push(adjustBrightness(primaryChoice, -35));
          }

          update('primary_color', primaryChoice);
          update('secondary_color', secondaryChoice);
          update('accent_color', palette[2] || adjustBrightness(primaryChoice, 40));
          setExtractedPalette(palette);

          // Generate an optimized thumbnail base64 Data URL for the submitted logo
          try {
            const thumbCanvas = document.createElement('canvas');
            const maxDim = 280;
            let w = img.width || maxDim;
            let h = img.height || maxDim;
            if (w > maxDim || h > maxDim) {
              if (w > h) {
                h = Math.round((h * maxDim) / w);
                w = maxDim;
              } else {
                w = Math.round((w * maxDim) / h);
                h = maxDim;
              }
            }
            thumbCanvas.width = Math.max(w, 40);
            thumbCanvas.height = Math.max(h, 40);
            const thumbCtx = thumbCanvas.getContext('2d');
            thumbCtx.drawImage(img, 0, 0, thumbCanvas.width, thumbCanvas.height);
            const dataUrl = thumbCanvas.toDataURL('image/png', 0.95);
            update('logo_url', dataUrl);
          } catch (canvasErr) {
            console.warn('Canvas thumbnail generation skipped:', canvasErr);
          }

          toast.success(
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Palette size={15} color={primaryChoice} /> Extracted official palette: <b>{primaryChoice}</b> (Primary) &amp; <b>{secondaryChoice}</b>
            </span>,
            { duration: 4000 }
          );
        }
      } catch (err) {
        console.error('Color extraction failed:', err);
      } finally {
        setAnalyzingLogo(false);
      }
    };
    img.src = imgSource;
  };

  const handleLogoFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file (PNG, JPG, SVG, WEBP).');
      return;
    }

    setLogoFile(file);
    const objectUrl = URL.createObjectURL(file);
    setLogoPreview(objectUrl);
    processImageForColors(objectUrl);

    // Read directly as Data URL for immediate fallback
    const reader = new FileReader();
    reader.onload = (ev) => {
      if (ev.target?.result) {
        update('logo_url', ev.target.result);
      }
    };
    reader.readAsDataURL(file);
  };

  // Helper RGB to Hex
  function rgbToHex(r, g, b) {
    const toHex = (n) => {
      const clamped = Math.max(0, Math.min(255, n));
      return clamped.toString(16).padStart(2, '0');
    };
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  // Helper brightness adjuster
  function adjustBrightness(hex, percent) {
    let num = parseInt(hex.replace('#', ''), 16);
    let amt = Math.round(2.55 * percent);
    let R = (num >> 16) + amt;
    let G = ((num >> 8) & 0x00FF) + amt;
    let B = (num & 0x0000FF) + amt;
    return (
      '#' +
      (
        0x1000000 +
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
        (B < 255 ? (B < 1 ? 0 : B) : 255)
      )
        .toString(16)
        .slice(1)
    );
  }

  // ── FINAL SUBMISSION: REGISTER & ONBOARD INSTITUTION ────────────────────────
  const handleFinalSubmit = async (e) => {
    e.preventDefault();

    if (!form.name || !form.code || !form.official_domain) {
      toast.error('Institution name, code, and official domain are required.');
      setCurrentStep(1);
      return;
    }

    if (!form.admin_username || !form.admin_password) {
      toast.error('Lead admin credentials must be configured.');
      setCurrentStep(4);
      return;
    }

    if (form.admin_password !== form.confirm_password) {
      toast.error('Admin passwords do not match.');
      setCurrentStep(4);
      return;
    }

    setBusy(true);
    let uploadedLogoUrl = form.logo_url;

    try {
      // 1. Upload logo file if selected
      if (logoFile) {
        const formData = new FormData();
        formData.append('file', logoFile);
        try {
          const upRes = await api.post('/institutions/upload-logo', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          if (upRes.data?.data_url) {
            uploadedLogoUrl = upRes.data.data_url;
          } else if (upRes.data?.logo_url) {
            uploadedLogoUrl = upRes.data.logo_url;
          }
        } catch (uploadErr) {
          console.warn('Logo upload fallback to client data URL:', uploadErr);
        }
      }

      // 2. Submit onboard payload
      const payload = {
        name: form.name.trim(),
        code: form.code.trim().toUpperCase(),
        official_domain: form.official_domain.trim().toLowerCase(),
        institution_type: form.institution_type,
        country: form.country,
        state: form.state,
        city: form.city,
        contact_email: form.contact_email.trim().toLowerCase(),
        contact_phone: form.contact_phone,
        logo_url: uploadedLogoUrl || form.logo_url || null,
        primary_color: form.primary_color,
        secondary_color: form.secondary_color,
        accent_color: form.accent_color,
        admin_fullname: form.admin_fullname.trim(),
        admin_username: form.admin_username.trim().toLowerCase(),
        admin_password: form.admin_password,
        admin_designation: form.admin_designation,
        academic_session: form.academic_session,
        current_semester: form.current_semester,
        max_supervisor_load: parseInt(form.max_supervisor_load) || 10,
        dual_supervisor_for_postgrad: Boolean(form.dual_supervisor_for_postgrad),
        auto_assign_co_supervisor: Boolean(form.auto_assign_co_supervisor),
        enable_ai_pairing: Boolean(form.enable_ai_pairing),
        instant_live_activation: Boolean(form.instant_live_activation),
      };

      const res = await api.post('/institutions/onboard', payload);
      setOnboardResult(res.data);
      setCurrentStep(5);
      toast.success(res.data.message || 'Institution onboarded successfully!');
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Onboarding failed. Please check entries.';
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  const copyToken = () => {
    if (onboardResult?.verification_token) {
      navigator.clipboard.writeText(onboardResult.verification_token);
      setCopiedToken(true);
      toast.success('Verification token copied to clipboard!');
      setTimeout(() => setCopiedToken(false), 3000);
    }
  };

  return (
    <div style={s.page}>
      {/* Top Navbar */}
      <header style={s.nav}>
        <div style={s.navInner}>
          <div style={s.brandGroup}>
            <Link to="/" style={s.brandLink}>
              <div style={s.navLogoBadge}>
                <GraduationCap size={20} color="#ffffff" strokeWidth={2.4} />
              </div>
              <div style={s.navBrandText}>
                <span style={s.navTitle}>SPSEMS Multi-School Engine</span>
                <span style={s.navSub}>Institutional Tenant Onboarding</span>
              </div>
            </Link>
            <div style={s.activeKwasuBadge}>
              <span style={s.pulseDot} />
              <span>KWASU Node Live (100%)</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <Link to="/login" style={s.loginLink}>
              Existing Login &rarr;
            </Link>
            <ThemeToggle showLabel={false} />
          </div>
        </div>
      </header>

      <main style={s.container}>
        {/* Intro Hero Banner */}
        <div style={s.hero}>
          <div style={s.heroHeader}>
            <div style={s.badge}>
              <Building2 size={14} color="#16a34a" />
              <span>Autonomous Tenant Provisioning Pipeline</span>
            </div>
            <h1 style={s.heroTitle}>Onboard Your Institution to SPSEMS</h1>
            <p style={s.heroSubtitle}>
              Join Kwara State University and other leading universities. Self-register your school,
              upload your official emblem, and let our system automatically configure a custom-branded
              portal with your school colors, degree regulations, and supervision governance.
            </p>
          </div>

          {/* Quick Presets Bar */}
          <div style={s.presetBar}>
            <span style={s.presetLabel}>Quick Fill Demo:</span>
            {SAMPLE_PRESETS.map((p) => (
              <button
                key={p.code}
                type="button"
                onClick={() => loadPreset(p)}
                style={s.presetBtn}
              >
                <span style={{ ...s.presetDot, background: p.primary }} />
                {p.name} ({p.code})
              </button>
            ))}
          </div>
        </div>

        {/* Wizard Stepper Header */}
        <div style={s.stepperWrap}>
          {[
            { step: 1, label: 'Institution Profile', icon: School },
            { step: 2, label: 'Logo & Color Palette', icon: Palette },
            { step: 3, label: 'Supervision Policies', icon: Sliders },
            { step: 4, label: 'Lead Super Admin', icon: ShieldCheck },
            { step: 5, label: 'Live Activation', icon: CheckCircle2 },
          ].map((item) => {
            const Icon = item.icon;
            const isCompleted = currentStep > item.step;
            const isCurrent = currentStep === item.step;
            return (
              <div
                key={item.step}
                onClick={() => currentStep !== 5 && item.step < currentStep && setCurrentStep(item.step)}
                style={{
                  ...s.stepItem,
                  cursor: currentStep !== 5 && item.step < currentStep ? 'pointer' : 'default',
                  opacity: currentStep >= item.step ? 1 : 0.5,
                }}
              >
                <div
                  style={{
                    ...s.stepCircle,
                    background: isCompleted
                      ? '#16a34a'
                      : isCurrent
                      ? form.primary_color || '#16a34a'
                      : 'var(--bg-card-subtle, rgba(255,255,255,0.06))',
                    borderColor: isCurrent ? form.primary_color || '#16a34a' : 'transparent',
                    color: isCompleted || isCurrent ? '#ffffff' : 'var(--text-muted, #9ca3af)',
                  }}
                >
                  {isCompleted ? <Check size={14} /> : <Icon size={14} />}
                </div>
                <div style={s.stepText}>
                  <div style={s.stepNum}>STEP {item.step}</div>
                  <div style={{ ...s.stepName, color: isCurrent ? 'var(--text-primary, #fff)' : 'var(--text-muted, #9ca3af)' }}>
                    {item.label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Multi-step Form Body */}
        <div style={s.card}>
          {/* STEP 1: IDENTITY & DOMAIN */}
          {currentStep === 1 && (
            <div style={s.stepBody}>
              <div style={s.sectionHeader}>
                <School size={22} color={form.primary_color} />
                <div>
                  <h2 style={s.sectionTitle}>Institutional Identity &amp; Educational Domain</h2>
                  <p style={s.sectionDesc}>Enter your school official registry details and academic domain.</p>
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Full Institution Name *</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. University of Ibadan"
                    value={form.name}
                    onChange={(e) => update('name', e.target.value)}
                    required
                  />
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Institution Code / Acronym *</label>
                  <input
                    style={{ ...s.input, textTransform: 'uppercase' }}
                    type="text"
                    placeholder="e.g. UI, OAU, UNILORIN"
                    value={form.code}
                    onChange={(e) => update('code', e.target.value)}
                    required
                  />
                  <span style={s.fieldHint}>Used for portal subdomain &amp; matric numbers</span>
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Official Domain Name (.edu.ng) *</label>
                  <div style={s.inputIconWrap}>
                    <Globe size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="text"
                      placeholder="e.g. ui.edu.ng"
                      value={form.official_domain}
                      onChange={(e) => update('official_domain', e.target.value)}
                      required
                    />
                  </div>
                  <span style={s.fieldHint}>Restricts student/staff self-registration to institutional email addresses</span>
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Institution Type</label>
                  <select
                    style={s.select}
                    value={form.institution_type}
                    onChange={(e) => update('institution_type', e.target.value)}
                  >
                    <option value="Federal University">Federal University</option>
                    <option value="State University">State University</option>
                    <option value="Private University">Private University</option>
                    <option value="Federal Polytechnic">Federal Polytechnic</option>
                    <option value="State Polytechnic">State Polytechnic</option>
                    <option value="College of Education">College of Education</option>
                  </select>
                </div>
              </div>

              <div style={s.grid3}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Country</label>
                  <input
                    style={s.input}
                    type="text"
                    value={form.country}
                    onChange={(e) => update('country', e.target.value)}
                  />
                </div>
                <div style={s.fieldWrap}>
                  <label style={s.label}>State</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. Oyo"
                    value={form.state}
                    onChange={(e) => update('state', e.target.value)}
                  />
                </div>
                <div style={s.fieldWrap}>
                  <label style={s.label}>City / Campus Location</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. Ibadan"
                    value={form.city}
                    onChange={(e) => update('city', e.target.value)}
                  />
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Official Contact Email *</label>
                  <div style={s.inputIconWrap}>
                    <Mail size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="email"
                      placeholder="e.g. ict@ui.edu.ng"
                      value={form.contact_email}
                      onChange={(e) => update('contact_email', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Official Phone Number</label>
                  <div style={s.inputIconWrap}>
                    <Phone size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="tel"
                      placeholder="e.g. +234 803 123 4567"
                      value={form.contact_phone}
                      onChange={(e) => update('contact_phone', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div style={s.btnRow}>
                <span />
                <button
                  type="button"
                  onClick={() => {
                    if (!form.name || !form.code || !form.official_domain || !form.contact_email) {
                      toast.error('Please fill all required fields (*) before proceeding.');
                      return;
                    }
                    setCurrentStep(2);
                  }}
                  style={{ ...s.btnPrimary, background: form.primary_color }}
                >
                  <span>Continue to Logo &amp; Color Scheme</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: OFFICIAL LOGO & COLOR SCHEME EXTRACTION */}
          {currentStep === 2 && (
            <div style={s.stepBody}>
              <div style={s.sectionHeader}>
                <Palette size={22} color={form.primary_color} />
                <div>
                  <h2 style={s.sectionTitle}>Official Logo &amp; Automatic Color Scheme Extraction</h2>
                  <p style={s.sectionDesc}>
                    Upload your school official emblem. The system automatically inspects and extracts
                    your university brand colors to style your institution portal!
                  </p>
                </div>
              </div>

              {/* Logo Upload Dropzone */}
              <div style={s.uploadContainer}>
                <div
                  style={s.dropzone}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/svg+xml,image/webp"
                    style={{ display: 'none' }}
                    onChange={handleLogoFileChange}
                  />
                  {logoPreview ? (
                    <div style={s.logoPreviewContainer}>
                      <img src={resolveLogoUrl(logoPreview)} alt="School Logo Preview" style={s.logoPreviewImg} />
                      <div style={s.logoPreviewMeta}>
                        <div style={s.logoTitle}>{logoFile ? logoFile.name : (form.name ? `${form.name} Emblem` : 'Uploaded Emblem')}</div>
                        <div style={s.logoSub}>Click to replace emblem (PNG, JPG, SVG, WEBP)</div>
                      </div>
                    </div>
                  ) : (
                    <div style={s.emptyUpload}>
                      <Upload size={32} color={form.primary_color} />
                      <p style={s.uploadText}>Click or drag &amp; drop your official university emblem</p>
                      <span style={s.uploadHint}>High resolution transparent PNG or SVG recommended</span>
                    </div>
                  )}
                </div>

                {analyzingLogo && (
                  <div style={s.analyzingBar}>
                    <Sparkles size={16} className="spin" color={form.primary_color} />
                    <span>Analyzing pixel data &amp; extracting institutional color scheme...</span>
                  </div>
                )}
              </div>

              {/* Color Scheme Picker & Extracted Swatches */}
              <div style={s.colorSection}>
                <div style={s.colorSectionHead}>
                  <Sparkles size={16} color={form.primary_color} />
                  <span style={s.colorSectionTitle}>Extracted Institutional Brand Swatches</span>
                  <span style={s.colorSectionNote}>(Click any swatch to set as Primary Color)</span>
                </div>

                <div style={s.paletteGrid}>
                  {extractedPalette.map((color, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => update('primary_color', color)}
                      style={{
                        ...s.paletteCard,
                        border: form.primary_color.toLowerCase() === color.toLowerCase()
                          ? `2px solid ${color}`
                          : '1px solid var(--border-card, rgba(255,255,255,0.1))',
                        boxShadow: form.primary_color.toLowerCase() === color.toLowerCase()
                          ? `0 0 12px ${color}66`
                          : 'none'
                      }}
                    >
                      <div style={{ ...s.colorSwatchBox, background: color }} />
                      <span style={s.colorHexText}>{color}</span>
                      {form.primary_color.toLowerCase() === color.toLowerCase() && (
                        <span style={{ ...s.activeColorPill, background: color }}>Primary</span>
                      )}
                    </button>
                  ))}
                </div>

                {/* Fine-Tuning Inputs */}
                <div style={s.colorInputsRow}>
                  <div style={s.colorPickerGroup}>
                    <label style={s.label}>Primary Brand Color (Buttons &amp; Headers)</label>
                    <div style={s.colorInputFlex}>
                      <input
                        type="color"
                        value={form.primary_color}
                        onChange={(e) => update('primary_color', e.target.value)}
                        style={s.nativeColorInput}
                      />
                      <input
                        type="text"
                        value={form.primary_color}
                        onChange={(e) => update('primary_color', e.target.value)}
                        style={{ ...s.input, width: 120, fontFamily: 'monospace' }}
                      />
                    </div>
                  </div>

                  <div style={s.colorPickerGroup}>
                    <label style={s.label}>Secondary / Dark Surface Color</label>
                    <div style={s.colorInputFlex}>
                      <input
                        type="color"
                        value={form.secondary_color}
                        onChange={(e) => update('secondary_color', e.target.value)}
                        style={s.nativeColorInput}
                      />
                      <input
                        type="text"
                        value={form.secondary_color}
                        onChange={(e) => update('secondary_color', e.target.value)}
                        style={{ ...s.input, width: 120, fontFamily: 'monospace' }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* LIVE DYNAMIC PORTAL PREVIEW */}
              <div style={s.previewCard}>
                <div style={s.previewHeader}>
                  <Layers size={16} color={form.primary_color} />
                  <span style={s.previewTitle}>Live Portal Theme Preview</span>
                  <span style={s.previewSubtitle}>Real-time simulation of your school portal layout</span>
                </div>

                <div style={s.mockPortal}>
                  {/* Mock Navbar */}
                  <div style={{ ...s.mockNav, borderTop: `4px solid ${form.primary_color}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {logoPreview ? (
                        <img src={resolveLogoUrl(logoPreview)} alt="Logo" style={s.mockLogo} />
                      ) : (
                        <div style={{ ...s.mockLogo, background: `${form.primary_color}22`, border: `1px solid ${form.primary_color}55`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <School size={16} color={form.primary_color} />
                        </div>
                      )}
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 13, color: 'var(--text-primary, #fff)' }}>
                          {form.name || 'Your University Name'} ({form.code || 'CODE'})
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted, #9ca3af)' }}>
                          Smart Project Supervision System
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span style={{ ...s.mockBadge, background: `${form.primary_color}22`, color: form.primary_color, borderColor: `${form.primary_color}55` }}>
                        Session: {form.academic_session}
                      </span>
                    </div>
                  </div>

                  {/* Mock Portal Content */}
                  <div style={s.mockContent}>
                    <div style={s.mockBanner}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: 15, color: 'var(--text-primary, #fff)' }}>
                          Welcome to {form.code || 'School'} SPSEMS Portal
                        </h4>
                        <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-muted, #9ca3af)' }}>
                          Academic governance, AI supervisor matching, and thesis supervision.
                        </p>
                      </div>
                      <button
                        type="button"
                        style={{ ...s.mockBtn, background: form.primary_color }}
                      >
                        Portal Action
                      </button>
                    </div>

                    <div style={s.mockStatsGrid}>
                      <div style={s.mockStat}>
                        <div style={{ fontSize: 10, color: 'var(--text-dim, #6b7280)' }}>STATUS</div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: form.primary_color }}>Active Node</div>
                      </div>
                      <div style={s.mockStat}>
                        <div style={{ fontSize: 10, color: 'var(--text-dim, #6b7280)' }}>DOMAIN</div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary, #fff)' }}>
                          {form.official_domain || 'institution.edu.ng'}
                        </div>
                      </div>
                      <div style={s.mockStat}>
                        <div style={{ fontSize: 10, color: 'var(--text-dim, #6b7280)' }}>SUPERVISION</div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary, #fff)' }}>
                          Dual Co-Supervisor: {form.dual_supervisor_for_postgrad ? 'Enabled' : 'Disabled'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div style={s.btnRow}>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  style={s.btnSecondary}
                >
                  <ArrowLeft size={16} />
                  <span>Back to Profile</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  style={{ ...s.btnPrimary, background: form.primary_color }}
                >
                  <span>Continue to Supervision Policies</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: ACADEMIC GOVERNANCE & SUPERVISION POLICIES */}
          {currentStep === 3 && (
            <div style={s.stepBody}>
              <div style={s.sectionHeader}>
                <Sliders size={22} color={form.primary_color} />
                <div>
                  <h2 style={s.sectionTitle}>Academic Policies &amp; Degree Supervision Governance</h2>
                  <p style={s.sectionDesc}>
                    Configure institutional rules, session parameters, and postgraduate dual-supervisor regulations.
                  </p>
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Current Academic Session</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. 2025/2026"
                    value={form.academic_session}
                    onChange={(e) => update('academic_session', e.target.value)}
                  />
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Current Semester</label>
                  <select
                    style={s.select}
                    value={form.current_semester}
                    onChange={(e) => update('current_semester', e.target.value)}
                  >
                    <option value="First Semester">First Semester</option>
                    <option value="Second Semester">Second Semester</option>
                  </select>
                </div>
              </div>

              <div style={s.fieldWrap}>
                <label style={s.label}>Max Project Supervision Load per Lecturer</label>
                <input
                  style={s.input}
                  type="number"
                  min="1"
                  max="30"
                  value={form.max_supervisor_load}
                  onChange={(e) => update('max_supervisor_load', e.target.value)}
                />
                <span style={s.fieldHint}>Maximum number of students assigned to a single supervisor</span>
              </div>

              {/* Governance Checkboxes */}
              <div style={s.policyBox}>
                <div style={s.policyItem}>
                  <input
                    type="checkbox"
                    id="dual_sup"
                    checked={form.dual_supervisor_for_postgrad}
                    onChange={(e) => update('dual_supervisor_for_postgrad', e.target.checked)}
                    style={s.checkbox}
                  />
                  <div>
                    <label htmlFor="dual_sup" style={s.policyLabel}>
                      Dual Supervisor Requirement for Postgraduate Students (MSc / PhD)
                    </label>
                    <p style={s.policyDesc}>
                      Enforces that every Master's and Doctoral student is assigned both a Main Supervisor and a Co-Supervisor.
                    </p>
                  </div>
                </div>

                <div style={s.policyItem}>
                  <input
                    type="checkbox"
                    id="auto_co"
                    checked={form.auto_assign_co_supervisor}
                    onChange={(e) => update('auto_assign_co_supervisor', e.target.checked)}
                    style={s.checkbox}
                  />
                  <div>
                    <label htmlFor="auto_co" style={s.policyLabel}>
                      Automatic Random Assignment of Co-Supervisors
                    </label>
                    <p style={s.policyDesc}>
                      When a postgraduate student registers, the system randomly assigns a qualified co-supervisor from the department.
                    </p>
                  </div>
                </div>

                <div style={s.policyItem}>
                  <input
                    type="checkbox"
                    id="ai_pair"
                    checked={form.enable_ai_pairing}
                    onChange={(e) => update('enable_ai_pairing', e.target.checked)}
                    style={s.checkbox}
                  />
                  <div>
                    <label htmlFor="ai_pair" style={s.policyLabel}>
                      AI-Assisted Matchmaking &amp; Risk Forecasting
                    </label>
                    <p style={s.policyDesc}>
                      Activates TF-IDF vector similarity matching and machine learning predictive risk assessment for student projects.
                    </p>
                  </div>
                </div>
              </div>

              <div style={s.btnRow}>
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  style={s.btnSecondary}
                >
                  <ArrowLeft size={16} />
                  <span>Back to Branding</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  style={{ ...s.btnPrimary, background: form.primary_color }}
                >
                  <span>Continue to Lead Admin Account</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: LEAD SUPER ADMIN ACCOUNT CREATION */}
          {currentStep === 4 && (
            <div style={s.stepBody}>
              <div style={s.sectionHeader}>
                <ShieldCheck size={22} color={form.primary_color} />
                <div>
                  <h2 style={s.sectionTitle}>Institutional Super Administrator Credentials</h2>
                  <p style={s.sectionDesc}>
                    Create the primary institutional administrator account (Director of ICT / Dean) for {form.name || 'your institution'}.
                  </p>
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Administrator Full Name *</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. Prof. A. O. Adeleke"
                    value={form.admin_fullname}
                    onChange={(e) => update('admin_fullname', e.target.value)}
                    required
                  />
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Administrative Designation / Title</label>
                  <input
                    style={s.input}
                    type="text"
                    placeholder="e.g. Director of ICT / HOD"
                    value={form.admin_designation}
                    onChange={(e) => update('admin_designation', e.target.value)}
                  />
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Admin Username *</label>
                  <div style={s.inputIconWrap}>
                    <User size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="text"
                      placeholder="e.g. ui_admin"
                      value={form.admin_username}
                      onChange={(e) => update('admin_username', e.target.value)}
                      required
                    />
                  </div>
                  <span style={s.fieldHint}>Used to sign in to the administrative portal</span>
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Admin Official Contact Email *</label>
                  <input
                    style={s.input}
                    type="email"
                    value={form.contact_email}
                    onChange={(e) => update('contact_email', e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={s.grid2}>
                <div style={s.fieldWrap}>
                  <label style={s.label}>Password *</label>
                  <div style={s.inputIconWrap}>
                    <Lock size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="password"
                      placeholder="Enter secure password"
                      value={form.admin_password}
                      onChange={(e) => update('admin_password', e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={s.fieldWrap}>
                  <label style={s.label}>Confirm Password *</label>
                  <div style={s.inputIconWrap}>
                    <Lock size={16} style={s.inputIcon} />
                    <input
                      style={{ ...s.input, paddingLeft: 38 }}
                      type="password"
                      placeholder="Confirm password"
                      value={form.confirm_password}
                      onChange={(e) => update('confirm_password', e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Instant Live Activation Option */}
              <div style={s.activationBox}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <input
                    type="checkbox"
                    id="instant_act"
                    checked={form.instant_live_activation}
                    onChange={(e) => update('instant_live_activation', e.target.checked)}
                    style={s.checkbox}
                  />
                  <div>
                    <label htmlFor="instant_act" style={{ ...s.policyLabel, color: 'var(--text-primary, #fff)' }}>
                      Instant Live Activation &amp; Sandbox Verification (Recommended)
                    </label>
                    <p style={s.policyDesc}>
                      Instantly verifies educational domain ownership, provisions isolated tenant tables,
                      and enables immediate live login for staff and students without waiting for external DNS propagation.
                    </p>
                  </div>
                </div>
              </div>

              <div style={s.btnRow}>
                <button
                  type="button"
                  onClick={() => setCurrentStep(3)}
                  style={s.btnSecondary}
                >
                  <ArrowLeft size={16} />
                  <span>Back to Policies</span>
                </button>
                <button
                  type="button"
                  onClick={handleFinalSubmit}
                  disabled={busy}
                  style={{
                    ...s.btnPrimary,
                    background: form.primary_color,
                    opacity: busy ? 0.7 : 1,
                  }}
                >
                  {busy ? (
                    <>
                      <Sparkles size={16} className="spin" />
                      <span>Provisioning Institution Tenant...</span>
                    </>
                  ) : (
                    <>
                      <span>Complete Onboarding &amp; Launch Portal</span>
                      <CheckCircle2 size={16} />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP 5: ONBOARDING SUCCESS & LIVE PORTAL LAUNCH */}
          {currentStep === 5 && onboardResult && (
            <div style={s.successStep}>
              <div style={s.successBadgeWrap}>
                <div style={{ ...s.successIconCircle, background: `${form.primary_color}22`, border: `2px solid ${form.primary_color}` }}>
                  <CheckCircle2 size={42} color={form.primary_color} />
                </div>
                <h2 style={s.successTitle}>Institution Successfully Onboarded!</h2>
                <p style={s.successDesc}>
                  <b>{onboardResult.institution_name}</b> ({onboardResult.institution_code}) is now active on the SPSEMS multi-school network.
                </p>
              </div>

              {/* Tenant Credentials Summary Card */}
              <div style={s.summaryCard}>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Institution Node</span>
                  <span style={s.summaryVal}>{onboardResult.institution_name} ({onboardResult.institution_code})</span>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Subdomain Slug</span>
                  <code style={s.codeSnippet}>{onboardResult.subdomain_slug}.spsems.edu.ng</code>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Official Email (Login Username)</span>
                  <span style={s.summaryVal}>
                    <code style={s.codeSnippet}>{form.email || onboardResult.admin_username}</code>
                  </span>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Lead Admin User</span>
                  <span style={s.summaryVal}>
                    Username: <code style={s.codeSnippet}>{onboardResult.admin_username}</code>
                  </span>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Branding Primary Color</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 14, height: 14, borderRadius: 3, background: form.primary_color }} />
                    <code style={s.codeSnippet}>{form.primary_color}</code>
                  </div>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Verification Token</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <code style={s.codeSnippet}>{onboardResult.verification_token}</code>
                    <button type="button" onClick={copyToken} style={s.copyBtn}>
                      {copiedToken ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                      <span>{copiedToken ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Dedicated School Login URL</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <code style={s.codeSnippet}>/login/{onboardResult.subdomain_slug}</code>
                    <button
                      type="button"
                      onClick={() => {
                        const fullUrl = `${window.location.origin}/login/${onboardResult.subdomain_slug}`;
                        navigator.clipboard.writeText(fullUrl);
                        toast.success('Dedicated school login URL copied to clipboard!');
                      }}
                      style={s.copyBtn}
                    >
                      <Copy size={12} />
                      <span>Copy URL</span>
                    </button>
                  </div>
                </div>
                <div style={s.summaryRow}>
                  <span style={s.summaryLabel}>Live Status</span>
                  <span style={{ ...s.livePill, background: '#16a34a' }}>
                    100% Onboarded &amp; Operational
                  </span>
                </div>
              </div>

              <div style={s.successActionRow}>
                <button
                  type="button"
                  onClick={() => navigate(`/login/${onboardResult.subdomain_slug}?token=${encodeURIComponent(onboardResult.verification_token || '')}&anim=1`)}
                  style={{ ...s.btnPrimary, background: form.primary_color }}
                >
                  <span>Launch {onboardResult.institution_code} SPSEMS Login</span>
                  <ArrowRight size={16} />
                </button>
                <Link to="/" style={s.btnSecondary}>
                  <span>Return to Home</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ── STYLES ───────────────────────────────────────────────────────────────────
const s = {
  page: {
    minHeight: '100vh',
    background: 'var(--bg-app, #0a0a0a)',
    color: 'var(--text-primary, #ffffff)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    paddingBottom: 60,
  },
  nav: {
    borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
    background: 'var(--bg-topbar, #0f0f0f)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
  },
  navInner: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '12px 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  brandLink: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    textDecoration: 'none',
  },
  navLogoBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    background: 'linear-gradient(135deg, #16a34a 0%, #059669 50%, #0284c7 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 12px rgba(22, 163, 74, 0.35)',
    flexShrink: 0,
  },
  navBrandText: {
    display: 'flex',
    flexDirection: 'column',
  },
  navTitle: {
    fontWeight: 700,
    fontSize: 15,
    color: 'var(--text-primary, #ffffff)',
    letterSpacing: '-0.2px',
  },
  navSub: {
    fontSize: 11,
    color: 'var(--text-muted, #9ca3af)',
  },
  activeKwasuBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    background: 'rgba(22,163,74,0.12)',
    border: '1px solid rgba(22,163,74,0.3)',
    color: '#22c55e',
    fontSize: 11,
    fontWeight: 600,
    padding: '3px 10px',
    borderRadius: 999,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
    background: '#22c55e',
    boxShadow: '0 0 8px #22c55e',
  },
  loginLink: {
    color: 'var(--text-muted, #9ca3af)',
    textDecoration: 'none',
    fontSize: 13,
    fontWeight: 500,
  },
  container: {
    maxWidth: 960,
    margin: '0 auto',
    padding: '32px 20px',
  },
  hero: {
    marginBottom: 28,
  },
  heroHeader: {
    textAlign: 'center',
    maxWidth: 720,
    margin: '0 auto 20px',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    background: 'rgba(22,163,74,0.12)',
    border: '1px solid rgba(22,163,74,0.25)',
    color: '#22c55e',
    fontSize: 12,
    fontWeight: 600,
    padding: '4px 12px',
    borderRadius: 999,
    marginBottom: 12,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: 800,
    letterSpacing: '-0.6px',
    margin: '0 0 10px',
    color: 'var(--text-primary, #ffffff)',
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'var(--text-muted, #9ca3af)',
    lineHeight: 1.6,
    margin: 0,
  },
  presetBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: 8,
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.07))',
    padding: '10px 16px',
    borderRadius: 12,
  },
  presetLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #9ca3af)',
    marginRight: 4,
  },
  presetBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.04))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.08))',
    color: 'var(--text-secondary, #e5e7eb)',
    fontSize: 12,
    fontWeight: 500,
    padding: '5px 12px',
    borderRadius: 8,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },
  presetDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },
  stepperWrap: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
    gap: 8,
    overflowX: 'auto',
    paddingBottom: 6,
  },
  stepItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 12px',
    borderRadius: 10,
    transition: 'all 0.15s ease',
  },
  stepCircle: {
    width: 30,
    height: 30,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 12,
    border: '2px solid transparent',
    flexShrink: 0,
  },
  stepText: {
    display: 'flex',
    flexDirection: 'column',
  },
  stepNum: {
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--text-dim, #6b7280)',
    letterSpacing: '0.5px',
  },
  stepName: {
    fontSize: 12,
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  card: {
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.08))',
    borderRadius: 16,
    boxShadow: 'var(--shadow-card, 0 4px 20px rgba(0,0,0,0.5))',
    padding: '32px 36px',
  },
  stepBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: 22,
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
    paddingBottom: 16,
    borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 700,
    margin: '0 0 4px',
    color: 'var(--text-primary, #ffffff)',
  },
  sectionDesc: {
    fontSize: 13,
    color: 'var(--text-muted, #9ca3af)',
    margin: 0,
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: 18,
  },
  grid3: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 16,
  },
  fieldWrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-secondary, #e5e7eb)',
  },
  input: {
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-input, rgba(255,255,255,0.1))',
    borderRadius: 8,
    color: 'var(--text-primary, #ffffff)',
    fontSize: 14,
    padding: '10px 14px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  select: {
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-input, rgba(255,255,255,0.1))',
    borderRadius: 8,
    color: 'var(--text-primary, #ffffff)',
    fontSize: 14,
    padding: '10px 14px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  inputIconWrap: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  inputIcon: {
    position: 'absolute',
    left: 12,
    color: 'var(--text-dim, #6b7280)',
    pointerEvents: 'none',
  },
  fieldHint: {
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
  },
  uploadContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  dropzone: {
    border: '2px dashed var(--border-input, rgba(255,255,255,0.15))',
    borderRadius: 12,
    padding: '24px 20px',
    textAlign: 'center',
    cursor: 'pointer',
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.02))',
    transition: 'border-color 0.2s ease',
  },
  emptyUpload: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 8,
  },
  uploadText: {
    fontSize: 14,
    fontWeight: 600,
    color: 'var(--text-primary, #ffffff)',
    margin: 0,
  },
  uploadHint: {
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
  },
  logoPreviewContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  logoPreviewImg: {
    width: 64,
    height: 64,
    objectFit: 'contain',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.05)',
    padding: 6,
  },
  logoPreviewMeta: {
    textAlign: 'left',
  },
  logoTitle: {
    fontWeight: 700,
    fontSize: 14,
    color: 'var(--text-primary, #ffffff)',
  },
  logoSub: {
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
  },
  analyzingBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 12,
    color: '#22c55e',
    fontWeight: 500,
    padding: '8px 12px',
    borderRadius: 8,
    background: 'rgba(22,163,74,0.1)',
  },
  colorSection: {
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.02))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
    borderRadius: 12,
    padding: 18,
  },
  colorSectionHead: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  colorSectionTitle: {
    fontSize: 13,
    fontWeight: 700,
    color: 'var(--text-primary, #ffffff)',
  },
  colorSectionNote: {
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
  },
  paletteGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
    gap: 10,
    marginBottom: 16,
  },
  paletteCard: {
    background: 'var(--bg-input, #0f0f0f)',
    borderRadius: 8,
    padding: '8px 10px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 6,
    cursor: 'pointer',
    position: 'relative',
  },
  colorSwatchBox: {
    width: '100%',
    height: 34,
    borderRadius: 6,
  },
  colorHexText: {
    fontFamily: 'monospace',
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-secondary, #e5e7eb)',
  },
  activeColorPill: {
    position: 'absolute',
    top: 4,
    right: 4,
    fontSize: 9,
    fontWeight: 700,
    color: '#ffffff',
    padding: '2px 5px',
    borderRadius: 4,
    textTransform: 'uppercase',
  },
  colorInputsRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 20,
    paddingTop: 12,
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
  },
  colorPickerGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  colorInputFlex: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  nativeColorInput: {
    width: 40,
    height: 38,
    border: 'none',
    borderRadius: 8,
    background: 'none',
    cursor: 'pointer',
  },
  previewCard: {
    border: '1px solid var(--border-card, rgba(255,255,255,0.08))',
    borderRadius: 12,
    overflow: 'hidden',
    background: 'var(--bg-input, #0f0f0f)',
  },
  previewHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 16px',
    background: 'var(--bg-card-header, #171717)',
    borderBottom: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
  },
  previewTitle: {
    fontWeight: 700,
    fontSize: 12,
    color: 'var(--text-primary, #ffffff)',
  },
  previewSubtitle: {
    fontSize: 11,
    color: 'var(--text-dim, #6b7280)',
    marginLeft: 6,
  },
  mockPortal: {
    padding: 16,
    background: 'var(--bg-app, #0a0a0a)',
  },
  mockNav: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 14px',
    background: 'var(--bg-topbar, #111111)',
    borderRadius: 8,
    marginBottom: 12,
  },
  mockLogo: {
    width: 28,
    height: 28,
    objectFit: 'contain',
  },
  mockBadge: {
    fontSize: 10,
    fontWeight: 600,
    padding: '3px 8px',
    borderRadius: 6,
    border: '1px solid',
  },
  mockContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  mockBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.06))',
    padding: '14px 16px',
    borderRadius: 8,
  },
  mockBtn: {
    color: '#ffffff',
    border: 'none',
    borderRadius: 6,
    padding: '7px 14px',
    fontSize: 11,
    fontWeight: 700,
    cursor: 'default',
  },
  mockStatsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 10,
  },
  mockStat: {
    background: 'var(--bg-card, #141414)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.06))',
    padding: '10px 12px',
    borderRadius: 8,
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  policyBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.02))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
    borderRadius: 12,
    padding: 18,
  },
  policyItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
  },
  checkbox: {
    marginTop: 4,
    accentColor: '#16a34a',
    width: 17,
    height: 17,
    cursor: 'pointer',
  },
  policyLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-primary, #ffffff)',
    cursor: 'pointer',
  },
  policyDesc: {
    fontSize: 12,
    color: 'var(--text-muted, #9ca3af)',
    margin: '3px 0 0',
    lineHeight: 1.4,
  },
  activationBox: {
    background: 'rgba(22,163,74,0.08)',
    border: '1px solid rgba(22,163,74,0.25)',
    borderRadius: 12,
    padding: 16,
  },
  btnRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 16,
    borderTop: '1px solid var(--border-subtle, rgba(255,255,255,0.06))',
    marginTop: 8,
  },
  btnPrimary: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    color: '#ffffff',
    border: 'none',
    borderRadius: 8,
    padding: '11px 22px',
    fontSize: 14,
    fontWeight: 700,
    cursor: 'pointer',
    transition: 'opacity 0.15s ease',
  },
  btnSecondary: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    background: 'var(--bg-card-subtle, rgba(255,255,255,0.05))',
    border: '1px solid var(--border-subtle, rgba(255,255,255,0.1))',
    color: 'var(--text-secondary, #e5e7eb)',
    borderRadius: 8,
    padding: '11px 18px',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    textDecoration: 'none',
  },
  successStep: {
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 24,
    padding: '20px 0',
  },
  successBadgeWrap: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
  },
  successIconCircle: {
    width: 80,
    height: 80,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  successTitle: {
    fontSize: 26,
    fontWeight: 800,
    margin: 0,
    color: 'var(--text-primary, #ffffff)',
  },
  successDesc: {
    fontSize: 14,
    color: 'var(--text-muted, #9ca3af)',
    margin: 0,
  },
  summaryCard: {
    width: '100%',
    maxWidth: 620,
    background: 'var(--bg-input, #0f0f0f)',
    border: '1px solid var(--border-card, rgba(255,255,255,0.08))',
    borderRadius: 12,
    padding: '16px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    textAlign: 'left',
  },
  summaryRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize: 13,
  },
  summaryLabel: {
    color: 'var(--text-muted, #9ca3af)',
    fontWeight: 500,
  },
  summaryVal: {
    fontWeight: 600,
    color: 'var(--text-primary, #ffffff)',
  },
  codeSnippet: {
    fontFamily: 'monospace',
    background: 'rgba(255,255,255,0.06)',
    padding: '3px 8px',
    borderRadius: 5,
    fontSize: 12,
    color: '#22c55e',
  },
  copyBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    background: 'rgba(255,255,255,0.08)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: 'var(--text-primary, #fff)',
    borderRadius: 5,
    padding: '3px 8px',
    fontSize: 11,
    cursor: 'pointer',
  },
  livePill: {
    fontSize: 11,
    fontWeight: 700,
    color: '#ffffff',
    padding: '3px 10px',
    borderRadius: 999,
  },
  successActionRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    marginTop: 8,
  },
};
