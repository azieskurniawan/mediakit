"""
Dialog for configuring audio layer (sound effect).
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSlider, QCheckBox,
    QDoubleSpinBox, QGroupBox
)
from PySide6.QtCore import Qt
from core.media_manager import AudioLayer


class AudioLayerDialog(QDialog):
    """Dialog for configuring an audio layer (sound effect)."""
    
    def __init__(self, parent=None, file_path: str = "", existing_config: AudioLayer = None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle("Configure Sound Effect Layer")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # File info
        file_group = QGroupBox("📁 File")
        file_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        file_layout = QVBoxLayout()
        self._file_label = QLabel(os.path.basename(file_path))
        self._file_label.setStyleSheet("font-weight: bold; color: #ccd6f6; border: none;")
        file_layout.addWidget(self._file_label)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Playback settings
        playback_group = QGroupBox("▶️ Playback")
        playback_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        playback_layout = QVBoxLayout()
        
        # Loop checkbox
        self._loop_checkbox = QCheckBox("🔁 Loop continuously (repeat until video ends)")
        self._loop_checkbox.setChecked(existing_config.loop if existing_config else False)
        self._loop_checkbox.setStyleSheet("color: #ccd6f6; border: none;")
        playback_layout.addWidget(self._loop_checkbox)
        
        # Delay
        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel("Start Delay:"))
        self._delay_spin = QDoubleSpinBox()
        self._delay_spin.setRange(0, 300)
        self._delay_spin.setValue(existing_config.delay_seconds if existing_config else 0)
        self._delay_spin.setSuffix(" sec")
        self._delay_spin.setDecimals(2)
        delay_row.addWidget(self._delay_spin)
        playback_layout.addLayout(delay_row)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # Volume
        volume_group = QGroupBox("🔊 Volume")
        volume_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        volume_layout = QVBoxLayout()
        
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volume:"))
        self._volume_label = QLabel("100%")
        self._volume_label.setStyleSheet("font-weight: bold; color: #64ffda; min-width: 60px;")
        vol_row.addWidget(self._volume_label)
        vol_row.addStretch()
        volume_layout.addLayout(vol_row)
        
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 200)
        self._volume_slider.setValue(int((existing_config.volume if existing_config else 1.0) * 100))
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self._volume_slider)
        
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)
        
        # Fade effects
        fade_group = QGroupBox("⏺️ Fade Effects (Optional)")
        fade_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        fade_layout = QVBoxLayout()
        
        fade_in_row = QHBoxLayout()
        fade_in_row.addWidget(QLabel("Fade In:"))
        self._fade_in_spin = QDoubleSpinBox()
        self._fade_in_spin.setRange(0, 10)
        self._fade_in_spin.setValue(existing_config.fade_in if existing_config else 0)
        self._fade_in_spin.setSuffix(" sec")
        self._fade_in_spin.setDecimals(2)
        fade_in_row.addWidget(self._fade_in_spin)
        fade_layout.addLayout(fade_in_row)
        
        fade_out_row = QHBoxLayout()
        fade_out_row.addWidget(QLabel("Fade Out:"))
        self._fade_out_spin = QDoubleSpinBox()
        self._fade_out_spin.setRange(0, 10)
        self._fade_out_spin.setValue(existing_config.fade_out if existing_config else 0)
        self._fade_out_spin.setSuffix(" sec")
        self._fade_out_spin.setDecimals(2)
        fade_out_row.addWidget(self._fade_out_spin)
        fade_layout.addLayout(fade_out_row)
        
        fade_group.setLayout(fade_layout)
        layout.addWidget(fade_group)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        ok_btn = QPushButton("✅ OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #64ffda;
                border: 1px solid #64ffda;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 255, 218, 0.2);
            }
        """)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_row.addWidget(ok_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        layout.addLayout(btn_row)
    
    def get_config(self) -> AudioLayer:
        """Get configured audio layer."""
        return AudioLayer(
            file_path=self.file_path,
            volume=self._volume_slider.value() / 100.0,
            loop=self._loop_checkbox.isChecked(),
            delay_seconds=self._delay_spin.value(),
            fade_in=self._fade_in_spin.value(),
            fade_out=self._fade_out_spin.value(),
            enabled=True
        )

