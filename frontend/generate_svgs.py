"""
Generate high-fidelity industrial SVG assets for the IntelliTwin dashboard.
Renders CNC Machine, Robotic Arm, Conveyor Belt, Air Compressor, and Hydraulic Press.
"""

import os

SVG_DIR = r"c:\Users\shiks\Downloads\res paper\frontend\assets"
os.makedirs(SVG_DIR, exist_ok=True)

# 1. CNC Machine SVG
cnc_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" fill="none">
  <rect x="20" y="25" width="120" height="60" rx="4" fill="#1e293b" stroke="#334155" stroke-width="2"/>
  <rect x="35" y="35" width="50" height="35" rx="2" fill="#0f172a" stroke="#475569" stroke-width="1.5"/>
  <circle cx="60" cy="52" r="8" fill="#10b981" opacity="0.3"/>
  <path d="M55 52h10M60 47v10" stroke="#10b981" stroke-width="1.5"/>
  <rect x="95" y="35" width="35" height="40" rx="2" fill="#0f172a" stroke="#38bdf8" stroke-width="1"/>
  <line x1="100" y1="45" x2="125" y2="45" stroke="#38bdf8" stroke-width="1.5"/>
  <line x1="100" y1="52" x2="120" y2="52" stroke="#64748b" stroke-width="1"/>
  <line x1="100" y1="59" x2="115" y2="59" stroke="#64748b" stroke-width="1"/>
  <circle cx="120" cy="68" r="3" fill="#10b981"/>
  <rect x="15" y="85" width="130" height="6" rx="2" fill="#334155"/>
</svg>'''

# 2. Robotic Arm SVG
robot_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" fill="none">
  <rect x="50" y="80" width="60" height="12" rx="3" fill="#334155" stroke="#475569" stroke-width="1.5"/>
  <circle cx="80" cy="75" r="10" fill="#f59e0b" stroke="#d97706" stroke-width="2"/>
  <path d="M80 75 L65 45" stroke="#f59e0b" stroke-width="8" stroke-linecap="round"/>
  <circle cx="65" cy="45" r="7" fill="#1e293b" stroke="#f59e0b" stroke-width="2"/>
  <path d="M65 45 L105 30" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/>
  <circle cx="105" cy="30" r="5" fill="#1e293b" stroke="#f59e0b" stroke-width="2"/>
  <path d="M105 30 L120 35" stroke="#94a3b8" stroke-width="4"/>
  <path d="M120 32 L128 26 M120 38 L128 44" stroke="#e2e8f0" stroke-width="3" stroke-linecap="round"/>
</svg>'''

# 3. Conveyor Belt SVG
conveyor_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120" fill="none">
  <!-- Belt Base -->
  <polygon points="30,85 170,45 180,60 40,100" fill="#1e293b" stroke="#ef4444" stroke-width="1.5"/>
  <!-- Conveyor Belt Top -->
  <polygon points="32,83 168,43 160,35 24,75" fill="#334155" stroke="#64748b" stroke-width="1"/>
  <!-- Rollers -->
  <circle cx="35" cy="88" r="8" fill="#475569" stroke="#ef4444" stroke-width="2"/>
  <circle cx="165" cy="48" r="8" fill="#475569" stroke="#ef4444" stroke-width="2"/>
  <circle cx="100" cy="68" r="6" fill="#334155" stroke="#64748b" stroke-width="1.5"/>
  <!-- Roller Spokes -->
  <line x1="35" y1="80" x2="35" y2="96" stroke="#ef4444" stroke-width="1.5"/>
  <line x1="165" y1="40" x2="165" y2="56" stroke="#ef4444" stroke-width="1.5"/>
  <!-- Motor Assembly -->
  <rect x="18" y="70" width="16" height="24" rx="2" fill="#ef4444" opacity="0.3"/>
  <rect x="150" y="25" width="22" height="18" rx="2" fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/>
  <!-- Warning Glow -->
  <circle cx="165" cy="48" r="14" fill="#ef4444" opacity="0.25"/>
  <text x="100" y="115" text-anchor="middle" fill="#ef4444" font-size="10" font-family="sans-serif" font-weight="bold">CRITICAL DEGRADATION</text>
</svg>'''

# 4. Air Compressor SVG
compressor_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" fill="none">
  <rect x="25" y="40" width="110" height="45" rx="22" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>
  <rect x="40" y="20" width="35" height="22" rx="3" fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
  <rect x="85" y="24" width="30" height="18" rx="2" fill="#0f172a" stroke="#64748b" stroke-width="1"/>
  <circle cx="120" cy="30" r="7" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <line x1="120" y1="30" x2="123" y2="26" stroke="#ef4444" stroke-width="1.5"/>
  <rect x="35" y="85" width="12" height="8" rx="1" fill="#475569"/>
  <rect x="110" y="85" width="12" height="8" rx="1" fill="#475569"/>
</svg>'''

# 5. Hydraulic Press SVG
press_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" fill="none">
  <rect x="30" y="15" width="100" height="12" rx="2" fill="#334155" stroke="#f59e0b" stroke-width="1.5"/>
  <rect x="30" y="75" width="100" height="15" rx="2" fill="#334155" stroke="#475569" stroke-width="1.5"/>
  <line x1="42" y1="27" x2="42" y2="75" stroke="#64748b" stroke-width="5"/>
  <line x1="118" y1="27" x2="118" y2="75" stroke="#64748b" stroke-width="5"/>
  <rect x="65" y="27" width="30" height="20" fill="#0f172a" stroke="#f59e0b" stroke-width="1.5"/>
  <rect x="55" y="47" width="50" height="10" rx="1" fill="#f59e0b" opacity="0.8"/>
  <circle cx="80" cy="65" r="6" fill="#ef4444" opacity="0.4"/>
</svg>'''

with open(os.path.join(SVG_DIR, "cnc_machine.svg"), "w") as f: f.write(cnc_svg)
with open(os.path.join(SVG_DIR, "robotic_arm.svg"), "w") as f: f.write(robot_svg)
with open(os.path.join(SVG_DIR, "conveyor_belt.svg"), "w") as f: f.write(conveyor_svg)
with open(os.path.join(SVG_DIR, "air_compressor.svg"), "w") as f: f.write(compressor_svg)
with open(os.path.join(SVG_DIR, "hydraulic_press.svg"), "w") as f: f.write(press_svg)

print("Created 5 high-fidelity machine SVGs in frontend/assets!")
