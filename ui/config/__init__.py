"""
UI 配置模組

提供設計系統的統一入口,方便其他模組 import
"""

from .design_system import (
    # 設計 tokens
    colors,
    typography,
    spacing,
    border_radius,
    shadow,
    animation,
    component_sizes,
    
    # 預設樣式
    default_styles,
    
    # 工具函式
    get_font_config,
    get_padding,
)

__all__ = [
    # 設計 tokens
    "colors",
    "typography",
    "spacing",
    "border_radius",
    "shadow",
    "animation",
    "component_sizes",
    
    # 預設樣式
    "default_styles",
    
    # 工具函式
    "get_font_config",
    "get_padding",
]
