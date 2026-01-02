"""
Enhanced Panel - Video Enhancement UI.
Supports batch processing with Real-ESRGAN and FFmpeg.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QCheckBox, QProgressBar, QFileDialog, QMessageBox, QRadioButton, QSpinBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from core.video_enhancer import VideoEnhancer, EnhanceMethod, EnhancePreset, EnhanceSettings
from pathlib import Path


class EnhancedPanel(QWidget):
    """Enhanced panel for video enhancement."""
    
    # Signals
    enhance_requested = Signal(list, dict)  # video_paths, settings
    
    def __init__(self, video_enhancer: VideoEnhancer, parent=None):
        super().__init__(parent)
        self.video_enhancer = video_enhancer
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title (fixed at top, outside scroll)
        title = QLabel("🎨 VIDEO ENHANCEMENT")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #64ffda; padding: 10px;")
        main_layout.addWidget(title)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #0f3460;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64ffda;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Scrollable content widget
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 5, 10, 10)
        
        # Video List Section
        video_group = QGroupBox("Videos to Enhance")
        video_layout = QVBoxLayout(video_group)
        
        # Video list
        self._video_list = QListWidget()
        self._video_list.setMinimumHeight(150)
        self._video_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                color: #ccd6f6;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
            }
        """)
        video_layout.addWidget(self._video_list)
        
        # Video buttons
        video_btn_layout = QHBoxLayout()
        
        self._add_video_btn = QPushButton("➕ Add Videos")
        self._add_video_btn.clicked.connect(self._add_videos)
        video_btn_layout.addWidget(self._add_video_btn)
        
        self._remove_video_btn = QPushButton("➖ Remove Selected")
        self._remove_video_btn.clicked.connect(self._remove_selected_video)
        video_btn_layout.addWidget(self._remove_video_btn)
        
        self._clear_video_btn = QPushButton("🗑️ Clear All")
        self._clear_video_btn.clicked.connect(self._clear_videos)
        video_btn_layout.addWidget(self._clear_video_btn)
        
        video_layout.addLayout(video_btn_layout)
        layout.addWidget(video_group)
        
        # Enhancement Method Section
        method_group = QGroupBox("Enhancement Method")
        method_layout = QVBoxLayout(method_group)
        
        # FFmpeg Fast
        self._method_ffmpeg_fast = QRadioButton("⚡ FFmpeg Fast (CPU, ~1-2 min per video)")
        self._method_ffmpeg_fast.setStyleSheet("color: #8892b0;")
        method_layout.addWidget(self._method_ffmpeg_fast)
        
        # FFmpeg Quality
        self._method_ffmpeg_quality = QRadioButton("✨ FFmpeg Quality (CPU, ~2-5 min per video)")
        self._method_ffmpeg_quality.setChecked(True)
        self._method_ffmpeg_quality.setStyleSheet("color: #8892b0;")
        method_layout.addWidget(self._method_ffmpeg_quality)
        
        # Real-ESRGAN 2x
        realesrgan_available = self.video_enhancer.is_realesrgan_available()
        
        self._method_realesrgan_2x = QRadioButton(
            "🤖 AI Upscale 2x - Real-ESRGAN (GPU, ~10-30 min per video)" +
            ("" if realesrgan_available else " [NOT INSTALLED]")
        )
        self._method_realesrgan_2x.setEnabled(realesrgan_available)
        self._method_realesrgan_2x.setStyleSheet(
            "color: #64ffda;" if realesrgan_available else "color: #555;"
        )
        method_layout.addWidget(self._method_realesrgan_2x)
        
        # Real-ESRGAN 4x
        self._method_realesrgan_4x = QRadioButton(
            "🤖 AI Upscale 4x - Real-ESRGAN (GPU, ~30-90 min per video)" +
            ("" if realesrgan_available else " [NOT INSTALLED]")
        )
        self._method_realesrgan_4x.setEnabled(realesrgan_available)
        self._method_realesrgan_4x.setStyleSheet(
            "color: #64ffda;" if realesrgan_available else "color: #555;"
        )
        method_layout.addWidget(self._method_realesrgan_4x)
        
        # Info about Real-ESRGAN
        if not realesrgan_available:
            install_label = QLabel("💡 Install Real-ESRGAN: pip install realesrgan")
            install_label.setStyleSheet("color: #f78c6c; font-size: 11px; font-style: italic;")
            method_layout.addWidget(install_label)
        
        layout.addWidget(method_group)
        
        # Processing Device Section (GPU/CPU)
        device_group = QGroupBox("Processing Device")
        device_layout = QVBoxLayout(device_group)
        
        # Check GPU availability
        try:
            import torch
            self._gpu_available = torch.cuda.is_available()
            self._gpu_name = torch.cuda.get_device_name(0) if self._gpu_available else "None"
        except:
            self._gpu_available = False
            self._gpu_name = "None"
        
        # GPU Info
        if self._gpu_available:
            gpu_info = QLabel(f"🎮 GPU Detected: {self._gpu_name}")
            gpu_info.setStyleSheet("color: #64ffda; font-weight: bold;")
            device_layout.addWidget(gpu_info)
            
            # Use GPU checkbox
            self._use_gpu_check = QCheckBox("✅ Use GPU for Real-ESRGAN (10-50x faster!)")
            self._use_gpu_check.setChecked(True)
            self._use_gpu_check.setStyleSheet("color: #8892b0; font-weight: bold;")
            device_layout.addWidget(self._use_gpu_check)
            
            gpu_note = QLabel("   💡 Falls back to CPU if GPU is busy or out of memory")
            gpu_note.setStyleSheet("color: #636e72; font-size: 10px; font-style: italic;")
            device_layout.addWidget(gpu_note)
        else:
            no_gpu_label = QLabel("⚠️ No GPU detected - using CPU only")
            no_gpu_label.setStyleSheet("color: #f78c6c;")
            device_layout.addWidget(no_gpu_label)
            
            self._use_gpu_check = QCheckBox("Use GPU")
            self._use_gpu_check.setChecked(False)
            self._use_gpu_check.setEnabled(False)
            device_layout.addWidget(self._use_gpu_check)
            
            cpu_note = QLabel("   💡 Real-ESRGAN will be MUCH slower on CPU (10-50x)")
            cpu_note.setStyleSheet("color: #636e72; font-size: 10px; font-style: italic;")
            device_layout.addWidget(cpu_note)
        
        layout.addWidget(device_group)
        
        # Enhancement Settings Section (for FFmpeg methods)
        settings_group = QGroupBox("Enhancement Settings (FFmpeg only)")
        settings_layout = QVBoxLayout(settings_group)
        
        # Preset
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)
        
        self._preset_combo = QComboBox()
        self._preset_combo.addItems([
            "Subtle",
            "Normal (Recommended)",
            "Strong",
            "Maximum"
        ])
        self._preset_combo.setCurrentIndex(1)  # Normal
        preset_layout.addWidget(self._preset_combo)
        preset_layout.addStretch()
        settings_layout.addLayout(preset_layout)
        
        # Options
        self._sharpen_check = QCheckBox("✨ Sharpen Video")
        self._sharpen_check.setChecked(True)
        settings_layout.addWidget(self._sharpen_check)
        
        self._denoise_check = QCheckBox("🧹 Remove Noise (Denoise)")
        self._denoise_check.setChecked(True)
        settings_layout.addWidget(self._denoise_check)
        
        self._color_check = QCheckBox("🎨 Enhance Colors")
        self._color_check.setChecked(True)
        settings_layout.addWidget(self._color_check)
        
        # Upscale (for FFmpeg)
        upscale_layout = QHBoxLayout()
        upscale_label = QLabel("Upscale:")
        upscale_layout.addWidget(upscale_label)
        
        self._upscale_combo = QComboBox()
        self._upscale_combo.addItems([
            "Keep Original Resolution",
            "2x (1080p → 4K)",
            "4x (540p → 4K)"
        ])
        upscale_layout.addWidget(self._upscale_combo)
        upscale_layout.addStretch()
        settings_layout.addLayout(upscale_layout)
        
        layout.addWidget(settings_group)
        
        # Output Quality Section (for All methods)
        quality_group = QGroupBox("Output Quality")
        quality_layout = QVBoxLayout(quality_group)
        
        # Bitrate Mode
        bitrate_mode_layout = QHBoxLayout()
        bitrate_mode_label = QLabel("Bitrate Mode:")
        bitrate_mode_layout.addWidget(bitrate_mode_label)
        
        self._bitrate_mode_combo = QComboBox()
        self._bitrate_mode_combo.addItems([
            "Auto (Resolution-based)",
            "High Quality (1.5x Auto)",
            "Maximum Quality (4K-level)",
            "Custom"
        ])
        self._bitrate_mode_combo.setCurrentIndex(0)  # Auto
        self._bitrate_mode_combo.currentIndexChanged.connect(self._on_bitrate_mode_changed)
        bitrate_mode_layout.addWidget(self._bitrate_mode_combo)
        bitrate_mode_layout.addStretch()
        quality_layout.addLayout(bitrate_mode_layout)
        
        # Custom bitrate input (in separate rows for cleaner layout)
        custom_bitrate_layout = QHBoxLayout()
        custom_bitrate_label = QLabel("Value:")
        custom_bitrate_layout.addWidget(custom_bitrate_label)
        
        self._custom_bitrate_spin = QSpinBox()
        self._custom_bitrate_spin.setMinimum(500)  # 0.5 Mbps minimum
        self._custom_bitrate_spin.setMaximum(200000)  # 200 Mbps
        self._custom_bitrate_spin.setValue(4000)  # 4 Mbps default
        self._custom_bitrate_spin.setSuffix(" kbps")
        self._custom_bitrate_spin.setSingleStep(500)  # Increment by 0.5 Mbps
        self._custom_bitrate_spin.setEnabled(False)
        self._custom_bitrate_spin.setMinimumWidth(120)
        custom_bitrate_layout.addWidget(self._custom_bitrate_spin)
        
        self._bitrate_info_label = QLabel("(4 Mbps)")
        self._bitrate_info_label.setStyleSheet("color: #64ffda; font-size: 11px;")
        custom_bitrate_layout.addWidget(self._bitrate_info_label)
        custom_bitrate_layout.addStretch()
        quality_layout.addLayout(custom_bitrate_layout)
        
        # Quick preset buttons in separate row
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Quick:")
        preset_layout.addWidget(preset_label)
        
        self._preset_4mbps_btn = QPushButton("4 Mbps")
        self._preset_4mbps_btn.clicked.connect(lambda: self._custom_bitrate_spin.setValue(4000))
        self._preset_4mbps_btn.setEnabled(False)
        preset_layout.addWidget(self._preset_4mbps_btn)
        
        self._preset_8mbps_btn = QPushButton("8 Mbps")
        self._preset_8mbps_btn.clicked.connect(lambda: self._custom_bitrate_spin.setValue(8000))
        self._preset_8mbps_btn.setEnabled(False)
        preset_layout.addWidget(self._preset_8mbps_btn)
        
        self._preset_12mbps_btn = QPushButton("12 Mbps")
        self._preset_12mbps_btn.clicked.connect(lambda: self._custom_bitrate_spin.setValue(12000))
        self._preset_12mbps_btn.setEnabled(False)
        preset_layout.addWidget(self._preset_12mbps_btn)
        
        self._preset_35mbps_btn = QPushButton("35 Mbps")
        self._preset_35mbps_btn.clicked.connect(lambda: self._custom_bitrate_spin.setValue(35000))
        self._preset_35mbps_btn.setEnabled(False)
        preset_layout.addWidget(self._preset_35mbps_btn)
        
        preset_layout.addStretch()
        quality_layout.addLayout(preset_layout)
        
        # Info label
        bitrate_info = QLabel("💡 Higher bitrate = better quality, larger files")
        bitrate_info.setStyleSheet("color: #636e72; font-size: 10px; font-style: italic;")
        quality_layout.addWidget(bitrate_info)
        quality_layout.addWidget(bitrate_info)
        
        layout.addWidget(quality_group)
        
        # Output Directory Section
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        
        self._output_dir_label = QLabel("Not selected")
        self._output_dir_label.setStyleSheet("color: #f78c6c;")
        output_layout.addWidget(self._output_dir_label)
        
        self._browse_output_btn = QPushButton("📁 Browse...")
        self._browse_output_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self._browse_output_btn)
        
        layout.addWidget(output_group)
        
        # Progress Section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self._status_label = QLabel("Ready to enhance videos")
        self._status_label.setStyleSheet("color: #64ffda;")
        progress_layout.addWidget(self._status_label)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #0f3460;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ccd6f6;
            }
            QProgressBar::chunk {
                background-color: #64ffda;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self._progress_bar)
        
        layout.addWidget(progress_group)
        
        # Enhance Button
        self._enhance_btn = QPushButton("🚀 START ENHANCEMENT")
        self._enhance_btn.setMinimumHeight(50)
        self._enhance_btn.setStyleSheet("""
            QPushButton {
                background-color: #64ffda;
                color: #0a192f;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #52d4c2;
            }
            QPushButton:pressed {
                background-color: #40c4b0;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #555;
            }
        """)
        self._enhance_btn.clicked.connect(self._start_enhancement)
        layout.addWidget(self._enhance_btn)
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def _add_videos(self):
        """Add videos to enhance list."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Videos to Enhance",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*.*)"
        )
        
        if files:
            for filepath in files:
                # Check if already in list
                existing = False
                for i in range(self._video_list.count()):
                    if self._video_list.item(i).data(Qt.ItemDataRole.UserRole) == filepath:
                        existing = True
                        break
                
                if not existing:
                    filename = Path(filepath).name
                    item = QListWidgetItem(f"📹 {filename}")
                    item.setData(Qt.ItemDataRole.UserRole, filepath)
                    self._video_list.addItem(item)
            
            self._update_status()
    
    def _remove_selected_video(self):
        """Remove selected video from list."""
        selected_items = self._video_list.selectedItems()
        for item in selected_items:
            self._video_list.takeItem(self._video_list.row(item))
        
        self._update_status()
    
    def _clear_videos(self):
        """Clear all videos."""
        self._video_list.clear()
        self._update_status()
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self._output_dir_label.setText(directory)
            self._output_dir_label.setStyleSheet("color: #64ffda;")
    
    def _update_status(self):
        """Update status label."""
        count = self._video_list.count()
        if count == 0:
            self._status_label.setText("No videos selected")
            self._status_label.setStyleSheet("color: #f78c6c;")
        else:
            self._status_label.setText(f"{count} video(s) ready to enhance")
            self._status_label.setStyleSheet("color: #64ffda;")
    
    def _start_enhancement(self):
        """Start video enhancement."""
        # Validate inputs
        if self._video_list.count() == 0:
            QMessageBox.warning(self, "No Videos", "Please add videos to enhance.")
            return
        
        if self._output_dir_label.text() == "Not selected":
            QMessageBox.warning(self, "No Output Directory", "Please select an output directory.")
            return
        
        # Collect video paths
        video_paths = []
        for i in range(self._video_list.count()):
            item = self._video_list.item(i)
            video_paths.append(item.data(Qt.ItemDataRole.UserRole))
        
        # Collect settings
        settings = self._collect_settings()
        
        # Emit signal
        self.enhance_requested.emit(video_paths, settings)
    
    def _collect_settings(self) -> dict:
        """Collect enhancement settings."""
        # Determine method
        if self._method_ffmpeg_fast.isChecked():
            method = EnhanceMethod.FFMPEG_FAST
        elif self._method_ffmpeg_quality.isChecked():
            method = EnhanceMethod.FFMPEG_QUALITY
        elif self._method_realesrgan_2x.isChecked():
            method = EnhanceMethod.REALESRGAN_2X
        else:
            method = EnhanceMethod.REALESRGAN_4X
        
        # Determine preset
        preset_map = {
            0: EnhancePreset.SUBTLE,
            1: EnhancePreset.NORMAL,
            2: EnhancePreset.STRONG,
            3: EnhancePreset.MAXIMUM
        }
        preset = preset_map.get(self._preset_combo.currentIndex(), EnhancePreset.NORMAL)
        
        # Upscale factor
        upscale_map = {0: 1, 1: 2, 2: 4}
        upscale_factor = upscale_map.get(self._upscale_combo.currentIndex(), 1)
        
        # Bitrate mode
        bitrate_mode = self._bitrate_mode_combo.currentIndex()
        custom_bitrate = self._custom_bitrate_spin.value() if bitrate_mode == 3 else None
        
        return {
            'method': method,
            'preset': preset,
            'sharpen': self._sharpen_check.isChecked(),
            'denoise': self._denoise_check.isChecked(),
            'enhance_colors': self._color_check.isChecked(),
            'upscale_factor': upscale_factor,
            'output_directory': self._output_dir_label.text(),
            'use_gpu': self._use_gpu_check.isChecked() if self._gpu_available else False,
            'bitrate_mode': bitrate_mode,  # 0=Auto, 1=High, 2=Maximum, 3=Custom
            'custom_bitrate': custom_bitrate
        }
    
    
    def _on_bitrate_mode_changed(self, index: int):
        """Handle bitrate mode change."""
        # Enable/disable custom bitrate input and preset buttons
        is_custom = (index == 3)
        self._custom_bitrate_spin.setEnabled(is_custom)
        self._preset_4mbps_btn.setEnabled(is_custom)
        self._preset_8mbps_btn.setEnabled(is_custom)
        self._preset_12mbps_btn.setEnabled(is_custom)
        self._preset_35mbps_btn.setEnabled(is_custom)
        
        # Update info label
        mode_info = {
            0: "Auto (12-100 Mbps based on resolution)",
            1: "High (18-150 Mbps, 1.5x auto)",
            2: "Maximum (35 Mbps for all, like Topaz!)",
            3: f"Custom ({self._custom_bitrate_spin.value()/1000:.0f} Mbps)"
        }
        self._bitrate_info_label.setText(mode_info.get(index, ""))
    
    def set_progress(self, value: int):
        """Set progress bar value."""
        self._progress_bar.setValue(value)
    
    def set_status(self, message: str, color: str = "#64ffda"):
        """Set status message."""
        self._status_label.setText(message)
        self._status_label.setStyleSheet(f"color: {color};")
    
    def set_enabled(self, enabled: bool):
        """Enable/disable controls."""
        self._add_video_btn.setEnabled(enabled)
        self._remove_video_btn.setEnabled(enabled)
        self._clear_video_btn.setEnabled(enabled)
        self._enhance_btn.setEnabled(enabled)
        self._browse_output_btn.setEnabled(enabled)

