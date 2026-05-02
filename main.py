import sys
import os
import math
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QFrame, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QFileDialog, QDialog, QFormLayout, QMessageBox,
    QComboBox, QTextEdit, QDateEdit, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QScrollBar
)
from PySide6.QtGui import (
    QPixmap, QColor, QCursor, QFont, QPainter, QPainterPath,
    QBrush, QPen, QLinearGradient, QRadialGradient, QPolygonF,
    QFontMetrics
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QDate, QSize,
    QRectF, QPointF, QTimer, Property
)

import qtawesome as qta
import database

class Theme:
    DARK = {
        "bg":          "#0D1117",
        "surface":     "#161B22",
        "surface2":    "#21262D",
        "border":      "#30363D",
        "text":        "#FFFFFF",
        "text_muted":  "#8B949E",
        "accent":      "#FFD700",
        "accent_dim":  "rgba(255,215,0,0.12)",
        "blue":        "#58A6FF",
        "green":       "#3FB950",
        "red":         "#FF6B6B",
        "orange":      "#F0883E",
    }
    LIGHT = {
        "bg":          "#F6F8FA",
        "surface":     "#FFFFFF",
        "surface2":    "#EAEEF2",
        "border":      "#D0D7DE",
        "text":        "#1F2328",
        "text_muted":  "#636C76",
        "accent":      "#B8860B",
        "accent_dim":  "rgba(184,134,11,0.12)",
        "blue":        "#0969DA",
        "green":       "#1A7F37",
        "red":         "#CF222E",
        "orange":      "#BC4C00",
    }
    _current = "DARK"

    @classmethod
    def get(cls):
        return cls.DARK if cls._current == "DARK" else cls.LIGHT

    @classmethod
    def toggle(cls):
        cls._current = "LIGHT" if cls._current == "DARK" else "DARK"

    @classmethod
    def is_dark(cls):
        return cls._current == "DARK"


def T(key):
    return Theme.get()[key]

def table_style():
    t = Theme.get()
    return f"""
        QTableWidget {{ background-color: {t['surface']}; color: {t['text']}; gridline-color: {t['border']}; border: none; font-size: 13px; }}
        QHeaderView::section {{ background-color: {t['surface2']}; color: {t['text_muted']}; padding: 10px; border: 1px solid {t['border']}; font-weight: bold; }}
        QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {t['surface2']}; }}
        QTableWidget::item:selected {{ background-color: {t['accent_dim']}; color: {t['accent']}; }}
        QScrollBar:vertical {{ background: {t['bg']}; width: 8px; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 4px; }}
    """

def input_style():
    t = Theme.get()
    return f"background-color: {t['bg']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 8px 12px; font-size: 13px;"

def dialog_style():
    t = Theme.get()
    return f"background-color: {t['surface']}; color: {t['text']};"

def label_style():
    return f"color: {T('text_muted')}; font-size: 13px;"

TABLE_STYLE  = table_style()
INPUT_STYLE  = input_style()
DIALOG_STYLE = dialog_style()
LABEL_STYLE  = label_style()


