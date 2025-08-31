"""
链接分类模块
负责识别用户输入中的链接类型，并决定使用哪个解析器
"""

from .link_classifier import LinkClassifier

__all__ = ['LinkClassifier'] 