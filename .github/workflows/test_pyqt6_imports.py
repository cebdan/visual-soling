#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test PyQt6 imports to find the source of QStringListModel error
"""

def test_pyqt6_imports():
    """Test all PyQt6 imports to identify the problem"""
    
    print("Testing PyQt6 imports...")
    
    try:
        print("1. Testing basic QtWidgets...")
        from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                    QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTableWidget, 
                                    QTableWidgetItem, QSplitter, QMenuBar, QFileDialog, 
                                    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, 
                                    QComboBox, QPushButton, QLabel, QTextEdit, QCheckBox,
                                    QListWidget, QMessageBox, QHeaderView, QTabWidget,
                                    QGroupBox, QGridLayout, QScrollArea, QSpinBox, QPlainTextEdit,
                                    QCompleter)
        print("✅ QtWidgets basic imports OK")
    except ImportError as e:
        print(f"❌ QtWidgets basic imports failed: {e}")
        return False
    
    try:
        print("2. Testing QtCore...")
        from PyQt6.QtCore import Qt, pyqtSignal, QTimer
        print("✅ QtCore basic imports OK")
    except ImportError as e:
        print(f"❌ QtCore basic imports failed: {e}")
        return False
    
    try:
        print("3. Testing QStringListModel from QtCore...")
        from PyQt6.QtCore import QStringListModel
        print("✅ QStringListModel from QtCore OK")
    except ImportError as e:
        print(f"❌ QStringListModel from QtCore failed: {e}")
        return False
    
    try:
        print("4. Testing QStringListModel from QtWidgets (this should fail)...")
        from PyQt6.QtWidgets import QStringListModel
        print("⚠️ QStringListModel from QtWidgets unexpectedly succeeded!")
        return False
    except ImportError as e:
        print(f"✅ QStringListModel from QtWidgets correctly failed: {e}")
    
    try:
        print("5. Testing QtGui...")
        from PyQt6.QtGui import QAction, QFont, QColor, QTextCharFormat, QTextCursor, QSyntaxHighlighter
        print("✅ QtGui imports OK")
    except ImportError as e:
        print(f"❌ QtGui imports failed: {e}")
        return False
    
    print("\n✅ All PyQt6 imports are working correctly!")
    print("The problem is likely in the visual_solving_ui_advanced_v2.py file")
    print("Make sure you replaced the file with the corrected version.")
    
    return True

def check_visual_solving_ui_file():
    """Check if visual_solving_ui_advanced_v2.py exists and has correct imports"""
    import os
    
    file_path = "visual_solving_ui_advanced_v2.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found")
        return False
    
    print(f"✅ File {file_path} exists")
    
    # Check imports in the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for wrong import
        if "from PyQt6.QtWidgets import" in content and "QStringListModel" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "from PyQt6.QtWidgets import" in line and "QStringListModel" in line:
                    print(f"❌ Found wrong import on line {i}: {line.strip()}")
                    print("This line should be removed or QStringListModel should be imported from QtCore")
                    return False
        
        # Check for correct import
        if "from PyQt6.QtCore import" in content and "QStringListModel" in content:
            print("✅ Found correct QStringListModel import from QtCore")
            return True
        else:
            print("⚠️ No QStringListModel import found in QtCore")
            return False
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PyQt6 Import Diagnostic Tool")
    print("=" * 60)
    
    if test_pyqt6_imports():
        print("\n" + "=" * 60)
        print("Checking visual_solving_ui_advanced_v2.py file...")
        print("=" * 60)
        check_visual_solving_ui_file()
        
        print("\n" + "=" * 60)
        print("SOLUTION:")
        print("=" * 60)
        print("If the file has wrong imports, replace the content of")
        print("visual_solving_ui_advanced_v2.py with the corrected version")
        print("that imports QStringListModel from PyQt6.QtCore, not PyQt6.QtWidgets")
