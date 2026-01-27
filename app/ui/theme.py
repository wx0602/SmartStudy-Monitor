# app/ui/theme.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    name: str
    bg_image: str
    bg: str
    card: str
    card2: str
    border: str
    text: str
    subtext: str
    primary: str
    good: str
    warn: str
    bad: str
    sidebar_bg_image: str


# ✅ 低饱和、耐看的配色（明暗两套）
# ✅ 亮色：把 card2 拉开一些，让渐变更明显（白 -> 更浅蓝）
LIGHT = Theme(
    name="light",
    bg_image="app/ui/light.jpg",
    bg="#F5F7FB",
    card="#FFFFFF",
    card2="#D7E8FF",
    border="#DCE6F5",
    text="#1F2A37",
    subtext="#64748B",

    primary="#3B82C4",   # 主蓝（不变）

    # ✅ 更“蓝系友好”的状态色
    good="#A0BF52",   # 冷青绿（高级）
    warn="#FFFDD0",   # ✅ 浅透明黄（奶油黄 / 香草黄）
    bad="#F0ADA0",    # 玫瑰红（克制）
    sidebar_bg_image="app/ui/lightbar.jpg",
)


DARK = Theme(
    name="dark",
    bg_image="app/ui/dark.jpg",
    bg="#070B14",
    card="#071426",
    card2="#163A66",
    border="#1D3557",
    text="#E5E7EB",
    subtext="#9AA6B2",

    primary="#6BA6D6",   # 暗色主蓝（不变）

    # ✅ 暗色更稳、更柔
    good="#8EAF8C",   # 冷青绿
    warn="#BBA988",   # 冷金（不橙）
    bad="#662B1F",    # 暗玫瑰红
    sidebar_bg_image="app/ui/darkbar.jpg",
)


def theme_by_name(name: str) -> Theme:
    return DARK if name == "dark" else LIGHT


