#!/usr/bin/env python3
"""
Hash – Instagram Profile Viewer
A sleek GUI tool to fetch public Instagram profile data using session cookies.
Developed by naif - khaled
"""

import sys
import re
import json
import time
import requests
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QProgressBar, QFileDialog, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

# ----------------------------------------------------------------------
# Dark theme stylesheet
# ----------------------------------------------------------------------
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QGroupBox {
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 1ex;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}
QLabel {
    color: #cdd6f4;
}
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px;
}
QLineEdit:focus {
    border: 1px solid #89b4fa;
}
QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #585b70;
}
QPushButton:pressed {
    background-color: #313244;
}
QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}
QTextEdit {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    font-family: "Courier New";
    font-size: 10pt;
}
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #cdd6f4;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 4px;
}
QScrollArea {
    background: transparent;
    border: none;
}
"""

# ----------------------------------------------------------------------
# Core scraper logic (same as before, with retry)
# ----------------------------------------------------------------------

def print_profile_text(info: Dict) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append(f"👤 @{info.get('username', 'N/A')} ({info.get('full_name', 'N/A')})")
    lines.append("=" * 70)
    lines.append(f"🆔 User ID         : {info.get('id', 'N/A')}")
    lines.append(f"🔒 Private         : {'YES' if info.get('is_private') else 'NO'}")
    lines.append(f"✅ Verified        : {'YES' if info.get('is_verified') else 'NO'}")
    acc_type = info.get('professional_type') or 'Personal'
    is_biz = info.get('is_business', False)
    is_pro = info.get('is_professional', False)
    if is_biz:
        acc_type += ' (Business)'
    elif is_pro:
        acc_type += ' (Creator)'
    else:
        acc_type += ' (Personal)'
    lines.append(f"📊 Account type    : {acc_type}")
    if info.get('business_category'):
        lines.append(f"🏢 Category        : {info['business_category']}")
    if info.get('business_email'):
        lines.append(f"📧 Email           : {info['business_email']}")
    if info.get('business_phone'):
        lines.append(f"📞 Phone           : {info['business_phone']}")
    if info.get('address_street') or info.get('city'):
        street = info.get('address_street', '')
        city = info.get('city', '')
        zip_code = info.get('zip', '')
        lines.append(f"📍 Address         : {street}, {city} {zip_code}".strip())
    lines.append(f"\n👥 Followers       : {info.get('follower_count', 0):,}")
    lines.append(f"👣 Following       : {info.get('following_count', 0):,}")
    lines.append(f"📷 Posts           : {info.get('post_count', 0):,}")
    lines.append(f"🎬 Reels           : {info.get('reel_count', 0)}")
    lines.append(f"📺 IGTV            : {info.get('igtv_count', 0)}")
    lines.append(f"⭐ Highlights      : {info.get('highlight_count', 0)}")
    bio = info.get('bio', '')[:200]
    lines.append(f"\n📝 Bio             : {bio}")
    bio_links = info.get('bio_links', [])
    if bio_links:
        links = [link.get('url', '') for link in bio_links if link.get('url')]
        lines.append(f"🔗 Bio links       : {', '.join(links)}")
    if info.get('external_url'):
        lines.append(f"🌐 External URL   : {info['external_url']}")
    if info.get('profile_pic_url'):
        pic = info['profile_pic_url'][:80]
        lines.append(f"🖼️ Profile pic URL : {pic}...")
    if info.get('joined_recently'):
        lines.append("🆕 Joined recently")
    lines.append(f"\n🤝 You follow them : {info.get('following_viewer', False)}")
    lines.append(f"🤝 They follow you : {info.get('followed_by_viewer', False)}")
    lines.append("=" * 70)
    return "\n".join(lines)


def get_own_username_from_homepage(session: requests.Session) -> Optional[str]:
    try:
        resp = session.get('https://www.instagram.com/', timeout=10)
        if resp.status_code != 200:
            return None
        match = re.search(r'window\._sharedData\s*=\s*({.*?});', resp.text, re.DOTALL)
        if not match:
            return None
        shared = json.loads(match.group(1))
        viewer = shared.get('config', {}).get('viewer')
        if viewer and viewer.get('username'):
            return viewer['username']
        return None
    except Exception:
        return None


def fetch_profile(sessionid: str, csrftoken: str, user_id: str,
                  target_username: Optional[str] = None,
                  retry_count: int = 3,
                  status_callback=None) -> Dict:
    for attempt in range(retry_count + 1):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'X-IG-App-ID': '936619743392459',
        })
        session.cookies.set('sessionid', sessionid, domain='.instagram.com')
        session.cookies.set('csrftoken', csrftoken, domain='.instagram.com')
        session.headers['X-CSRFToken'] = csrftoken

        try:
            r = session.get('https://www.instagram.com/', timeout=5)
            m = re.search(r'"www_claim":"([^"]+)"', r.text)
            if m:
                session.headers['X-IG-WWW-Claim'] = m.group(1)
        except:
            pass

        if not target_username:
            info_url = f'https://i.instagram.com/api/v1/users/{user_id}/info/'
            resp = session.get(info_url, params={'__d': 'disco', '__user': user_id}, timeout=10)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    own_username = data.get('user', {}).get('username')
                    if own_username:
                        target_username = own_username
                except:
                    pass
            if not target_username:
                target_username = get_own_username_from_homepage(session)
                if not target_username:
                    return {'error': 'Could not auto-detect your username. Please provide it manually.'}

        web_url = 'https://i.instagram.com/api/v1/users/web_profile_info/'
        params = {
            'username': target_username,
            '__d': 'disco',
            '__user': user_id,
            '__a': '1',
            '__req': '3',
        }
        resp = session.get(web_url, params=params, timeout=10)

        if resp.status_code == 200:
            try:
                data = resp.json()
                user_data = data.get('data', {}).get('user')
                if not user_data:
                    user_data = data.get('user')
                if not user_data:
                    return {'error': 'User data not found in response.'}
                profile = {
                    'id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name'),
                    'is_private': user_data.get('is_private'),
                    'is_verified': user_data.get('is_verified'),
                    'professional_type': user_data.get('professional_type'),
                    'is_business': user_data.get('is_business'),
                    'is_professional': user_data.get('is_professional'),
                    'business_category': user_data.get('business_category'),
                    'business_email': user_data.get('business_email'),
                    'business_phone': user_data.get('business_phone'),
                    'address_street': user_data.get('address_street'),
                    'city': user_data.get('city'),
                    'zip': user_data.get('zip'),
                    'follower_count': user_data.get('edge_followed_by', {}).get('count'),
                    'following_count': user_data.get('edge_follow', {}).get('count'),
                    'post_count': user_data.get('edge_owner_to_timeline_media', {}).get('count'),
                    'reel_count': user_data.get('reel_count'),
                    'igtv_count': user_data.get('igtv_count'),
                    'highlight_count': user_data.get('highlight_count'),
                    'bio': user_data.get('biography'),
                    'bio_links': user_data.get('bio_links'),
                    'external_url': user_data.get('external_url'),
                    'profile_pic_url': user_data.get('profile_pic_url'),
                    'joined_recently': user_data.get('joined_recently'),
                    'following_viewer': user_data.get('following_viewer'),
                    'followed_by_viewer': user_data.get('followed_by_viewer'),
                }
                if profile['follower_count'] is None:
                    profile['follower_count'] = user_data.get('follower_count', 0)
                if profile['following_count'] is None:
                    profile['following_count'] = user_data.get('following_count', 0)
                if profile['post_count'] is None:
                    profile['post_count'] = user_data.get('media_count', 0)
                return {'success': True, 'profile': profile}
            except Exception as e:
                return {'error': f'Parsing error: {e}'}

        elif resp.status_code == 429:
            retry_after = resp.headers.get('Retry-After')
            if retry_after:
                try:
                    wait = int(retry_after)
                except:
                    wait = 60
            else:
                wait = 60 * (attempt + 1)
            if status_callback:
                status_callback(f"⚠️ Rate limited (attempt {attempt+1}). Waiting {wait} seconds...")
            if attempt < retry_count:
                time.sleep(wait)
                continue
            else:
                return {'error': f'Rate limited after {retry_count+1} attempts. Please wait longer and retry manually.'}
        else:
            return {'error': f'HTTP {resp.status_code}: {resp.text[:200]}'}

    return {'error': 'Unexpected failure.'}


# ----------------------------------------------------------------------
# Worker thread
# ----------------------------------------------------------------------
class FetchWorker(QThread):
    finished = pyqtSignal(dict)
    status_update = pyqtSignal(str)

    def __init__(self, sessionid, csrftoken, user_id, target_username):
        super().__init__()
        self.sessionid = sessionid
        self.csrftoken = csrftoken
        self.user_id = user_id
        self.target_username = target_username

    def run(self):
        def status_callback(msg):
            self.status_update.emit(msg)
        result = fetch_profile(
            self.sessionid, self.csrftoken, self.user_id,
            self.target_username, retry_count=3,
            status_callback=status_callback
        )
        self.finished.emit(result)


# ----------------------------------------------------------------------
# Main Window – Hash
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hash – Instagram Profile Viewer')
        self.setMinimumSize(780, 700)

        # Apply dark style
        self.setStyleSheet(DARK_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ----- Help / Info Section (collapsible) -----
        help_group = QGroupBox("📖 What this script does")
        help_group.setCheckable(True)
        help_group.setChecked(False)  # collapsed by default
        help_layout = QVBoxLayout(help_group)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <b>Hash – Instagram Profile Viewer</b><br>
        <br>
        This tool fetches detailed public profile information from Instagram using your session cookies.
        <br><br>
        <b>How to get your cookies:</b><br>
        1. Log in to Instagram in your browser.<br>
        2. Open Developer Tools (F12) → Application → Cookies → https://www.instagram.com.<br>
        3. Copy the values for <b>sessionid</b>, <b>csrftoken</b>, and <b>ds_user_id</b>.<br>
        4. Paste them into the fields below, or click <b>Load JSON</b> to upload a file.<br>
        <br>
        <b>JSON file format:</b><br>
        <pre>{
          "sessionid": "123...",
          "csrftoken": "abc...",
          "ds_user_id": "456...",
          "target": "username"   (optional)
        }</pre>
        <br>
        <b>Features:</b><br>
        • Auto‑detects your own username if no target is given.<br>
        • Handles rate limits (429) with automatic retry (up to 3 attempts).<br>
        • Displays follower count, bio, business info, story/reel counts, and more.<br>
        <br>
        <i>Developed by naif · khaled</i>
        """)
        help_layout.addWidget(help_text)
        main_layout.addWidget(help_group)

        # ----- Credentials Group -----
        input_group = QGroupBox('🔑 Account Credentials')
        form = QFormLayout(input_group)

        self.sessionid_edit = QLineEdit()
        self.sessionid_edit.setPlaceholderText('e.g. 1234567890%3A...')
        form.addRow('Session ID:', self.sessionid_edit)

        self.csrftoken_edit = QLineEdit()
        self.csrftoken_edit.setPlaceholderText('e.g. abc123...')
        form.addRow('CSRF Token:', self.csrftoken_edit)

        self.userid_edit = QLineEdit()
        self.userid_edit.setPlaceholderText('e.g. 1234567890')
        form.addRow('User ID (ds_user_id):', self.userid_edit)

        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText('Leave empty to auto-detect your own username')
        form.addRow('Target Username (optional):', self.target_edit)

        # Load JSON button
        load_btn = QPushButton('📂 Load Cookies JSON')
        load_btn.clicked.connect(self.load_json)
        form.addRow(load_btn)

        main_layout.addWidget(input_group)

        # ----- Buttons and Progress -----
        btn_layout = QHBoxLayout()
        self.fetch_btn = QPushButton('🚀 Fetch Profile')
        self.fetch_btn.clicked.connect(self.on_fetch)
        self.clear_btn = QPushButton('🗑️ Clear Output')
        self.clear_btn.clicked.connect(self.clear_output)
        self.retry_btn = QPushButton('🔁 Retry Last')
        self.retry_btn.clicked.connect(self.on_retry)
        self.retry_btn.setEnabled(False)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        btn_layout.addWidget(self.fetch_btn)
        btn_layout.addWidget(self.retry_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.progress)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ----- Output Area -----
        output_group = QGroupBox('📋 Profile Output')
        output_layout = QVBoxLayout(output_group)
        self.output = QTextEdit()
        self.output.setFont(QFont('Courier New', 10))
        self.output.setReadOnly(True)
        output_layout.addWidget(self.output)
        main_layout.addWidget(output_group)

        # ----- Footer (developer credit) -----
        footer = QLabel('Developed by naif · khaled  |  Hash v2.0')
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet('color: #6c7086; padding: 5px;')
        main_layout.addWidget(footer)

        # Store last used params for retry
        self.last_sessionid = ''
        self.last_csrftoken = ''
        self.last_user_id = ''
        self.last_target = ''

    # ------------------------------------------------------------------
    # JSON Loader
    # ------------------------------------------------------------------
    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Cookies JSON", "", "JSON Files (*.json)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'sessionid' in data:
                self.sessionid_edit.setText(data['sessionid'])
            if 'csrftoken' in data:
                self.csrftoken_edit.setText(data['csrftoken'])
            if 'ds_user_id' in data:
                self.userid_edit.setText(str(data['ds_user_id']))
            if 'target' in data:
                self.target_edit.setText(data['target'])
            self.output.append(f"✅ Loaded cookies from {file_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load JSON:\n{e}')

    # ------------------------------------------------------------------
    # Fetch / Retry logic
    # ------------------------------------------------------------------
    def on_fetch(self):
        sessionid = self.sessionid_edit.text().strip()
        csrftoken = self.csrftoken_edit.text().strip()
        user_id = self.userid_edit.text().strip()
        target = self.target_edit.text().strip() or None

        if not sessionid or not csrftoken or not user_id:
            QMessageBox.warning(self, 'Missing Fields', 'Please fill in Session ID, CSRF Token, and User ID.')
            return

        self.last_sessionid = sessionid
        self.last_csrftoken = csrftoken
        self.last_user_id = user_id
        self.last_target = target

        self._start_fetch(sessionid, csrftoken, user_id, target)

    def on_retry(self):
        if not self.last_sessionid:
            return
        self._start_fetch(self.last_sessionid, self.last_csrftoken,
                          self.last_user_id, self.last_target)

    def _start_fetch(self, sessionid, csrftoken, user_id, target):
        self.fetch_btn.setEnabled(False)
        self.retry_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.output.clear()
        self.output.append('⏳ Fetching profile... please wait.\n')

        self.worker = FetchWorker(sessionid, csrftoken, user_id, target)
        self.worker.status_update.connect(self.on_status_update)
        self.worker.finished.connect(self.on_fetch_finished)
        self.worker.start()

    def on_status_update(self, msg):
        self.output.append(f'ℹ️ {msg}')

    def on_fetch_finished(self, result):
        self.progress.setVisible(False)
        self.fetch_btn.setEnabled(True)
        self.retry_btn.setEnabled(True)

        if 'error' in result:
            self.output.append(f'❌ ERROR: {result["error"]}')
        elif result.get('success') and 'profile' in result:
            formatted = print_profile_text(result['profile'])
            self.output.append(formatted)
            self.output.append('\n✅ Profile fetched successfully.')
        else:
            self.output.append('❌ Unexpected result.')

    def clear_output(self):
        self.output.clear()


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # base fusion before stylesheet
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
