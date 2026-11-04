"""Tema sunset kecil untuk Widgets, tanpa font atau aset eksternal."""

SUNSET = """
QWidget { color: #382F29; font-size: 14px; }
QMainWindow, QDialog { background: #FFF8F0; }
QFrame#sidebar { background: #FFF0DF; border-right: 1px solid #EEDCCA; }
QWidget#mainPanel { background: #FFF8F0; }
QLabel#brand { font-size: 27px; font-weight: 700; color: #422B20; }
QLabel#muted, QLabel#inputHint { color: #79675B; font-size: 12px; }
QLabel#sectionLabel { color: #956145; font-size: 11px; font-weight: 600; }
QLabel#conversationTitle { font-size: 21px; font-weight: 600; }
QLabel#modelName { color: #79675B; font-size: 12px; }
QLabel#localBadge { background: #FFE2BD; color: #754621; border-radius: 10px; padding: 5px 10px; font-size: 11px; }
QLabel#settingsError { background: #FFF0DB; color: #8C341A; border: 1px solid #DFAD7C; border-radius: 8px; padding: 10px; }
QPushButton { background: #FFFCF7; border: 1px solid #DDC6B3; border-radius: 9px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #FFE6CE; border-color: #C97E51; }
QPushButton:pressed { background: #FFD5B4; }
QPushButton:focus { border: 2px solid #B9471B; }
QPushButton:disabled { color: #9F8A7B; background: #F2E8DE; border-color: #E6D8CC; }
QPushButton#sendButton { color: white; background: #B9471B; border-color: #B9471B; min-width: 64px; }
QPushButton#sendButton:hover { background: #9E3914; }
QPushButton#sendButton:disabled { color: #9F8A7B; background: #F2E8DE; border-color: #E6D8CC; }
QPushButton#newConversation { background: #FFE0C6; color: #843B1D; border-color: #E8B896; text-align: left; }
QPushButton#newConversation:hover { background: #FFD1AE; }
QPushButton#renameConversation { background: transparent; border: 1px solid transparent; padding: 4px; font-size: 11px; color: #843B1D; }
QPushButton#renameConversation:hover { background: #FFE0C6; }
QPushButton#renameConversation:focus { border-color: #B9471B; }
QPushButton#renameConversation:disabled { color: #9F8A7B; }
QListWidget { background: transparent; border: none; outline: 0; }
QListWidget::item { padding: 12px 10px; margin-bottom: 6px; border: 1px solid transparent; border-radius: 9px; }
QListWidget::item:hover { background: #FFE6CE; }
QListWidget::item:selected { background: #FFDEC2; color: #663319; border: 1px solid #D99160; }
QListWidget:focus { border: 1px solid #B9471B; border-radius: 9px; }
QFrame#conversationArea { background: #FFFCF8; border: 1px solid #EAD8C7; border-radius: 18px; }
QWidget#welcome { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FFFCF8,stop:1 #FFF0DB); border-radius: 14px; }
QLabel#welcomeTitle { font-size: 28px; font-weight: 600; color: #503021; }
QLabel#welcomeDetail { color: #84634D; font-size: 14px; }
QTextEdit#transcript { background: transparent; border: none; padding: 8px 18px 18px 18px; selection-background-color: #FFD2AF; selection-color: #382F29; }
QFrame#composer { background: #FFFCF8; border: 1px solid #DDC6B3; border-radius: 14px; }
QPlainTextEdit#messageInput { background: transparent; border: none; padding: 0; selection-background-color: #FFD2AF; selection-color: #382F29; }
QPlainTextEdit#messageInput:focus { border-bottom: 2px solid #B9471B; }
QLineEdit, QSpinBox { background: #FFFCF8; border: 1px solid #DDC6B3; border-radius: 6px; padding: 8px; selection-background-color: #FFD2AF; selection-color: #382F29; }
QLineEdit:focus, QSpinBox:focus { border: 2px solid #B9471B; }
QStatusBar { background: #FFF8F0; color: #79675B; font-size: 12px; }
QSplitter::handle { background: #EEDCCA; width: 1px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #D9BDA7; border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""