def qss(t: Theme) -> str:
    # ✅ 卡片背景：明暗都使用渐变
    card_bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t.card}, stop:1 {t.card2})"

    # ✅ 视频内层：亮色更轻，暗色更稳
    video_inner_bg = "rgba(0,0,0,0.32)" if t.name == "dark" else "rgba(255,255,255,0.28)"

    # ✅ Container：右侧闹钟/计时器模块背景（玻璃层）
    container_bg = "rgba(255,255,255,0.06)" if t.name == "dark" else "rgba(255,255,255,0.35)"

    # ✅ 右侧 SidebarContent：更克制的磨砂（按主题）
    if t.name == "dark":
        sidebar_overlay = "rgba(8,18,32,0.34)"
        sidebar_border  = "rgba(120, 180, 255, 0.22)"
        toolbtn_hover_bg = "rgba(107,166,214,0.12)"
        checkbox_hover_bg = "rgba(107,166,214,0.10)"
        prog_bg = "rgba(255,255,255,0.08)"
        state_inactive_bg = "rgba(255,255,255,0.06)"
        state_active_text = "#0B1220"
        alert1_text = "#0B1220"

        # ✅ 额外：暗色高光边（更科技）
        card_border = "rgba(255,255,255,0.08)"            # 外边更像玻璃
        card_highlight = "rgba(255,255,255,0.06)"         # 顶部内高光
        card_highlight2 = "rgba(255,255,255,0.02)"        # 下方渐隐
        hero_border = "rgba(255,255,255,0.09)"
    else:
        sidebar_overlay = "rgba(255,255,255,0.20)"
        sidebar_border  = "rgba(120, 170, 255, 0.22)"
        toolbtn_hover_bg = "rgba(59,130,196,0.10)"
        checkbox_hover_bg = "rgba(59,130,196,0.08)"
        prog_bg = "rgba(255,255,255,0.45)"
        state_inactive_bg = "rgba(255,255,255,0.45)"
        state_active_text = "#1F2A37"
        alert1_text = "#1F2A37"

        # ✅ 亮色：保持边框用主题 border
        card_border = t.border
        card_highlight = "rgba(255,255,255,0.00)"         # 亮色无需内高光
        card_highlight2 = "rgba(255,255,255,0.00)"
        hero_border = t.border

    return f"""
    QWidget {{
        font-family: 'Microsoft YaHei UI','Segoe UI',sans-serif;
        color: {t.text};
        background: transparent;
    }}

    /* =========================
       通用卡片（含暗色高光边）
       ========================= */
    QFrame#Card {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;

        /* ✅ 暗色“内高光”质感（亮色为 0 不影响） */
        padding-top: 1px;
    }}
    QFrame#Card::before {{
        /* Qt Stylesheet 不支持 ::before，这里占位说明 */
    }}

    /* ✅ 用 inset 阴影模拟高光（Qt 支持有限，但多数平台可用） */
    QFrame#Card {{
        /* 上沿轻高光 + 内部轻暗角（让渐变更立体） */
        background: {card_bg};
    }}

    /* 右侧侧边栏底框（背景图由 SidebarBackgroundFrame 绘制） */
    QFrame#RightSidebar {{
        background: transparent;
        border: 1px solid {t.border};
        border-radius: 14px;
    }}

    /* ✅ 右侧内容磨砂层（不盖死背景图） */
    QFrame#SidebarContent {{
        background: {sidebar_overlay};
        border: 1px solid {sidebar_border};
        border-radius: 14px;
    }}

    QStackedWidget {{
        background: transparent;
        border: none;
    }}
    QStackedWidget > QWidget {{
        background: transparent;
    }}

    /* =========================
       视频大卡（暗色也加一点高光边）
       ========================= */
    QFrame#HeroCard {{
        background: {card_bg};
        border: 1px solid {hero_border};
        border-radius: 26px;
    }}
    QLabel#VideoInner {{
        background: {video_inner_bg};
        border-radius: 18px;
    }}

    /* =========================
       标题体系（层级更清晰）
       ========================= */
    QLabel#Title {{
        color: {t.text};
        font-weight: 900;
        font-size: 15px;
        letter-spacing: 0.2px;
    }}
    QLabel#SubTitle {{
        color: {t.subtext};
        font-weight: 650;
        font-size: 12px;
    }}

    /* =========================
       工具栏按钮
       ========================= */
    QPushButton#ToolBtn {{
        background: rgba(255,255,255,0.0);
        border: 1px solid {t.border};
        border-radius: 12px;
        font-size: 22px;
        font-weight: 900;
    }}
    QPushButton#ToolBtn:hover {{
        border-color: {t.primary};
        color: {t.primary};
        background: {toolbtn_hover_bg};
    }}

    /* =========================
       进度条
       ========================= */
    QProgressBar {{
        background: {prog_bg};
        border: 1px solid {t.border};
        border-radius: 9px;
        text-align: center;
        font-weight: 900;
        color: {t.text};
    }}
    QProgressBar::chunk {{
        background: {t.primary};
        border-radius: 8px;
    }}

    /* ✅ 进度条按属性变色 */
    QProgressBar[barLevel="good"]::chunk {{ background: {t.good}; }}
    QProgressBar[barLevel="warn"]::chunk {{ background: {t.warn}; }}
    QProgressBar[barLevel="bad"]::chunk  {{ background: {t.bad};  }}

    /* ✅ 姿态状态文字按属性变色 */
    QLabel#PostureStatus[state="good"] {{ color: {t.good}; }}
    QLabel#PostureStatus[state="bad"]  {{ color: {t.bad};  }}

    /* =========================
       行为块两态
       ========================= */
    QLabel#StateInactive {{
        background: {state_inactive_bg};
        border: 1px solid {t.border};
        border-radius: 10px;
        color: {t.text};
        font-size: 15px;
        font-weight: 900;
    }}
    QLabel#StateActive {{
        background: {t.warn};
        border: 1px solid {t.warn};
        border-radius: 10px;
        color: {state_active_text};
        font-size: 17px;
        font-weight: 1000;
    }}

    /* =========================
       警报框（仍保留原 Type1/Type2）
       ========================= */
    QLabel#AlertType2 {{
        background: {t.bad};
        color: white;
        border-radius: 14px;
        font-size: 32px;
        font-weight: 1000;
        padding: 20px;
    }}
    QLabel#AlertType1 {{
        background: {t.warn};
        color: {alert1_text};
        border-radius: 14px;
        font-size: 20px;
        font-weight: 1000;
        padding: 10px 20px;
    }}

    /* =========================
       ControlsPanel / GroupBox
       ========================= */
    QGroupBox {{
        font-weight: 900;
        border: none;
        border-top: 1px solid {t.border};
        margin-top: 10px;
        padding-top: 10px;
        color: {t.primary};
        font-size: 13px;
        letter-spacing: 0.2px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 0px;
        padding: 0 5px;
    }}

    QCheckBox {{
        font-size: 14px;
        padding: 8px 0;
        border-bottom: 1px dashed rgba(180,180,180,0.22);
    }}
    QCheckBox:hover {{
        background: {checkbox_hover_bg};
        border-radius: 6px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        background: rgba(255,255,255,0.06);
        border: 2px solid {t.border};
        border-radius: 4px;
    }}
    QCheckBox::indicator:hover {{
        border-color: {t.primary};
    }}
    QCheckBox::indicator:checked {{
        background: rgba(255,255,255,0.06);
        border: 2px solid {t.primary};
        /* image 由 controls.py 注入 Base64 */
    }}

    QSlider::groove:horizontal {{
        height: 6px;
        border-radius: 3px;
        background: rgba(255,255,255,0.10);
        border: 1px solid {t.border};
    }}
    QSlider::handle:horizontal {{
        width: 14px;
        margin: -6px 0;
        border-radius: 7px;
        background: {t.primary};
    }}

    /* =========================
       ClockPanel（时钟）
       ========================= */
    QFrame#Container {{
        background: {container_bg};
        border-radius: 12px;
        border: 1px solid {t.border};
    }}

    QLabel#ClockTitle {{
        color: {t.subtext};
        font-size: 12px;
        font-weight: 900;
        letter-spacing: 2px;
    }}
    QLabel#ClockTime {{
        color: {t.text};
        font-size: 42px;
        font-family: 'Consolas';
        font-weight: 1000;
    }}
    QLabel#ClockDate {{
        color: {t.subtext};
        font-size: 13px;
        font-weight: 700;
    }}

    QPushButton#BtnStart {{
        background: rgba(47,163,107,0.16);
        color: {t.good};
        border: 1px solid {t.good};
        border-radius: 16px;
        font-weight: 900;
        font-size: 11px;
    }}
    QPushButton#BtnPause {{
        background: rgba(216,163,74,0.16);
        color: {t.warn};
        border: 1px solid {t.warn};
        border-radius: 16px;
        font-weight: 900;
        font-size: 11px;
    }}
    QPushButton#BtnReset {{
        background: rgba(148,163,184,0.15);
        color: {t.subtext};
        border: 1px solid {t.border};
        border-radius: 16px;
        font-weight: 900;
        font-size: 11px;
    }}

    QPushButton#BtnAlarmToggle {{
        border-radius: 15px;
        font-size: 14px;
        font-weight: 1000;
        border: 1px solid {t.border};
        background: rgba(255,255,255,0.06);
    }}
    QPushButton#BtnAlarmToggle:checked {{
        background: {t.primary};
        color: white;
        border: none;
    }}

    QTimeEdit {{
        border: 1px solid {t.border};
        border-radius: 10px;
        padding: 4px 8px;
        background: rgba(255,255,255,0.10);
        color: {t.text};
        font-weight: 900;
    }}
    QSpinBox {{
        background: transparent;
        border: none;
        font-weight: 1000;
        color: {t.text};
    }}
    QSpinBox::selection {{
        background: transparent;
        color: {t.text};
    }}

    /* 暗色科技感：hover 边框微亮 */
    {"QFrame#Card:hover, QFrame#HeroCard:hover { border-color: %s; }" % t.primary if t.name=="dark" else ""}

    """