def make_btn(text, color=None, text_color="black", width=None, height=40, icon=None, icon_color=None):
    if color is None:
        color = T("accent")
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    if icon:
        btn.setIcon(qta.icon(icon, color=icon_color or text_color))
        btn.setIconSize(QSize(16, 16))
    w = f"min-width: {width}px;" if width else ""
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: {color}; color: {text_color};
            border-radius: 8px; font-weight: bold; font-size: 13px;
            padding: 6px 18px; {w} min-height: {height}px; }}
        QPushButton:hover {{ border: 1px solid rgba(255,255,255,0.2); }}
    """)
    return btn


def page_header(title, btn_text=None, btn_callback=None, btn_icon=None):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(title)
    lbl.setStyleSheet(f"color: {T('text')}; font-size: 26px; font-weight: bold;")
    h.addWidget(lbl)
    h.addStretch()
    if btn_text and btn_callback:
        btn = make_btn(btn_text, T("green"), "white", icon=btn_icon, icon_color="white")
        btn.clicked.connect(btn_callback)
        h.addWidget(btn)
    return w

class AvatarWidget(QLabel):
    COLORS = ["#FF6B6B","#FFD700","#58A6FF","#3FB950","#F0883E",
              "#D2A8FF","#79C0FF","#A8D8A8","#FFA07A","#87CEEB"]

    def __init__(self, name="?", size=48, image_path=None):
        super().__init__()
        self.avatar_size = size
        self.setFixedSize(size, size)
        self.set_avatar(name, image_path)

    def set_avatar(self, name="?", image_path=None):
        self.name = name
        self.image_path = image_path
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        s = self.avatar_size
        path = QPainterPath()
        path.addEllipse(QRectF(0, 0, s, s))
        painter.setClipPath(path)

        if self.image_path and os.path.exists(self.image_path):
            pix = QPixmap(self.image_path).scaled(s, s, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, pix)
        else:
            initial = self.name[0].upper() if self.name else "?"
            idx = sum(ord(c) for c in self.name) % len(self.COLORS)
            color = QColor(self.COLORS[idx])
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(0, 0, s, s))
            painter.setPen(QPen(QColor("white")))
            font = QFont("Segoe UI", int(s * 0.36), QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, initial)

        painter.end()

class BarChartWidget(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self._anim_progress = 0.0
        self._hover_index = -1
        self._bar_rects = []
        self.setMinimumHeight(200)
        self.setMouseTracking(True)

        self._animation = QPropertyAnimation(self, b"animationProgress")
        self._animation.setDuration(900)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def animationProgress(self):
        return self._anim_progress

    def setAnimationProgress(self, value):
        self._anim_progress = value
        self.update()

    animationProgress = Property(float, animationProgress, setAnimationProgress)

    def set_data(self, data):
        self.data = data
        self._hover_index = -1
        self._animation.stop()
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        t = Theme.get()

        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 40, 10, 30, 40
        chart_w = w - pad_l - pad_r
        chart_h = h - pad_t - pad_b

        max_val = max((v for _, v, _ in self.data), default=1) or 1
        bar_count = len(self.data)
        bar_gap = 12
        bar_w = (chart_w - bar_gap * (bar_count + 1)) / bar_count

        painter.setPen(QPen(QColor(t['text'])))
        font = QFont("Segoe UI", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(pad_l, 4, chart_w, 22), Qt.AlignLeft, self.title)

        self._bar_rects = []
        for i, (label, value, color) in enumerate(self.data):
            x = pad_l + bar_gap * (i + 1) + bar_w * i
            animated_value = value * self._anim_progress
            bar_h = (animated_value / max_val) * (chart_h - 20)
            y = pad_t + chart_h - bar_h

            c = QColor(color)
            if i == self._hover_index:
                painter.setBrush(QBrush(c.lighter(130)))
            else:
                grad = QLinearGradient(x, y, x, y + bar_h)
                grad.setColorAt(0, c.lighter(120))
                grad.setColorAt(1, c.darker(110))
                painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            path = QPainterPath()
            rect = QRectF(x, y, bar_w, bar_h)
            path.addRoundedRect(rect, 4, 4)
            painter.drawPath(path)

            if i == self._hover_index:
                painter.setPen(QPen(QColor(255, 255, 255, 180), 2))
                painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 6, 6)

            painter.setPen(QPen(QColor(t['text'])))
            font2 = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font2)
            painter.drawText(QRectF(x, y - 18, bar_w, 16), Qt.AlignCenter, str(int(animated_value)))

            font3 = QFont("Segoe UI", 8)
            painter.setFont(font3)
            painter.setPen(QPen(QColor(t['text_muted'])))
            painter.drawText(QRectF(x - 4, pad_t + chart_h + 4, bar_w + 8, 24),
                             Qt.AlignCenter, label)

            self._bar_rects.append(rect)

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, 'position') else event.pos()
        hover_index = -1
        for i, rect in enumerate(self._bar_rects):
            if rect.contains(pos):
                hover_index = i
                break
        if hover_index != self._hover_index:
            self._hover_index = hover_index
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_index = -1
        self.update()
        super().leaveEvent(event)

class DonutChartWidget(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self._anim_progress = 0.0
        self._hover_index = -1
        self._segment_angles = []
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

        self._animation = QPropertyAnimation(self, b"animationProgress")
        self._animation.setDuration(900)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def animationProgress(self):
        return self._anim_progress

    def setAnimationProgress(self, value):
        self._anim_progress = value
        self.update()

    animationProgress = Property(float, animationProgress, setAnimationProgress)

    def set_data(self, data):
        self.data = data
        self._hover_index = -1
        self._animation.stop()
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        t = Theme.get()

        w, h = self.width(), self.height()
        side = min(w, h) - 40
        cx = w // 2
        cy = h // 2
        outer_r = side // 2
        inner_r = int(outer_r * 0.58)

        total = sum(v for _, v, _ in self.data) or 1
        start_angle = -90 * 16
        self._segment_angles = []

        current_start = start_angle
        for i, (label, value, color) in enumerate(self.data):
            span = int((value / total) * 360 * 16 * self._anim_progress)
            segment_rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            painter.drawPie(segment_rect, current_start, span)

            norm_start = current_start % (360 * 16)
            norm_end = (current_start + span) % (360 * 16)
            self._segment_angles.append((norm_start, norm_end, outer_r, inner_r))
            if i == self._hover_index and span > 0:
                highlight_path = QPainterPath()
                rect = QRectF(cx - outer_r - 4, cy - outer_r - 4, (outer_r + 4) * 2, (outer_r + 4) * 2)
                highlight_path.addEllipse(rect)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 120), 3))
                painter.drawPath(highlight_path)

            current_start += span

        painter.setBrush(QBrush(QColor(t['surface'])))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2))

        painter.setPen(QPen(QColor(t['text'])))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(cx - inner_r, cy - 14, inner_r * 2, 28),
                         Qt.AlignCenter, self.title)

        legend_y = cy + outer_r + 8
        legend_x = cx - (len(self.data) * 70) // 2
        for i, (label, value, color) in enumerate(self.data):
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(legend_x, legend_y, 10, 10), 2, 2)
            painter.setPen(QPen(QColor(t['text_muted'])))
            painter.setFont(QFont("Segoe UI", 8))
            text = f"{label} ({value})"
            if i == self._hover_index:
                painter.setPen(QPen(QColor(t['text']), 1))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(QRectF(legend_x + 14, legend_y - 1, 56, 14),
                             Qt.AlignLeft, text)
            legend_x += 80

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, 'position') else event.pos()
        rel_x = pos.x() - self.width() / 2
        rel_y = pos.y() - self.height() / 2
        dist = math.hypot(rel_x, rel_y)
        angle = int((90 - math.degrees(math.atan2(rel_y, rel_x))) * 16) % (360 * 16)

        hover_index = -1
        for i, (start, end, outer_r, inner_r) in enumerate(self._segment_angles):
            if inner_r < dist < outer_r:
                if start <= end:
                    if start <= angle <= end:
                        hover_index = i
                        break
                else:
                    if angle >= start or angle <= end:
                        hover_index = i
                        break
        if hover_index != self._hover_index:
            self._hover_index = hover_index
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_index = -1
        self.update()
        super().leaveEvent(event)

class ThemeToggleBtn(QWidget):
    def __init__(self, on_toggle):
        super().__init__()
        self.on_toggle = on_toggle
        self.setFixedSize(56, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._anim_pos = 1.0 if Theme.is_dark() else 0.0

    def mousePressEvent(self, event):
        Theme.toggle()
        self._anim_pos = 1.0 if Theme.is_dark() else 0.0
        self.update()
        self.on_toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        is_dark = Theme.is_dark()

        track_color = QColor("#30363D") if is_dark else QColor("#D0D7DE")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, 4, 56, 20), 10, 10)

        thumb_x = 32 if is_dark else 4
        thumb_color = QColor("#FFD700") if is_dark else QColor("#636C76")
        painter.setBrush(QBrush(thumb_color))
        painter.drawEllipse(QRectF(thumb_x, 2, 24, 24))

        icon_name = "fa5s.moon" if is_dark else "fa5s.sun"
        icon_color = "#FFD700" if is_dark else "white"
        pix = qta.icon(icon_name, color=icon_color).pixmap(QSize(14, 14))
        painter.drawPixmap(int(thumb_x + 5), 7, pix)
        painter.end()

class PersonDetailDialog(QDialog):
    def __init__(self, parent, person_data, person_type="renter"):
        super().__init__(parent)
        self.person_data = person_data
        self.person_type = person_type
        self.setWindowTitle("Person Details")
        self.setFixedWidth(480)
        self.setStyleSheet(dialog_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        header = QHBoxLayout()
        name = f"{person_data.get('first_name','')} {person_data.get('last_name','')}".strip()
        profile_path = person_data.get('profile_path') or person_data.get('profile_pic_path')
        avatar = AvatarWidget(name, 80, profile_path)
        header.addWidget(avatar)

        info_col = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {T('text')}; font-size: 20px; font-weight: bold;")
        info_col.addWidget(name_lbl)

        if person_type == "renter":
            status = person_data.get('renter_status', '—')
            status_colors = {"Active": T("green"), "Inactive": T("text_muted"), "Blacklisted": T("red")}
            s_color = status_colors.get(status, T("text_muted"))
        else:
            status = person_data.get('role', '—')
            s_color = T("blue")

        status_lbl = QLabel(f"● {status}")
        status_lbl.setStyleSheet(f"color: {s_color}; font-size: 13px; font-weight: bold;")
        info_col.addWidget(status_lbl)
        header.addLayout(info_col)
        header.addStretch()
        layout.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {T('border')}; max-height: 1px;")
        layout.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: transparent;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background: transparent;")
        grid = QGridLayout(scroll_content)
        grid.setSpacing(10)

        if person_type == "renter":
            fields = [
                ("Gender",        person_data.get('gender')),
                ("Occupation",    person_data.get('occupation_type')),
                ("Institution",   person_data.get('institution_employer')),
                ("Contact",       person_data.get('contact_number')),
                ("Email",         person_data.get('email')),
                ("ID Type",       person_data.get('id_type')),
                ("ID Number",     person_data.get('id_number')),
                ("Address",       person_data.get('address')),
                ("Emerg. Name",   person_data.get('emergency_contact_name')),
                ("Emerg. Number", person_data.get('emergency_contact_number')),
            ]
        else:
            fields = [
                ("Username",   person_data.get('username')),
                ("Role",       person_data.get('role')),
                ("Email",      person_data.get('email')),
                ("Contact",    person_data.get('contact_number')),
                ("Joined",     str(person_data.get('created_at', '—'))),
            ]

        row = 0
        for label_text, value in fields:
            if value:
                lbl = QLabel(label_text + ":")
                lbl.setStyleSheet(f"color: {T('text_muted')}; font-size: 12px; font-weight: bold;")
                val = QLabel(str(value))
                val.setStyleSheet(f"color: {T('text')}; font-size: 13px;")
                val.setWordWrap(True)
                grid.addWidget(lbl, row, 0)
                grid.addWidget(val, row, 1)
                row += 1

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        close_btn = make_btn("Close", T("surface2"), T("text"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class RenterSelfProfileDialog(QDialog):
    def __init__(self, parent, name, person_id, person_type="renter"):
        super().__init__(parent)
        self.person_id = person_id
        self.person_type = person_type
        self.chosen_path = None
        self.setWindowTitle(f"Set Your Profile Picture — {name}")
        self.setFixedWidth(380)
        self.setStyleSheet(dialog_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(f"Hello, {name}!")
        title.setStyleSheet(f"color: {T('text')}; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("You can set your profile picture here.\nThis step is optional — you can skip it.")
        sub.setStyleSheet(f"color: {T('text_muted')}; font-size: 13px;")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        layout.addWidget(sub)

        self.avatar_preview = AvatarWidget(name, 100)
        layout.addWidget(self.avatar_preview, alignment=Qt.AlignCenter)

        choose_btn = make_btn("  Choose Photo", T("blue"), "white", icon="fa5s.camera", icon_color="white")
        choose_btn.clicked.connect(self._choose_photo)
        layout.addWidget(choose_btn)

        self.path_label = QLabel("No photo selected")
        self.path_label.setStyleSheet(f"color: {T('text_muted')}; font-size: 11px;")
        self.path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.path_label)

        btns = QHBoxLayout()
        skip_btn = make_btn("Skip", T("surface2"), T("text"))
        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        skip_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btns.addWidget(skip_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Profile Picture", "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self.chosen_path = path
            name_part = os.path.basename(path)[:30]
            self.path_label.setText(f"✓ {name_part}")
            self.avatar_preview.set_avatar(
                self.avatar_preview.name, path
            )
            self.avatar_preview.update()

class StaffDialog(QDialog):
    def __init__(self, parent, staff=None):
        super().__init__(parent)
        self.setWindowTitle("Add Staff" if not staff else "Edit Staff")
        self.setFixedWidth(460)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(ph=""):
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setStyleSheet(input_style())
            return e

        self.full_name = inp("Full Name")
        self.username  = inp("Username")
        self.password  = inp("Password (leave blank to keep)")
        self.password.setEchoMode(QLineEdit.Password)
        self.role = QComboBox()
        self.role.addItems(["Admin", "Staff", "Maintenance", "Security"])
        self.role.setStyleSheet(input_style())
        self.email   = inp("email@example.com")
        self.contact = inp("09XXXXXXXXX")

        layout.addRow("Full Name*:", self.full_name)
        layout.addRow("Username*:",  self.username)
        layout.addRow("Password:",   self.password)
        layout.addRow("Role:",       self.role)
        layout.addRow("Email:",      self.email)
        layout.addRow("Contact:",    self.contact)

        if staff:
            self.full_name.setText(staff.get('full_name', ''))
            self.username.setText(staff.get('username', ''))
            self.role.setCurrentText(staff.get('role', 'Staff'))
            self.email.setText(staff.get('email', '') or '')
            self.contact.setText(staff.get('contact_number', '') or '')

        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        save_btn.clicked.connect(self._validate_and_accept)
        layout.addRow(save_btn)

    def _validate_and_accept(self):
        if not self.full_name.text().strip() or not self.username.text().strip():
            QMessageBox.warning(self, "Missing", "Full name and username are required.")
            return
        self.accept()

    def get_data(self):
        d = dict(
            full_name=self.full_name.text().strip(),
            username=self.username.text().strip(),
            role=self.role.currentText(),
            email=self.email.text().strip() or None,
            contact_number=self.contact.text().strip() or None,
        )
        pw = self.password.text().strip()
        if pw:
            d['password'] = pw
        return d

class WelcomePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.bg_label = QLabel(self)
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, "images", "dorm_bg.png")
        if os.path.exists(image_path):
            self.bg_label.setPixmap(QPixmap(image_path))
            self.bg_label.setScaledContents(True)

        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(0,0,0,115);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(10)

        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setAlignment(Qt.AlignCenter)
        dorm_label = QLabel("Dorm")
        dorm_label.setStyleSheet("color: white; font-size: 115px; font-family: 'Brush Script MT'; background: transparent; margin-right: -10px;")
        norm_label = QLabel("Norm")
        norm_label.setStyleSheet("color: white; font-size: 115px; font-family: 'Segoe UI'; font-weight: bold; background: transparent;")
        title_layout.addWidget(dorm_label)
        title_layout.addWidget(norm_label)

        tagline = QLabel("Making you feel at home away from home")
        tagline.setStyleSheet("color: #DADCE0; font-size: 22px; font-family: 'Segoe UI'; font-weight: 300; background: transparent;")

        self.toggle_btn = QPushButton("◈ VIEW AMENITIES & INCLUSIONS ▼")
        self.toggle_btn.setFixedWidth(300)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #FFD700; border: 1px solid #FFD700; border-radius: 15px; padding: 8px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background: rgba(255,215,0,0.1); }
        """)
        self.toggle_btn.clicked.connect(self.toggle_amenities)

        self.feature_container = QWidget()
        self.feature_container.setVisible(False)
        feature_layout = QGridLayout(self.feature_container)
        feature_layout.setSpacing(12)
        all_features = ["Fiber Wi-Fi"," Utilities"," Security"," Kitchen"," Balcony"," Smart TV"," Dining"," Living Room"]
        row, col = 0, 0
        for feat in all_features:
            pill = QLabel(feat)
            pill.setStyleSheet("background-color: rgba(255,215,0,0.12); color: #FFD700; border: 1px solid rgba(255,215,0,0.4); padding: 8px 15px; border-radius: 18px; font-size: 12px; font-weight: bold;")
            feature_layout.addWidget(pill, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        btn = QPushButton("GET STARTED")
        btn.setFixedSize(320, 60)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #FFD700; color: black; border-radius: 30px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #E6C200; border: 2px solid white; }
        """)
        btn.clicked.connect(lambda: self.controller.parent().fade_to_page(1))

        content_layout.addWidget(title_container, alignment=Qt.AlignCenter)
        content_layout.addWidget(tagline, alignment=Qt.AlignCenter)
        content_layout.addSpacing(40)
        content_layout.addWidget(self.toggle_btn, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.feature_container, alignment=Qt.AlignCenter)
        content_layout.addSpacing(40)
        content_layout.addWidget(btn, alignment=Qt.AlignCenter)
        layout.addWidget(content_wrapper, alignment=Qt.AlignCenter)

    def toggle_amenities(self):
        is_visible = self.feature_container.isVisible()
        self.feature_container.setVisible(not is_visible)
        self.toggle_btn.setText("CLOSE AMENITIES ▲" if not is_visible else "◈ VIEW AMENITIES & INCLUSIONS ▼")

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        self.overlay.resize(self.size())
        super().resizeEvent(event)

class LoginPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.bg_label = QLabel(self)
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, "images", "dorm_bg.png")
        if os.path.exists(image_path):
            self.bg_label.setPixmap(QPixmap(image_path))
            self.bg_label.setScaledContents(True)

        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(0,0,0,165);")

        main_layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back_btn = QPushButton("← BACK")
        back_btn.setStyleSheet("color: #FFD700; background: transparent; font-size: 16px; font-weight: bold; border: none;")
        back_btn.clicked.connect(lambda: self.controller.setCurrentIndex(0))
        header.addWidget(back_btn, alignment=Qt.AlignLeft)
        header.setContentsMargins(20, 20, 20, 0)
        main_layout.addLayout(header)
        main_layout.addStretch()

        self.card = QFrame()
        self.card.setFixedSize(450, 650)
        self.card.setStyleSheet("background-color: #161B22; border-radius: 25px; border: 1px solid #30363D;")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(15)

        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        dorm_mini = QLabel("Dorm")
        dorm_mini.setStyleSheet("color: #FFD700; font-family: 'Brush Script MT'; font-size: 28px; border: none;")
        norm_mini = QLabel("Norm")
        norm_mini.setStyleSheet("color: white; font-family: 'Segoe UI'; font-weight: bold; font-size: 28px; border: none;")
        brand_layout.addWidget(dorm_mini)
        brand_layout.addWidget(norm_mini)
        card_layout.addWidget(brand_container, alignment=Qt.AlignCenter)

        title = QLabel("Welcome Back!")
        title.setStyleSheet("color: white; font-size: 30px; font-weight: bold; border: none;")
        card_layout.addWidget(title, alignment=Qt.AlignCenter)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #FF6B6B; font-size: 12px; border: none; font-weight: bold;")
        self.info_label.setWordWrap(True)
        self.info_label.setVisible(False)
        card_layout.addWidget(self.info_label)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Admin Username")
        self.user_input.setFixedSize(370, 50)
        self.user_input.setStyleSheet(
            "QLineEdit {"
            "background-color: #0D1117; color: white; border: 1px solid #30363D; border-radius: 10px; padding-left: 15px;"
            "}"
            "QLineEdit:focus {"
            "background-color: #0D1117; color: white; border: 1px solid #30363D; outline: none;"
            "}"
            "QLineEdit:hover {"
            "border: 1px solid #4D5762;"
            "}"
        )
        card_layout.addWidget(self.user_input)

        pass_container = QWidget()
        pass_container.setFixedSize(370, 50)
        pass_container.setStyleSheet(
            "background-color: #0D1117; border: 1px solid #30363D; border-radius: 10px;"
        )
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(0)
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedSize(320, 50)
        self.pass_input.setStyleSheet(
            "QLineEdit {"
            "background: transparent; color: white; border: none; border-top-left-radius: 10px; border-bottom-left-radius: 10px; padding-left: 15px;"
            "}"
            "QLineEdit:focus {"
            "background: transparent; color: white; border: none; outline: none;"
            "}"
            "QLineEdit:hover {"
            "background: transparent; border: none;"
            "}"
        )
        self.eye_btn = QPushButton()
        self.eye_btn.setIcon(qta.icon("fa5s.eye", color="#8B949E"))
        self.eye_btn.setIconSize(QSize(18, 18))
        self.eye_btn.setFixedSize(50, 50)
        self.eye_btn.setCheckable(True)
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.setStyleSheet(
            "QPushButton {"
            "background: transparent; color: #8B949E; border: none; border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
            "}"
            "QPushButton:focus {"
            "background: transparent; border: none; outline: none;"
            "}"
        )
        self.eye_btn.clicked.connect(self.toggle_password_visibility)
        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.eye_btn)
        card_layout.addWidget(pass_container)

        login_btn = QPushButton("LOGIN")
        login_btn.setFixedSize(370, 55)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet("background-color: #FFD700; color: black; border-radius: 12px; font-size: 16px; font-weight: bold; margin-top: 10px;")
        login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(login_btn)

        footer_note = QLabel("Don't have an account? Contact Admin.")
        footer_note.setStyleSheet("color: #8B949E; font-size: 12px; border: none; margin-top: 10px;")
        card_layout.addWidget(footer_note, alignment=Qt.AlignCenter)

        main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        main_layout.addStretch()

    def toggle_password_visibility(self):
        if self.eye_btn.isChecked():
            self.pass_input.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setIcon(qta.icon("fa5s.eye-slash", color="#8B949E"))
        else:
            self.pass_input.setEchoMode(QLineEdit.Password)
            self.eye_btn.setIcon(qta.icon("fa5s.eye", color="#8B949E"))

    def handle_login(self):
        user = self.user_input.text().strip()
        pw   = self.pass_input.text().strip()
        if not user or not pw:
            self.info_label.setText("Please enter both username and password.")
            self.info_label.setVisible(True)
            return

        db = database.AdminModule()
        user_data = db.validate_login(user, pw)
        if user_data:
            self.info_label.setVisible(False)
            dashboard = self.controller.parent().dashboard
            dashboard.set_current_user(user_data)
            self.controller.parent().fade_to_page(2)
        else:
            self.info_label.setText("Invalid username or password.")
            self.info_label.setVisible(True)

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        self.overlay.resize(self.size())
        super().resizeEvent(event)

class DashboardPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_user = None
        self._apply_bg()

        self.admin_db       = database.AdminModule()
        self.renter_db      = database.RenterModule()
        self.room_db        = database.RoomModule()
        self.assignment_db  = database.AssignmentModule()
        self.payment_db     = database.PaymentModule()
        self.maintenance_db = database.MaintenanceModule()
        self.utility_db     = database.UtilityModule()
        self.visitor_db     = database.VisitorModule()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self._apply_sidebar()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 40, 20, 20)

        brand_row = QHBoxLayout()
        logo_label = QLabel("DormNorm")
        logo_label.setStyleSheet(f"color: {T('accent')}; font-family: 'Brush Script MT'; font-size: 32px; margin-bottom: 10px;")
        self.theme_toggle = ThemeToggleBtn(self._on_theme_toggle)
        brand_row.addWidget(logo_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        brand_row.addStretch()
        brand_row.addWidget(self.theme_toggle, alignment=Qt.AlignRight | Qt.AlignVCenter)
        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addSpacing(20)

        self.pages_content = QStackedWidget()

        menu_items = [
            ("  Dashboard",    0, "fa5s.home",        "#58A6FF"),
            ("  Renters",      1, "fa5s.users",       "#3FB950"),
            ("  Staff",        2, "fa5s.user-tie",    "#FFD700"),
            ("  Rooms",        3, "fa5s.bed",         "#F0883E"),
            ("  Bills & Pay",  4, "fa5s.credit-card", "#D2A8FF"),
            ("  Activity Logs",5, "fa5s.list-alt",    "#79C0FF"),
            ("  Maintenance",  6, "fa5s.tools",       "#FF6B6B"),
            ("  Visitors",     7, "fa5s.eye",         "#A8D8A8"),
        ]
        self.sidebar_buttons = []
        for text, index, icon_name, icon_color in menu_items:
            btn = QPushButton(text)
            btn.setIcon(qta.icon(icon_name, color=icon_color))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, i=index: self.switch_page(i))
            if index == 0:
                btn.setChecked(True)
            btn.setStyleSheet(self._sidebar_btn_style())
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()
        logout_btn = QPushButton("  Logout")
        logout_btn.setIcon(qta.icon("fa5s.sign-out-alt", color=T("red")))
        logout_btn.setIconSize(QSize(16, 16))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"color: {T('red')}; background: transparent; font-weight: bold; padding: 10px; border: 1px solid {T('red')}; border-radius: 10px;")
        logout_btn.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(logout_btn)

        self.home_page        = self._build_home_page()
        self.renters_page     = self._build_renters_page()
        self.staff_page       = self._build_staff_page()
        self.rooms_page       = self._build_rooms_page()
        self.payments_page    = self._build_payments_page()
        self.logs_page        = self._build_logs_page()
        self.maintenance_page = self._build_maintenance_page()
        self.visitors_page    = self._build_visitors_page()

        for p in [self.home_page, self.renters_page, self.staff_page,
                  self.rooms_page, self.payments_page, self.logs_page,
                  self.maintenance_page, self.visitors_page]:
            self.pages_content.addWidget(p)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages_content)

    def _apply_bg(self):
        self.setStyleSheet(f"background-color: {T('bg')};")

    def _apply_sidebar(self):
        self.sidebar.setStyleSheet(f"background-color: {T('surface')}; border-right: 1px solid {T('border')};")

    def _on_theme_toggle(self):
        self._rebuild_styles()

    def _rebuild_styles(self):
        self._apply_bg()
        self._apply_sidebar()
        for btn in self.sidebar_buttons:
            btn.setStyleSheet(self._sidebar_btn_style())

        self.refresh_home_stats()
        for table in [self.renters_table, self.rooms_table,
                      self.payments_table, self.logs_table,
                      self.maintenance_table, self.visitors_table,
                      self.recent_logs_table, self.staff_table]:
            table.setStyleSheet(table_style())
        self.renter_chart.update()
        self.room_chart.update()
        self.payment_donut.update()
        self.renter_faces_area.update()

    def _sidebar_btn_style(self):
        t = Theme.get()
        return f"""
            QPushButton {{ text-align: left; padding: 12px 15px; font-size: 14px; font-weight: bold;
                border-radius: 5px; color: {t['text_muted']}; border: none; background: transparent; }}
            QPushButton:hover {{ background-color: {t['surface2']}; color: {t['text']}; }}
            QPushButton:checked {{ background-color: {t['accent_dim']}; color: {t['accent']}; border-left: 3px solid {t['accent']}; }}
        """

    def set_current_user(self, user_data):
        self.current_user = user_data
        self.welcome_label.setText(f'Hello, <span style="color:{T("accent")};">{user_data["full_name"]}</span>!')
        self.refresh_home_stats()

    def switch_page(self, index):
        self.pages_content.setCurrentIndex(index)
        refresh_map = {
            0: self.refresh_home_stats,
            1: self.load_renters,
            2: self.load_staff,
            3: self.load_rooms,
            4: self.load_payments,
            5: self.load_logs,
            6: self.load_maintenance,
            7: self.load_visitors,
        }
        if index in refresh_map:
            refresh_map[index]()

    def handle_logout(self):
        if self.current_user:
            self.admin_db.add_log(self.current_user['admin_id'], 'LOGOUT',
                                  f"{self.current_user['full_name']} logged out.")
        self.current_user = None
        self.controller.parent().fade_to_page(1)

    def _make_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(table_style())
        table.setAlternatingRowColors(True)
        return table

    def _set_table_row(self, table, row, values):
        table.insertRow(row)
        for col, val in enumerate(values):
            item = QTableWidgetItem(str(val) if val is not None else "—")
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            table.setItem(row, col, item)

    def _card_frame(self):
        f = QFrame()
        f.setStyleSheet(f"background-color: {T('surface')}; border-radius: 16px; border: 1px solid {T('border')};")
        return f

    def _build_home_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        header = QHBoxLayout()
        self.welcome_label = QLabel(f'Hello, <span style="color:{T("accent")};">Admin</span>!')
        self.welcome_label.setStyleSheet(f"color: {T('text')}; font-size: 28px; font-weight: bold;")
        date_lbl = QLabel(QDate.currentDate().toString("dddd, MMMM d, yyyy"))
        date_lbl.setStyleSheet(f"color: {T('text_muted')}; font-size: 14px;")
        header.addWidget(self.welcome_label)
        header.addStretch()
        header.addWidget(date_lbl)
        layout.addLayout(header)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        self.stat_boarders = self._stat_card("Current Boarders", "—", T("accent"))
        self.stat_vacant   = self._stat_card("Vacant Rooms",     "—", T("blue"))
        self.stat_maint    = self._stat_card("Maintenance",      "—", T("red"))
        self.stat_payments = self._stat_card("Pending Payments", "—", T("green"))
        self.stat_staff    = self._stat_card("Total Staff",      "—", T("orange"))
        for card in [self.stat_boarders, self.stat_vacant, self.stat_maint,
                     self.stat_payments, self.stat_staff]:
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        renter_card = self._card_frame()
        renter_card.setMinimumHeight(260)
        rc_layout = QVBoxLayout(renter_card)
        rc_layout.setContentsMargins(16, 16, 16, 16)
        self.renter_chart = BarChartWidget("Renters by Occupation")
        rc_layout.addWidget(self.renter_chart)
        charts_row.addWidget(renter_card, 2)

        room_card = self._card_frame()
        room_card.setMinimumHeight(260)
        room_layout = QVBoxLayout(room_card)
        room_layout.setContentsMargins(16, 16, 16, 16)
        self.room_chart = DonutChartWidget("Rooms")
        room_layout.addWidget(self.room_chart)
        charts_row.addWidget(room_card, 1)

        pay_card = self._card_frame()
        pay_card.setMinimumHeight(260)
        pay_layout = QVBoxLayout(pay_card)
        pay_layout.setContentsMargins(16, 16, 16, 16)
        self.payment_donut = DonutChartWidget("Payments")
        pay_layout.addWidget(self.payment_donut)
        charts_row.addWidget(pay_card, 1)

        layout.addLayout(charts_row)

        faces_card = self._card_frame()
        faces_layout = QVBoxLayout(faces_card)
        faces_layout.setContentsMargins(16, 14, 16, 14)
        faces_title = QLabel("Active Renters")
        faces_title.setStyleSheet(f"color: {T('text')}; font-size: 15px; font-weight: bold; border: none; background: transparent;")
        faces_layout.addWidget(faces_title)

        self.renter_faces_area = QScrollArea()
        self.renter_faces_area.setFixedHeight(88)
        self.renter_faces_area.setWidgetResizable(True)
        self.renter_faces_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.renter_faces_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.renter_faces_area.setStyleSheet("border: none; background: transparent;")
        self.renter_faces_inner = QWidget()
        self.renter_faces_inner.setStyleSheet("background: transparent;")
        self.renter_faces_row = QHBoxLayout(self.renter_faces_inner)
        self.renter_faces_row.setContentsMargins(0, 4, 0, 4)
        self.renter_faces_row.setSpacing(10)
        self.renter_faces_row.addStretch()
        self.renter_faces_area.setWidget(self.renter_faces_inner)
        faces_layout.addWidget(self.renter_faces_area)
        layout.addWidget(faces_card)

        recent_lbl = QLabel("Recent Activity")
        recent_lbl.setStyleSheet(f"color: {T('text')}; font-size: 18px; font-weight: bold;")
        layout.addWidget(recent_lbl)
        self.recent_logs_table = self._make_table(["Admin", "Action", "Details", "Timestamp"])
        self.recent_logs_table.setMaximumHeight(220)
        layout.addWidget(self.recent_logs_table)
        layout.addStretch()

        scroll.setWidget(page)
        return scroll

    def _stat_card(self, title, value, color):
        card = QFrame()
        card.setMinimumSize(160, 110)
        card.setFrameShape(QFrame.NoFrame)
        card.setFrameShadow(QFrame.Plain)
        card.setStyleSheet(f"background-color: {T('surface')}; border-radius: 16px; border: none;")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 14, 18, 14)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {T('text_muted')}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 34px; font-weight: bold; border: none; background: transparent;")
        v_lbl.setObjectName("value")
        l.addWidget(t_lbl)
        l.addWidget(v_lbl)
        return card

    def _update_stat_card(self, card, value):
        card.findChild(QLabel, "value").setText(str(value))

    def refresh_home_stats(self):
        t = Theme.get()
        stats = self.renter_db.get_stats()
        renters_count = 0
        if stats:
            renters_count = stats.get("renters", 0)
            self._update_stat_card(self.stat_boarders, stats.get("renters", "—"))
            self._update_stat_card(self.stat_vacant,   stats.get("vacant", "—"))

        maint_count = 0
        pay_count = 0
        paid_count = 0
        overdue_count = 0

        try:
            conn = self.maintenance_db.connect()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE status='Pending'")
                maint_count = cursor.fetchone()['c']
                self._update_stat_card(self.stat_maint, maint_count)

                cursor.execute("SELECT COUNT(*) AS c FROM payments WHERE status='Pending'")
                pay_count = cursor.fetchone()['c']
                cursor.execute("SELECT COUNT(*) AS c FROM payments WHERE status='Paid'")
                paid_count = cursor.fetchone()['c']
                cursor.execute("SELECT COUNT(*) AS c FROM payments WHERE status='Overdue'")
                overdue_count = cursor.fetchone()['c']
                self._update_stat_card(self.stat_payments, pay_count)

                # Staff count
                cursor.execute("SELECT COUNT(*) AS c FROM admins")
                staff_count = cursor.fetchone()['c']
                self._update_stat_card(self.stat_staff, staff_count)
                conn.close()
        except Exception:
            pass

        try:
            conn2 = self.renter_db.connect() if hasattr(self.renter_db, 'connect') else None
            occ_data = []
            if conn2:
                cur = conn2.cursor(dictionary=True)
                cur.execute("SELECT occupation_type, COUNT(*) AS c FROM renters WHERE renter_status='Active' GROUP BY occupation_type")
                rows = cur.fetchall()
                colors = [t['accent'], t['blue'], t['green'], t['orange'], t['red']]
                occ_data = [(r['occupation_type'], r['c'], colors[i % len(colors)]) for i, r in enumerate(rows)]
                conn2.close()
            if not occ_data:
                occ_data = [("Student", renters_count, t['accent'])]
            self.renter_chart.set_data(occ_data)
        except Exception:
            pass

        try:
            rooms = self.room_db.get_all_rooms()
            available = sum(1 for r in rooms if r.get('status') == 'Available')
            full = sum(1 for r in rooms if r.get('status') == 'Full')
            maint_r = sum(1 for r in rooms if r.get('status') == 'Under Maintenance')
            room_data = []
            if available: room_data.append(("Available", available, t['green']))
            if full:      room_data.append(("Full", full, t['red']))
            if maint_r:   room_data.append(("Maint.", maint_r, t['orange']))
            if not room_data: room_data = [("No Rooms", 1, t['border'])]
            self.room_chart.set_data(room_data)
        except Exception:
            pass

        pay_donut_data = []
        if paid_count:    pay_donut_data.append(("Paid", paid_count, t['green']))
        if pay_count:     pay_donut_data.append(("Pending", pay_count, t['accent']))
        if overdue_count: pay_donut_data.append(("Overdue", overdue_count, t['red']))
        if not pay_donut_data: pay_donut_data = [("No Data", 1, t['border'])]
        self.payment_donut.set_data(pay_donut_data)

        try:
            logs = self.admin_db.get_activity_logs() or []
        except Exception:
            logs = []

        self.recent_logs_table.setRowCount(0)
        if not logs:
            self._set_table_row(self.recent_logs_table, 0, [
                "No recent activity yet", "", "", ""
            ])
        else:
            for i, log in enumerate(logs[:8]):
                self._set_table_row(self.recent_logs_table, i, [
                    log['admin_name'], log['action_type'],
                    log['action_text'], str(log['log_timestamp'])
                ])

        self._refresh_renter_faces()

    def _refresh_renter_faces(self):
        while self.renter_faces_row.count() > 1:
            item = self.renter_faces_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            renters = self.renter_db.get_all_renters()
            active = [r for r in renters if r.get('renter_status') == 'Active']
            for r in active[:30]:
                name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
                profile_path = r.get('profile_path') or r.get('profile_pic_path')
                col = QVBoxLayout()
                col.setSpacing(2)
                col.setAlignment(Qt.AlignCenter)
                av = AvatarWidget(name, 48, profile_path)
                av.setCursor(Qt.PointingHandCursor)
                av.setToolTip(name)
                renter_copy = dict(r)
                av.mousePressEvent = lambda ev, rd=renter_copy: self._show_renter_detail(rd)
                short_name = name.split()[0] if name else "?"
                nm_lbl = QLabel(short_name)
                nm_lbl.setStyleSheet(f"color: {T('text_muted')}; font-size: 9px;")
                nm_lbl.setAlignment(Qt.AlignCenter)
                wrapper = QWidget()
                wrapper.setStyleSheet("background: transparent;")
                wl = QVBoxLayout(wrapper)
                wl.setContentsMargins(0, 0, 0, 0)
                wl.setSpacing(2)
                wl.addWidget(av, alignment=Qt.AlignCenter)
                wl.addWidget(nm_lbl, alignment=Qt.AlignCenter)
                self.renter_faces_row.insertWidget(self.renter_faces_row.count() - 1, wrapper)
        except Exception:
            pass

    def _show_renter_detail(self, renter_data):
        dlg = PersonDetailDialog(self, renter_data, "renter")
        dlg.exec()

    def _show_staff_detail(self, staff_data):
        dlg = PersonDetailDialog(self, staff_data, "staff")
        dlg.exec()

    def _build_renters_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)

        layout.addWidget(page_header("Renter Management", "  Register Renter", self.open_add_renter_dialog, btn_icon="fa5s.user-plus"))
        layout.addSpacing(10)

        search_row = QHBoxLayout()
        self.renter_search = QLineEdit()
        self.renter_search.setPlaceholderText("⌕  Search by name, contact, or email…")
        self.renter_search.setStyleSheet(input_style() + "min-height:38px;")
        self.renter_search.textChanged.connect(self.search_renters)
        search_row.addWidget(self.renter_search)
        layout.addLayout(search_row)
        layout.addSpacing(10)

        self.renters_table = self._make_table(
            ["ID", "Avatar", "Full Name", "Gender", "Occupation", "Contact", "Email", "Status"]
        )
        self.renters_table.setColumnWidth(1, 56)
        self.renters_table.setRowHeight(0, 52)
        self.renters_table.clicked.connect(self._on_renter_row_clicked)
        layout.addWidget(self.renters_table)

        btn_row = QHBoxLayout()
        view_btn   = make_btn("  View",    T("blue"),   "white", icon="fa5s.eye",        icon_color="white")
        edit_btn   = make_btn("  Edit",    T("blue"),   "white", icon="fa5s.edit",       icon_color="white")
        delete_btn = make_btn("  Delete",  T("red"),    "white", icon="fa5s.trash-alt",  icon_color="white")
        pic_btn    = make_btn("  Set Pic", T("orange"), "white", icon="fa5s.camera",     icon_color="white")
        view_btn.clicked.connect(self._view_renter)
        edit_btn.clicked.connect(self.open_edit_renter_dialog)
        delete_btn.clicked.connect(self.delete_renter)
        pic_btn.clicked.connect(self._renter_set_pic)
        btn_row.addStretch()
        btn_row.addWidget(view_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(pic_btn)
        layout.addLayout(btn_row)
        return page

    def load_renters(self, rows=None):
        if rows is None:
            rows = self.renter_db.get_all_renters()
        self.renters_table.setRowCount(0)
        for i, r in enumerate(rows):
            self.renters_table.insertRow(i)
            self.renters_table.setRowHeight(i, 52)
            name = f"{r['first_name']} {r.get('middle_name','')} {r['last_name']}".strip()
            profile_path = r.get('profile_path') or r.get('profile_pic_path')
            av = AvatarWidget(name, 40, profile_path)
            self.renters_table.setCellWidget(i, 1, av)
            vals = [r['renter_id'], None, name, r['gender'], r['occupation_type'],
                    r['contact_number'], r['email'], r['renter_status']]
            for col, val in enumerate(vals):
                if col == 1:
                    continue
                item = QTableWidgetItem(str(val) if val is not None else "—")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.renters_table.setItem(i, col, item)

    def _on_renter_row_clicked(self, index):
        pass 

    def _view_renter(self):
        row = self.renters_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a renter.")
            return
        renter_id = int(self.renters_table.item(row, 0).text())
        renter = self.renter_db.get_renter_by_id(renter_id)
        if renter:
            self._show_renter_detail(renter)

    def _renter_set_pic(self):
        row = self.renters_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a renter.")
            return
        renter_id = int(self.renters_table.item(row, 0).text())
        renter = self.renter_db.get_renter_by_id(renter_id)
        if not renter:
            return
        name = f"{renter.get('first_name','')} {renter.get('last_name','')}".strip()
        dlg = RenterSelfProfileDialog(self, name, renter_id, "renter")
        if dlg.exec() and dlg.chosen_path:
            try:
                conn = self.renter_db.connect()
                cur = conn.cursor()
                cur.execute("UPDATE renters SET profile_path=%s WHERE renter_id=%s",
                            (dlg.chosen_path, renter_id))
                conn.commit()
                conn.close()
            except Exception:
                pass
            QMessageBox.information(self, "Profile Updated", f"{name}'s profile picture has been set!")
            self.load_renters()
            self.refresh_home_stats()

    def search_renters(self):
        kw = self.renter_search.text().strip()
        rows = self.renter_db.search_renters(kw) if kw else self.renter_db.get_all_renters()
        self.load_renters(rows)

    def open_add_renter_dialog(self):
        dlg = RenterDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            result = self.renter_db.add_renter(**data)
            if result:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'ADD_RENTER',
                                          f"Added renter: {data['first_name']} {data['last_name']}")

                name = f"{data['first_name']} {data['last_name']}"
                reply = QMessageBox.question(self, "Set Profile Picture",
                    f"Would you like to set a profile picture for {name}?\n(They can do this themselves, or you can do it now.)",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    new_renter = self.renter_db.get_all_renters()[-1] if self.renter_db.get_all_renters() else {}
                    rid = new_renter.get('renter_id', 0)
                    spd = RenterSelfProfileDialog(self, name, rid, "renter")
                    if spd.exec() and spd.chosen_path:
                        try:
                            conn = self.renter_db.connect()
                            cur = conn.cursor()
                            cur.execute("UPDATE renters SET profile_path=%s WHERE renter_id=%s",
                                        (spd.chosen_path, rid))
                            conn.commit()
                            conn.close()
                        except Exception:
                            pass
                QMessageBox.information(self, "Success", "Renter registered successfully!")
                self.load_renters()
            else:
                QMessageBox.critical(self, "Error", "Failed to register renter.")

    def open_edit_renter_dialog(self):
        row = self.renters_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a renter.")
            return
        renter_id = int(self.renters_table.item(row, 0).text())
        renter = self.renter_db.get_renter_by_id(renter_id)
        if not renter:
            return
        dlg = RenterDialog(self, renter)
        if dlg.exec():
            data = dlg.get_data()
            ok = self.renter_db.update_renter(renter_id, **data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'EDIT_RENTER',
                                          f"Edited renter ID {renter_id}")
                QMessageBox.information(self, "Success", "Renter updated!")
                self.load_renters()
            else:
                QMessageBox.critical(self, "Error", "Update failed.")

    def delete_renter(self):
        row = self.renters_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a renter.")
            return
        renter_id = int(self.renters_table.item(row, 0).text())
        name = self.renters_table.item(row, 2).text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete renter '{name}'?\nThis cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.renter_db.delete_renter(renter_id)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'DELETE_RENTER',
                                          f"Deleted renter: {name}")
                self.load_renters()
            else:
                QMessageBox.critical(self, "Error", "Delete failed.")

    def _build_staff_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Staff Management", "  Add Staff", self.open_add_staff_dialog, btn_icon="fa5s.user-plus"))
        layout.addSpacing(10)

        self.staff_table = self._make_table(
            ["ID", "Avatar", "Full Name", "Username", "Role", "Email", "Contact"]
        )
        self.staff_table.setColumnWidth(1, 56)
        layout.addWidget(self.staff_table)

        btn_row = QHBoxLayout()
        view_btn   = make_btn("  View",    T("blue"),   "white", icon="fa5s.eye",       icon_color="white")
        edit_btn   = make_btn("  Edit",    T("blue"),   "white", icon="fa5s.edit",      icon_color="white")
        delete_btn = make_btn("  Delete",  T("red"),    "white", icon="fa5s.trash-alt", icon_color="white")
        pic_btn    = make_btn("  Set Pic", T("orange"), "white", icon="fa5s.camera",    icon_color="white")
        view_btn.clicked.connect(self._view_staff)
        edit_btn.clicked.connect(self.open_edit_staff_dialog)
        delete_btn.clicked.connect(self.delete_staff)
        pic_btn.clicked.connect(self._staff_set_pic)
        btn_row.addStretch()
        btn_row.addWidget(view_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(pic_btn)
        layout.addLayout(btn_row)
        return page

    def load_staff(self):
        try:
            admins = self.admin_db.get_all_admins() if hasattr(self.admin_db, 'get_all_admins') else []
        except Exception:
            admins = []
        self.staff_table.setRowCount(0)
        for i, a in enumerate(admins):
            self.staff_table.insertRow(i)
            self.staff_table.setRowHeight(i, 52)
            name = a.get('full_name', '—')
            profile_path = a.get('profile_pic_path') or a.get('profile_path')
            av = AvatarWidget(name, 40, profile_path)
            self.staff_table.setCellWidget(i, 1, av)
            vals = [a.get('admin_id', i), None, name, a.get('username', '—'),
                    a.get('role', '—'), a.get('email', '—'), a.get('contact_number', '—')]
            for col, val in enumerate(vals):
                if col == 1:
                    continue
                item = QTableWidgetItem(str(val) if val is not None else "—")
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.staff_table.setItem(i, col, item)

    def _view_staff(self):
        row = self.staff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a staff member.")
            return
        try:
            admins = self.admin_db.get_all_admins()
            staff = admins[row] if row < len(admins) else None
            if staff:
                self._show_staff_detail(staff)
        except Exception:
            pass

    def _staff_set_pic(self):
        row = self.staff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a staff member.")
            return
        try:
            staff_id = int(self.staff_table.item(row, 0).text())
            name = self.staff_table.item(row, 2).text()
            dlg = RenterSelfProfileDialog(self, name, staff_id, "staff")
            if dlg.exec() and dlg.chosen_path:
                try:
                    conn = self.admin_db.connect()
                    cur = conn.cursor()
                    cur.execute("UPDATE admins SET profile_pic_path=%s WHERE admin_id=%s",
                                (dlg.chosen_path, staff_id))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                QMessageBox.information(self, "Profile Updated", f"{name}'s profile picture has been set!")
                self.load_staff()
        except Exception:
            pass

    def open_add_staff_dialog(self):
        dlg = StaffDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                conn = self.admin_db.connect()
                cur = conn.cursor()
                pw = data.pop('password', 'changeme123')
                import hashlib
                hashed = hashlib.sha256(pw.encode()).hexdigest()
                cur.execute("""INSERT INTO admins (full_name, username, password, role, email, contact_number)
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            (data['full_name'], data['username'], hashed,
                             data.get('role','Staff'), data.get('email'), data.get('contact_number')))
                conn.commit()
                conn.close()
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'ADD_STAFF',
                                          f"Added staff: {data['full_name']}")
                QMessageBox.information(self, "Success", "Staff added!")
                self.load_staff()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add staff: {e}")

    def open_edit_staff_dialog(self):
        row = self.staff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a staff member.")
            return
        try:
            staff_id = int(self.staff_table.item(row, 0).text())
            admins = self.admin_db.get_all_admins()
            staff = next((a for a in admins if a.get('admin_id') == staff_id), None)
            if not staff:
                return
            dlg = StaffDialog(self, staff)
            if dlg.exec():
                data = dlg.get_data()
                try:
                    conn = self.admin_db.connect()
                    cur = conn.cursor()
                    if 'password' in data:
                        import hashlib
                        hashed = hashlib.sha256(data.pop('password').encode()).hexdigest()
                        cur.execute("UPDATE admins SET password=%s WHERE admin_id=%s", (hashed, staff_id))
                    cur.execute("""UPDATE admins SET full_name=%s, username=%s, role=%s, email=%s, contact_number=%s
                                   WHERE admin_id=%s""",
                                (data['full_name'], data['username'], data.get('role','Staff'),
                                 data.get('email'), data.get('contact_number'), staff_id))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Success", "Staff updated!")
                    self.load_staff()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Update failed: {e}")
        except Exception:
            pass

    def delete_staff(self):
        row = self.staff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a staff member.")
            return
        staff_id = int(self.staff_table.item(row, 0).text())
        name = self.staff_table.item(row, 2).text()
        if self.current_user and self.current_user.get('admin_id') == staff_id:
            QMessageBox.warning(self, "Cannot Delete", "You cannot delete your own account.")
            return
        reply = QMessageBox.question(self, "Confirm", f"Delete staff '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = self.admin_db.connect()
                cur = conn.cursor()
                cur.execute("DELETE FROM admins WHERE admin_id=%s", (staff_id,))
                conn.commit()
                conn.close()
                self.load_staff()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {e}")

    def _build_rooms_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Room Management", "  Add Room", self.open_add_room_dialog, btn_icon="fa5s.plus"))
        layout.addSpacing(10)

        self.rooms_table = self._make_table(
            ["ID", "Room No.", "Floor", "Rate (₱)", "Capacity", "Occupied", "Status", "Description"]
        )
        self.rooms_table.doubleClicked.connect(self.open_edit_room_dialog)
        layout.addWidget(self.rooms_table)

        btn_row = QHBoxLayout()
        edit_btn   = make_btn("  Edit",   T("blue"), "white", icon="fa5s.edit",      icon_color="white")
        delete_btn = make_btn("  Delete", T("red"),  "white", icon="fa5s.trash-alt", icon_color="white")
        edit_btn.clicked.connect(self.open_edit_room_dialog)
        delete_btn.clicked.connect(self.delete_room)
        btn_row.addStretch()
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)
        return page

    def load_rooms(self):
        rooms = self.room_db.get_all_rooms()
        self.rooms_table.setRowCount(0)
        for i, r in enumerate(rooms):
            self._set_table_row(self.rooms_table, i, [
                r['room_id'], r['room_number'], r['floor_level'],
                f"₱{r['monthly_rate']:,.2f}", r['capacity'],
                r['occupied'], r['status'], r['description']
            ])

    def open_add_room_dialog(self):
        dlg = RoomDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            ok = self.room_db.add_room(**data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'ADD_ROOM',
                                          f"Added room {data['room_number']}")
                QMessageBox.information(self, "Success", "Room added!")
                self.load_rooms()
            else:
                QMessageBox.critical(self, "Error", "Failed to add room.")

    def open_edit_room_dialog(self):
        row = self.rooms_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a room.")
            return
        room_id = int(self.rooms_table.item(row, 0).text())
        room = self.room_db.get_room_by_id(room_id)
        if not room:
            return
        dlg = RoomDialog(self, room)
        if dlg.exec():
            data = dlg.get_data()
            ok = self.room_db.update_room(room_id, **data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'EDIT_ROOM',
                                          f"Edited room ID {room_id}")
                QMessageBox.information(self, "Success", "Room updated!")
                self.load_rooms()
            else:
                QMessageBox.critical(self, "Error", "Update failed.")

    def delete_room(self):
        row = self.rooms_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a room.")
            return
        room_id = int(self.rooms_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm", f"Delete room ID {room_id}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.room_db.delete_room(room_id)
            if ok:
                self.load_rooms()
            else:
                QMessageBox.critical(self, "Error", "Delete failed.")

    def _build_payments_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Bills & Payments", "  Add Payment", self.open_add_payment_dialog, btn_icon="fa5s.plus"))
        layout.addSpacing(10)

        self.payments_table = self._make_table(
            ["ID", "Invoice", "Renter", "Amount", "Balance", "Method", "Billing Month", "Date", "Status"]
        )
        layout.addWidget(self.payments_table)

        btn_row = QHBoxLayout()
        status_btn = make_btn("  Mark Paid", T("green"), "white", icon="fa5s.check-circle", icon_color="white")
        delete_btn = make_btn("  Delete",   T("red"),   "white", icon="fa5s.trash-alt",    icon_color="white")
        status_btn.clicked.connect(self.mark_payment_paid)
        delete_btn.clicked.connect(self.delete_payment)
        btn_row.addStretch()
        btn_row.addWidget(status_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)
        return page

    def load_payments(self):
        payments = self.payment_db.get_all_payments()
        self.payments_table.setRowCount(0)
        for i, p in enumerate(payments):
            self._set_table_row(self.payments_table, i, [
                p['payment_id'], p['invoice_number'], p['renter_name'],
                f"₱{p['amount']:,.2f}", f"₱{p['balance_amount']:,.2f}",
                p['payment_method'], p['billing_month'],
                str(p['payment_date']), p['status']
            ])
            t = Theme.get()
            status_colors = {"Paid": t['green'], "Pending": t['accent'],
                             "Overdue": t['red'], "Partial": t['orange']}
            color = status_colors.get(p['status'], t['text'])
            self.payments_table.item(i, 8).setForeground(QColor(color))

    def open_add_payment_dialog(self):
        renters = self.renter_db.get_all_renters()
        dlg = PaymentDialog(self, renters)
        if dlg.exec():
            data = dlg.get_data()
            if self.current_user:
                data['processed_by'] = self.current_user['admin_id']
            ok = self.payment_db.add_payment(**data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'ADD_PAYMENT',
                                          f"Added payment {data['invoice_number']}")
                QMessageBox.information(self, "Success", "Payment recorded!")
                self.load_payments()
            else:
                QMessageBox.critical(self, "Error", "Failed to add payment.")

    def mark_payment_paid(self):
        row = self.payments_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a payment.")
            return
        payment_id = int(self.payments_table.item(row, 0).text())
        ok = self.payment_db.update_payment_status(payment_id, "Paid")
        if ok:
            self.load_payments()

    def delete_payment(self):
        row = self.payments_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a payment.")
            return
        payment_id = int(self.payments_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this payment record?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.payment_db.delete_payment(payment_id)
            if ok:
                self.load_payments()

    def _build_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Activity Logs"))
        layout.addSpacing(10)
        self.logs_table = self._make_table(["Log ID", "Admin", "Action", "Details", "Timestamp"])
        layout.addWidget(self.logs_table)
        return page

    def load_logs(self):
        logs = self.admin_db.get_activity_logs()
        self.logs_table.setRowCount(0)
        for i, log in enumerate(logs):
            self._set_table_row(self.logs_table, i, [
                log['log_id'], log['admin_name'],
                log['action_type'], log['action_text'],
                str(log['log_timestamp'])
            ])

    def _build_maintenance_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Maintenance Requests", "  Add Request", self.open_add_maintenance_dialog, btn_icon="fa5s.plus"))
        layout.addSpacing(10)

        self.maintenance_table = self._make_table(
            ["ID", "Room", "Renter", "Issue", "Priority", "Status", "Date Requested"]
        )
        layout.addWidget(self.maintenance_table)

        btn_row = QHBoxLayout()
        resolve_btn = make_btn("  Mark Resolved", T("green"), "white", icon="fa5s.check-circle", icon_color="white")
        delete_btn  = make_btn("  Delete",        T("red"),   "white", icon="fa5s.trash-alt",    icon_color="white")
        resolve_btn.clicked.connect(self.resolve_maintenance)
        delete_btn.clicked.connect(self.delete_maintenance)
        btn_row.addStretch()
        btn_row.addWidget(resolve_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)
        return page

    def load_maintenance(self):
        requests = self.maintenance_db.get_all_requests()
        self.maintenance_table.setRowCount(0)
        t = Theme.get()
        for i, r in enumerate(requests):
            self._set_table_row(self.maintenance_table, i, [
                r['request_id'], r['room_number'], r['renter_name'],
                r['description'], r['priority'], r['status'],
                str(r['request_date'])
            ])
            priority_colors = {"High": t['red'], "Medium": t['accent'], "Low": t['green']}
            color = priority_colors.get(r['priority'], t['text'])
            self.maintenance_table.item(i, 4).setForeground(QColor(color))

    def open_add_maintenance_dialog(self):
        rooms   = self.room_db.get_all_rooms()
        renters = self.renter_db.get_all_renters()
        dlg = MaintenanceDialog(self, rooms, renters)
        if dlg.exec():
            data = dlg.get_data()
            ok = self.maintenance_db.add_request(**data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'ADD_MAINTENANCE',
                                          f"Maintenance request added for room {data['room_id']}")
                QMessageBox.information(self, "Success", "Request added!")
                self.load_maintenance()
            else:
                QMessageBox.critical(self, "Error", "Failed to add request.")

    def resolve_maintenance(self):
        row = self.maintenance_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a request.")
            return
        request_id = int(self.maintenance_table.item(row, 0).text())
        ok = self.maintenance_db.update_status(request_id, "Completed",
                                               "Resolved by admin.",
                                               QDate.currentDate().toString("yyyy-MM-dd"))
        if ok:
            if self.current_user:
                self.admin_db.add_log(self.current_user['admin_id'], 'RESOLVE_MAINTENANCE',
                                      f"Resolved request ID {request_id}")
            self.load_maintenance()

    def delete_maintenance(self):
        row = self.maintenance_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a request.")
            return
        request_id = int(self.maintenance_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this request?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.maintenance_db.delete_request(request_id)
            if ok:
                self.load_maintenance()

    def _build_visitors_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addWidget(page_header("Visitor Logs", "  Log Visitor In", self.open_add_visitor_dialog, btn_icon="fa5s.sign-in-alt"))
        layout.addSpacing(10)

        self.visitors_table = self._make_table(
            ["ID", "Visitor Name", "Relationship", "Visiting Renter", "Time In", "Time Out"]
        )
        layout.addWidget(self.visitors_table)

        btn_row = QHBoxLayout()
        out_btn    = make_btn("  Log Out",  T("blue"), "white", icon="fa5s.sign-out-alt", icon_color="white")
        delete_btn = make_btn("  Delete",   T("red"),  "white", icon="fa5s.trash-alt",    icon_color="white")
        out_btn.clicked.connect(self.log_visitor_out)
        delete_btn.clicked.connect(self.delete_visitor)
        btn_row.addStretch()
        btn_row.addWidget(out_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)
        return page

    def load_visitors(self):
        visitors = self.visitor_db.get_all_visitors()
        self.visitors_table.setRowCount(0)
        for i, v in enumerate(visitors):
            self._set_table_row(self.visitors_table, i, [
                v['visitor_id'], v['visitor_name'], v['relationship'],
                v['renter_name'], str(v['time_in']),
                str(v['time_out']) if v['time_out'] else "Still inside"
            ])

    def open_add_visitor_dialog(self):
        renters = self.renter_db.get_all_renters()
        dlg = VisitorDialog(self, renters)
        if dlg.exec():
            data = dlg.get_data()
            ok = self.visitor_db.log_visitor_in(**data)
            if ok:
                if self.current_user:
                    self.admin_db.add_log(self.current_user['admin_id'], 'VISITOR_IN',
                                          f"{data['visitor_name']} logged in as visitor")
                self.load_visitors()
            else:
                QMessageBox.critical(self, "Error", "Failed to log visitor.")

    def log_visitor_out(self):
        row = self.visitors_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a visitor.")
            return
        visitor_id = int(self.visitors_table.item(row, 0).text())
        ok = self.visitor_db.log_visitor_out(visitor_id,
                                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if ok:
            self.load_visitors()

    def delete_visitor(self):
        row = self.visitors_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a visitor.")
            return
        visitor_id = int(self.visitors_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm", "Delete this visitor log?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            ok = self.visitor_db.delete_visitor_log(visitor_id)
            if ok:
                self.load_visitors()

class RenterDialog(QDialog):
    def __init__(self, parent, renter=None):
        super().__init__(parent)
        self.setWindowTitle("Register Renter" if not renter else "Edit Renter")
        self.setFixedWidth(500)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(placeholder=""):
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            e.setStyleSheet(input_style())
            return e

        self.first_name  = inp("First Name")
        self.middle_name = inp("Middle Name (optional)")
        self.last_name   = inp("Last Name")
        self.occupation  = QComboBox()
        self.occupation.addItems(["Student", "Professional", "Other"])
        self.occupation.setStyleSheet(input_style())
        self.institution = inp("School / Employer")
        self.gender      = QComboBox()
        self.gender.addItems(["Female", "Male", "Other"])
        self.gender.setStyleSheet(input_style())
        self.contact     = inp("09XXXXXXXXX")
        self.email       = inp("email@example.com")
        self.id_type     = inp("e.g. School ID, National ID")
        self.id_number   = inp("ID Number")
        self.address     = QTextEdit()
        self.address.setFixedHeight(60)
        self.address.setStyleSheet(input_style())
        self.emergency_name   = inp("Emergency Contact Name")
        self.emergency_number = inp("Emergency Contact Number")
        self.status = QComboBox()
        self.status.addItems(["Active", "Inactive", "Blacklisted"])
        self.status.setStyleSheet(input_style())

        layout.addRow("First Name*:",     self.first_name)
        layout.addRow("Middle Name:",     self.middle_name)
        layout.addRow("Last Name*:",      self.last_name)
        layout.addRow("Occupation:",      self.occupation)
        layout.addRow("School/Employer:", self.institution)
        layout.addRow("Gender:",          self.gender)
        layout.addRow("Contact*:",        self.contact)
        layout.addRow("Email:",           self.email)
        layout.addRow("ID Type:",         self.id_type)
        layout.addRow("ID Number:",       self.id_number)
        layout.addRow("Address:",         self.address)
        layout.addRow("Emerg. Name:",     self.emergency_name)
        layout.addRow("Emerg. Number:",   self.emergency_number)
        layout.addRow("Status:",          self.status)

        if renter:
            self.first_name.setText(renter.get('first_name', ''))
            self.middle_name.setText(renter.get('middle_name', ''))
            self.last_name.setText(renter.get('last_name', ''))
            self.occupation.setCurrentText(renter.get('occupation_type', 'Student'))
            self.institution.setText(renter.get('institution_employer', '') or '')
            self.gender.setCurrentText(renter.get('gender', 'Female'))
            self.contact.setText(renter.get('contact_number', ''))
            self.email.setText(renter.get('email', '') or '')
            self.id_type.setText(renter.get('id_type', '') or '')
            self.id_number.setText(renter.get('id_number', '') or '')
            self.address.setPlainText(renter.get('address', '') or '')
            self.emergency_name.setText(renter.get('emergency_contact_name', '') or '')
            self.emergency_number.setText(renter.get('emergency_contact_number', '') or '')
            self.status.setCurrentText(renter.get('renter_status', 'Active'))

        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        save_btn.clicked.connect(self._validate_and_accept)
        layout.addRow(save_btn)

    def _validate_and_accept(self):
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            QMessageBox.warning(self, "Missing", "First and Last name are required.")
            return
        if not self.contact.text().strip():
            QMessageBox.warning(self, "Missing", "Contact number is required.")
            return
        self.accept()

    def get_data(self):
        return dict(
            first_name=self.first_name.text().strip(),
            middle_name=self.middle_name.text().strip(),
            last_name=self.last_name.text().strip(),
            occupation_type=self.occupation.currentText(),
            institution_employer=self.institution.text().strip() or None,
            gender=self.gender.currentText(),
            contact_number=self.contact.text().strip(),
            email=self.email.text().strip() or None,
            id_type=self.id_type.text().strip() or None,
            id_number=self.id_number.text().strip() or None,
            address=self.address.toPlainText().strip() or None,
            emergency_contact_name=self.emergency_name.text().strip() or None,
            emergency_contact_number=self.emergency_number.text().strip() or None,
            renter_status=self.status.currentText()
        )

class RoomDialog(QDialog):
    def __init__(self, parent, room=None):
        super().__init__(parent)
        self.setWindowTitle("Add Room" if not room else "Edit Room")
        self.setFixedWidth(420)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(ph=""):
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setStyleSheet(input_style())
            return e

        self.room_number  = inp("e.g. 101")
        self.floor_level  = QComboBox()
        self.floor_level.addItems(["1st Floor", "2nd Floor"])
        self.floor_level.setStyleSheet(input_style())
        self.monthly_rate = inp("e.g. 1800")
        self.capacity     = inp("e.g. 4")
        self.status       = QComboBox()
        self.status.addItems(["Available", "Full", "Under Maintenance"])
        self.status.setStyleSheet(input_style())
        self.description  = QTextEdit()
        self.description.setFixedHeight(60)
        self.description.setStyleSheet(input_style())

        layout.addRow("Room Number*:", self.room_number)
        layout.addRow("Floor Level:",  self.floor_level)
        layout.addRow("Monthly Rate:", self.monthly_rate)
        layout.addRow("Capacity:",     self.capacity)
        layout.addRow("Status:",       self.status)
        layout.addRow("Description:",  self.description)

        if room:
            self.room_number.setText(room.get('room_number', ''))
            self.floor_level.setCurrentText(room.get('floor_level', '1st Floor'))
            self.monthly_rate.setText(str(room.get('monthly_rate', '')))
            self.capacity.setText(str(room.get('capacity', '')))
            self.status.setCurrentText(room.get('status', 'Available'))
            self.description.setPlainText(room.get('description', '') or '')

        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)

    def get_data(self):
        return dict(
            room_number=self.room_number.text().strip(),
            floor_level=self.floor_level.currentText(),
            monthly_rate=float(self.monthly_rate.text() or 0),
            capacity=int(self.capacity.text() or 0),
            status=self.status.currentText(),
            description=self.description.toPlainText().strip()
        )

class PaymentDialog(QDialog):
    def __init__(self, parent, renters):
        super().__init__(parent)
        self.setWindowTitle("Record Payment")
        self.setFixedWidth(440)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(ph=""):
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setStyleSheet(input_style())
            return e

        self.invoice      = inp("e.g. INV-2026-001")
        self.renter_combo = QComboBox()
        self.renter_combo.setStyleSheet(input_style())
        self._renter_ids  = []
        for r in renters:
            self.renter_combo.addItem(f"{r['first_name']} {r['last_name']}")
            self._renter_ids.append(r['renter_id'])
        self.amount       = inp("e.g. 1800.00")
        self.balance      = inp("Remaining balance (0 if fully paid)")
        self.method       = QComboBox()
        self.method.addItems(["Cash", "GCash", "Bank Transfer", "Other"])
        self.method.setStyleSheet(input_style())
        self.reference    = inp("Reference # (optional)")
        self.billing_month= inp("e.g. May 2026")
        self.pay_date     = QDateEdit(QDate.currentDate())
        self.pay_date.setCalendarPopup(True)
        self.pay_date.setStyleSheet(input_style())
        self.status       = QComboBox()
        self.status.addItems(["Paid", "Partial", "Pending", "Overdue", "Advanced"])
        self.status.setStyleSheet(input_style())
        self.remarks      = inp("Remarks (optional)")

        layout.addRow("Invoice No*:",   self.invoice)
        layout.addRow("Renter*:",       self.renter_combo)
        layout.addRow("Amount*:",       self.amount)
        layout.addRow("Balance:",       self.balance)
        layout.addRow("Method:",        self.method)
        layout.addRow("Reference #:",   self.reference)
        layout.addRow("Billing Month:", self.billing_month)
        layout.addRow("Payment Date:",  self.pay_date)
        layout.addRow("Status:",        self.status)
        layout.addRow("Remarks:",       self.remarks)

        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)

    def get_data(self):
        return dict(
            invoice_number=self.invoice.text().strip(),
            renter_id=self._renter_ids[self.renter_combo.currentIndex()],
            amount=float(self.amount.text() or 0),
            balance_amount=float(self.balance.text() or 0),
            payment_method=self.method.currentText(),
            billing_month=self.billing_month.text().strip(),
            payment_date=self.pay_date.date().toString("yyyy-MM-dd"),
            status=self.status.currentText(),
            reference_number=self.reference.text().strip() or None,
            remarks=self.remarks.text().strip() or None,
            processed_by=None
        )

class MaintenanceDialog(QDialog):
    def __init__(self, parent, rooms, renters):
        super().__init__(parent)
        self.setWindowTitle("Add Maintenance Request")
        self.setFixedWidth(440)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        self.room_combo = QComboBox()
        self.room_combo.setStyleSheet(input_style())
        self._room_ids = []
        for r in rooms:
            self.room_combo.addItem(f"Room {r['room_number']} ({r['floor_level']})")
            self._room_ids.append(r['room_id'])

        self.renter_combo = QComboBox()
        self.renter_combo.setStyleSheet(input_style())
        self._renter_ids = []
        for r in renters:
            self.renter_combo.addItem(f"{r['first_name']} {r['last_name']}")
            self._renter_ids.append(r['renter_id'])

        self.description = QTextEdit()
        self.description.setFixedHeight(80)
        self.description.setStyleSheet(input_style())
        self.priority = QComboBox()
        self.priority.addItems(["Low", "Medium", "High"])
        self.priority.setCurrentText("Medium")
        self.priority.setStyleSheet(input_style())

        layout.addRow("Room*:",    self.room_combo)
        layout.addRow("Renter*:",  self.renter_combo)
        layout.addRow("Issue*:",   self.description)
        layout.addRow("Priority:", self.priority)

        save_btn = make_btn("  Save", T("green"), "white", icon="fa5s.save", icon_color="white")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)

    def get_data(self):
        return dict(
            room_id=self._room_ids[self.room_combo.currentIndex()],
            renter_id=self._renter_ids[self.renter_combo.currentIndex()],
            description=self.description.toPlainText().strip(),
            priority=self.priority.currentText()
        )

class VisitorDialog(QDialog):
    def __init__(self, parent, renters):
        super().__init__(parent)
        self.setWindowTitle("Log Visitor In")
        self.setFixedWidth(400)
        self.setStyleSheet(dialog_style())
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(ph=""):
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setStyleSheet(input_style())
            return e

        self.visitor_name = inp("Visitor Full Name")
        self.relationship = inp("e.g. Parent, Sibling, Friend")
        self.renter_combo = QComboBox()
        self.renter_combo.setStyleSheet(input_style())
        self._renter_ids  = []
        for r in renters:
            self.renter_combo.addItem(f"{r['first_name']} {r['last_name']}")
            self._renter_ids.append(r['renter_id'])

        layout.addRow("Visitor Name*:", self.visitor_name)
        layout.addRow("Relationship:",  self.relationship)
        layout.addRow("Visiting*:",     self.renter_combo)

        save_btn = make_btn("  Log In", T("green"), "white", icon="fa5s.sign-in-alt", icon_color="white")
        save_btn.clicked.connect(self.accept)
        layout.addRow(save_btn)

    def get_data(self):
        return dict(
            renter_id=self._renter_ids[self.renter_combo.currentIndex()],
            visitor_name=self.visitor_name.text().strip(),
            relationship=self.relationship.text().strip()
        )

class DormNormApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DormNorm")
        self.setMinimumSize(1100, 750)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome   = WelcomePage(self.stack)
        self.login     = LoginPage(self.stack)
        self.dashboard = DashboardPage(self.stack)

        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentIndex(0)

    def fade_to_page(self, index):
        self.anim = QPropertyAnimation(self.stack, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)

        def change_page():
            self.stack.setCurrentIndex(index)
            self.anim2 = QPropertyAnimation(self.stack, b"windowOpacity")
            self.anim2.setDuration(400)
            self.anim2.setStartValue(0.0)
            self.anim2.setEndValue(1.0)
            self.anim2.start()

        self.anim.finished.connect(change_page)
        self.anim.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DormNormApp()
    window.showMaximized()
    sys.exit(app.exec())