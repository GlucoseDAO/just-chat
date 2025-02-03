from pathlib import Path
import re

def read_file(file_path: Path) -> str:
    """Read content from a single file"""
    content = file_path.read_text(encoding='utf-8')
    return content

def about_glucosedao(question: str) -> str:
    """
    Answer questions about GlucoseDAO
    """
    print("question ", question)
    return """
    Leadership Structure
    Core Team
    -Founder: Zaharia Livia (Type 1 diabetic)
    -Founding Members: Anton Kulaga, Brandon Houten
    Scientific Advisory Board
    -Irina Gaianova (University of Michigan, Biostatistics)
    -Prof. Georg Fullen (Rostock University)
    -Renat Sergazinov (GlucoBench author)
    """
