"""
設計系統配置
定義整個應用程式的視覺設計 tokens

遵循原則:
- DRY: 單一真實來源,所有顏色、字體、間距統一管理
- SOLID: 單一職責原則,只負責設計 tokens
- KISS: 簡單明瞭的命名和結構
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Colors:
    """
    顏色系統 - 深色科技風主題
    採用柔和灰階背景搭配亮藍主色
    """
    # === 背景色系 ===
    background_primary: str = "#1E1E1E"      # 主背景
    background_secondary: str = "#2C2C2C"    # 次要背景
    background_tertiary: str = "#3A3A3A"     # 三級背景
    background_gradient_start: str = "#1E1E1E"
    background_gradient_end: str = "#2C2C2C"
    
    # === 主色系 ===
    primary: str = "#3A8DFF"                 # 主色 - 亮藍
    primary_hover: str = "#2E7CE6"           # 主色 hover 狀態
    primary_pressed: str = "#266BD9"         # 主色 pressed 狀態
    primary_light: str = "#5AA0FF"           # 主色淺色版
    
    # === 輔助色系 ===
    secondary: str = "#00C2A8"               # 輔助色 - 青綠
    secondary_hover: str = "#00A890"
    
    # === 功能色系 ===
    success: str = "#4CAF50"                 # 成功
    success_hover: str = "#45a049"
    warning: str = "#FF9800"                 # 警告
    error: str = "#e74c3c"                   # 錯誤
    error_hover: str = "#c0392b"
    info: str = "#2196F3"                    # 資訊
    
    # === 文字色系 ===
    text_primary: str = "#FFFFFF"            # 主要文字
    text_secondary: str = "#B3B3B3"          # 次要文字
    text_tertiary: str = "#808080"           # 三級文字
    text_disabled: str = "#666666"           # 禁用文字
    text_link: str = "#3A8DFF"               # 連結文字
    
    # === 邊框色系 ===
    border_light: str = "#404040"            # 淺邊框
    border_medium: str = "#505050"           # 中邊框
    border_dark: str = "#2A2A2A"             # 深邊框
    
    # === 覆蓋層 ===
    overlay: str = "rgba(0, 0, 0, 0.6)"      # 遮罩層
    
    # === 卡片色系 ===
    card_background: str = "#252525"         # 卡片背景
    card_hover: str = "#2D2D2D"              # 卡片 hover
    
    # === 表格色系 ===
    table_header: str = "#2A2A2A"            # 表頭背景
    table_row_even: str = "#252525"          # 偶數行
    table_row_odd: str = "#2C2C2C"           # 奇數行
    table_row_hover: str = "#333333"         # hover 行


@dataclass(frozen=True)
class Typography:
    """
    字體系統
    定義字體家族、大小、粗細
    """
    # === 字體家族 ===
    font_family_primary: str = "Microsoft JhengHei UI"  # 微軟正黑體 UI (適合繁體中文)
    font_family_secondary: str = "Segoe UI"             # 英文備用
    font_family_monospace: str = "Consolas"             # 等寬字體
    
    # === 字體大小 ===
    size_h1: int = 32                        # 主標題
    size_h2: int = 24                        # 副標題
    size_h3: int = 20                        # 三級標題
    size_h4: int = 18                        # 四級標題
    size_body_large: int = 16                # 大正文
    size_body: int = 14                      # 正文
    size_body_small: int = 12                # 小正文
    size_caption: int = 11                   # 說明文字
    
    # === 字重 ===
    # 注意: Tkinter 只支援 "normal" 和 "bold"
    weight_normal: str = "normal"            # 400
    weight_bold: str = "bold"                # 700
    
    # === 行高 ===
    line_height_tight: float = 1.2           # 緊湊
    line_height_normal: float = 1.5          # 正常
    line_height_loose: float = 1.8           # 寬鬆


@dataclass(frozen=True)
class Spacing:
    """
    間距系統
    採用 8px 基準網格
    """
    xs: int = 4                              # 0.5x
    sm: int = 8                              # 1x 基準
    md: int = 16                             # 2x
    lg: int = 24                             # 3x
    xl: int = 32                             # 4x
    xxl: int = 48                            # 6x
    xxxl: int = 64                           # 8x


@dataclass(frozen=True)
class BorderRadius:
    """圓角系統"""
    none: int = 0
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999                         # 完全圓角


@dataclass(frozen=True)
class Shadow:
    """陰影系統"""
    none: str = "none"
    sm: Tuple[str, str] = ("0 2px 4px rgba(0,0,0,0.1)", "0 1px 2px rgba(0,0,0,0.06)")
    md: Tuple[str, str] = ("0 4px 6px rgba(0,0,0,0.1)", "0 2px 4px rgba(0,0,0,0.06)")
    lg: Tuple[str, str] = ("0 10px 15px rgba(0,0,0,0.1)", "0 4px 6px rgba(0,0,0,0.06)")
    xl: Tuple[str, str] = ("0 20px 25px rgba(0,0,0,0.1)", "0 10px 10px rgba(0,0,0,0.04)")


@dataclass(frozen=True)
class Animation:
    """動畫系統"""
    duration_fast: int = 150                 # 快速動畫 (ms)
    duration_normal: int = 300               # 正常動畫 (ms)
    duration_slow: int = 500                 # 慢速動畫 (ms)
    
    # easing 曲線
    easing_default: str = "ease-in-out"
    easing_enter: str = "ease-out"
    easing_exit: str = "ease-in"


@dataclass(frozen=True)
class ComponentSizes:
    """元件尺寸系統"""
    # 按鈕高度
    button_height_sm: int = 32
    button_height_md: int = 40
    button_height_lg: int = 48
    
    # 輸入框高度
    input_height_sm: int = 32
    input_height_md: int = 40
    input_height_lg: int = 48
    
    # 圖示大小
    icon_size_sm: int = 16
    icon_size_md: int = 20
    icon_size_lg: int = 24
    icon_size_xl: int = 32


# === 設計系統實例 ===
# 遵循 DRY 原則,在整個應用程式中使用這些實例
colors = Colors()
typography = Typography()
spacing = Spacing()
border_radius = BorderRadius()
shadow = Shadow()
animation = Animation()
component_sizes = ComponentSizes()


# === 便利函式 ===
def get_font_config(size: int, weight: str = "normal") -> tuple:
    """
    取得字體配置
    
    Args:
        size: 字體大小
        weight: 字體粗細
        
    Returns:
        tuple: CustomTkinter 字體配置 (family, size, weight)
    """
    return (typography.font_family_primary, size, weight)


def get_padding(vertical: int, horizontal: int) -> Tuple[int, int]:
    """
    取得內距配置
    
    Args:
        vertical: 垂直內距
        horizontal: 水平內距
        
    Returns:
        Tuple: (水平, 垂直)
    """
    return (horizontal, vertical)


# === 預設配置 ===
class DefaultStyles:
    """預設樣式配置"""
    
    # 主要按鈕
    PRIMARY_BUTTON = {
        "fg_color": colors.primary,
        "hover_color": colors.primary_hover,
        "text_color": colors.text_primary,
        "corner_radius": border_radius.md,
        "border_width": 0
    }
    
    # 次要按鈕
    SECONDARY_BUTTON = {
        "fg_color": colors.secondary,
        "hover_color": colors.secondary_hover,
        "text_color": colors.text_primary,
        "corner_radius": border_radius.md,
        "border_width": 0
    }
    
    # 錯誤按鈕
    ERROR_BUTTON = {
        "fg_color": colors.error,
        "hover_color": colors.error_hover,
        "text_color": colors.text_primary,
        "corner_radius": border_radius.md,
        "border_width": 0
    }
    
    # 卡片
    CARD = {
        "fg_color": colors.card_background,
        "corner_radius": border_radius.lg,
        "border_width": 1,
        "border_color": colors.border_light
    }
    
    # 輸入框
    INPUT = {
        "fg_color": colors.background_secondary,
        "border_color": colors.border_medium,
        "text_color": colors.text_primary,
        "placeholder_text_color": colors.text_tertiary,
        "corner_radius": border_radius.md,
        "border_width": 1
    }


default_styles = DefaultStyles()
