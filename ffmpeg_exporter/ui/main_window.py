"""
Main Window - Primary application window with tab navigation.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from ui.media_panel import MediaPanel
from ui.effects_panel import EffectsPanel
from ui.preview_panel import PreviewPanel
from ui.export_dialog import ExportDialog
from ui.settings_dialog import SettingsDialog
from ui.livestream_panel import LivestreamPanel
from ui.job_monitor_window import JobMonitorWindow
from core.settings_manager import SettingsManager
from core.media_manager import MediaManager, MediaConfig, LoopMode
from core.job_manager import JobManager, JobType
from core.ffmpeg_builder import FFmpegBuilder, ExportSettings
from core.livestream_builder import LivestreamBuilder, LivestreamSettings
from core.stream_scheduler import StreamScheduler, StreamSchedule


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self._settings_manager = SettingsManager()
        self._media_manager = MediaManager()
        self._job_manager = JobManager()
        self._stream_scheduler = StreamScheduler(config_dir="ffmpeg_exporter/config")
        
        # Set scheduler callback
        self._stream_scheduler.set_trigger_callback(self._on_schedule_triggered)
        
        # Job monitor window (created on demand)
        self._job_monitor_window = None
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        
        # Check FFmpeg configuration
        self._check_ffmpeg_config()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("MediaKit Pro")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area (tabs + preview)
        self._content_layout = QHBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        
        # Left panel with tabs
        left_panel = self._create_left_panel()
        self._content_layout.addWidget(left_panel, 1)
        
        # Right panel with preview
        self._preview_panel = PreviewPanel()
        self._content_layout.addWidget(self._preview_panel, 2)
        
        main_layout.addLayout(self._content_layout, 1)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")
    
    def _create_header(self) -> QWidget:
        """Create the header widget."""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # App title
        title = QLabel("◆ MEDIAKIT PRO")
        title.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Job monitor button
        job_monitor_btn = QPushButton("📊")
        job_monitor_btn.setObjectName("iconButton")
        job_monitor_btn.setFixedSize(40, 40)
        job_monitor_btn.setToolTip("Job Monitor")
        job_monitor_btn.clicked.connect(self._show_job_monitor)
        layout.addWidget(job_monitor_btn)
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("iconButton")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)
        
        # Toggle preview button
        self._toggle_preview_btn = QPushButton("👁")
        self._toggle_preview_btn.setObjectName("iconButton")
        self._toggle_preview_btn.setFixedSize(40, 40)
        self._toggle_preview_btn.setToolTip("Toggle Preview")
        self._toggle_preview_btn.setCheckable(True)
        self._toggle_preview_btn.setChecked(True)
        self._toggle_preview_btn.toggled.connect(self._toggle_preview)
        layout.addWidget(self._toggle_preview_btn)
        
        # Export button
        export_btn = QPushButton("EXPORT VIDEO")
        export_btn.setObjectName("exportButton")
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self._show_export_dialog)
        layout.addWidget(export_btn)
        
        return header
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with tabs."""
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setMaximumWidth(450)
        
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("mainTabs")
        
        # Media tab
        self._media_panel = MediaPanel(self._settings_manager)
        self._tab_widget.addTab(self._media_panel, "MEDIA")
        
        # Effects tab
        self._effects_panel = EffectsPanel()
        self._tab_widget.addTab(self._effects_panel, "EFFECTS")
        
        # Livestream tab
        self._livestream_panel = LivestreamPanel(self._settings_manager, self._stream_scheduler)
        self._livestream_panel.start_stream_requested.connect(self._start_livestream)
        self._tab_widget.addTab(self._livestream_panel, "LIVESTREAM")
        
        layout.addWidget(self._tab_widget)
        
        return left_panel
    
    def _apply_styles(self) -> None:
        """Apply CSS styles to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            
            #header {
                background-color: #16213e;
                border-bottom: 1px solid #0f3460;
            }
            
            #appTitle {
                color: #00d4ff;
            }
            
            #iconButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 18px;
            }
            
            #iconButton:hover {
                background-color: #1a4f7a;
            }
            
            #exportButton {
                background-color: #00d4ff;
                color: #16213e;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 12px;
            }
            
            #exportButton:hover {
                background-color: #00b8e6;
            }
            
            #leftPanel {
                background-color: #16213e;
                border-right: 1px solid #0f3460;
            }
            
            QTabWidget::pane {
                border: none;
                background-color: #16213e;
            }
            
            QTabBar::tab {
                background-color: #0f3460;
                color: #8892b0;
                padding: 12px 30px;
                border: none;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #00d4ff;
                border-bottom: 2px solid #00d4ff;
            }
            
            QTabBar::tab:hover:!selected {
                color: white;
            }
            
            QLabel {
                color: #ccd6f6;
            }
            
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
            }
            
            QPushButton:hover {
                background-color: #1a4f7a;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                background-color: #0f3460;
                color: white;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 8px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #00d4ff;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #0f3460;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background-color: #00d4ff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            QSlider::sub-page:horizontal {
                background-color: #00d4ff;
                border-radius: 3px;
            }
            
            QStatusBar {
                background-color: #16213e;
                color: #8892b0;
            }
            
            QGroupBox {
                color: #8892b0;
                font-weight: bold;
                border: 1px solid #0f3460;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QCheckBox {
                color: #ccd6f6;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #0f3460;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
            }
            
            QRadioButton {
                color: #ccd6f6;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #0f3460;
            }
            
            QRadioButton::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
            }
        """)
    
    def _check_ffmpeg_config(self) -> None:
        """Check if FFmpeg is configured."""
        if not self._settings_manager.settings.is_ffmpeg_configured():
            self._status_bar.showMessage("⚠ FFmpeg not configured - Go to Settings")
    
    def _toggle_preview(self, checked: bool) -> None:
        """Toggle preview panel visibility."""
        self._preview_panel.setVisible(checked)
    
    def _show_job_monitor(self) -> None:
        """Show job monitor window."""
        if self._job_monitor_window is None or not self._job_monitor_window.isVisible():
            self._job_monitor_window = JobMonitorWindow(self._job_manager, self)
            self._job_monitor_window.show()
        else:
            self._job_monitor_window.activateWindow()
            self._job_monitor_window.raise_()
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self._settings_manager, self)
        if dialog.exec():
            self._check_ffmpeg_config()
            self._status_bar.showMessage("Settings saved")
    
    def _show_export_dialog(self) -> None:
        """Show export dialog."""
        # First validate FFmpeg
        if not self._settings_manager.settings.is_ffmpeg_configured():
            QMessageBox.warning(
                self,
                "FFmpeg Not Configured",
                "Please configure FFmpeg path in Settings before exporting."
            )
            self._show_settings()
            return
        
        # Collect media config
        media_config = self._collect_media_config()
        
        # Validate configuration
        validation_errors = self._media_manager.validate_config()
        if validation_errors:
            QMessageBox.warning(
                self,
                "Configuration Error",
                "Please fix the following issues:\n\n" + "\n".join(f"• {e}" for e in validation_errors)
            )
            return
        
        # Show export dialog
        dialog = ExportDialog(
            self._settings_manager,
            media_config,
            self._job_manager,
            self
        )
        dialog.exec()
    
    def _collect_media_config(self) -> MediaConfig:
        """Collect media configuration from all panels."""
        config = MediaConfig()
        
        # Get media panel settings
        media_settings = self._media_panel.get_settings()
        config.mode = media_settings.get('mode', config.mode)
        config.video_files = media_settings.get('video_files', [])
        config.cover_video = media_settings.get('cover_video', '')
        config.static_image = media_settings.get('static_image', '')
        config.audio_files = media_settings.get('audio_files', [])
        config.audio_source = media_settings.get('audio_source', config.audio_source)
        config.audio_mix_video_volume = media_settings.get('audio_mix_video_volume', 1.0)
        config.audio_mix_music_volume = media_settings.get('audio_mix_music_volume', 1.0)
        config.loop_mode = media_settings.get('loop_mode', LoopMode.MATCH_AUDIO)
        config.custom_duration = media_settings.get('custom_duration', 0.0)
        config.audio_multiplier = media_settings.get('audio_multiplier', 1)
        
        # SFX on beat settings
        config.sfx_enabled = media_settings.get('sfx_enabled', False)
        config.sfx_file = media_settings.get('sfx_file', '')
        config.sfx_volume = media_settings.get('sfx_volume', 0.5)
        config.beat_times = media_settings.get('beat_times', [])
        
        # Get effects panel settings
        effects_settings = self._effects_panel.get_settings()
        config.logo_overlay = effects_settings.get('logo_overlay', config.logo_overlay)
        config.text_overlay = effects_settings.get('text_overlay', config.text_overlay)
        
        # Update media manager config
        self._media_manager.config = config
        
        return config
    
    def _start_livestream(self, settings_dict: dict) -> None:
        """
        Start a livestream job.
        
        Args:
            settings_dict: Livestream settings as dictionary.
        """
        # First validate FFmpeg
        if not self._settings_manager.settings.is_ffmpeg_configured():
            QMessageBox.warning(
                self,
                "FFmpeg Not Configured",
                "Please configure FFmpeg path in Settings before livestreaming."
            )
            self._show_settings()
            return
        
        # Collect media config
        media_config = self._collect_media_config()
        
        # Validate configuration
        validation_errors = self._media_manager.validate_config()
        if validation_errors:
            QMessageBox.warning(
                self,
                "Configuration Error",
                "Please fix the following issues:\n\n" + "\n".join(f"• {e}" for e in validation_errors)
            )
            return
        
        # Create livestream settings
        stream_settings = LivestreamSettings(
            rtmp_url=settings_dict.get('rtmp_url', 'rtmp://a.rtmp.youtube.com/live2/'),
            stream_key=settings_dict.get('stream_key', ''),
            width=settings_dict.get('width', 1920),
            height=settings_dict.get('height', 1080),
            fps=settings_dict.get('fps', 30),
            bitrate_kbps=settings_dict.get('bitrate_kbps', 4500),
            audio_bitrate_kbps=settings_dict.get('audio_bitrate_kbps', 128),
            duration_minutes=settings_dict.get('duration_minutes', 0),
            encoding_method=settings_dict.get('encoding_method')
        )
        
        try:
            # Build FFmpeg command
            builder = LivestreamBuilder(
                self._settings_manager.settings.ffmpeg_path,
                self._settings_manager.settings.ffprobe_path
            )
            
            command, temp_files = builder.build_command(media_config, stream_settings)
            
            # Create job name
            duration_str = f"{stream_settings.duration_minutes}min" if stream_settings.duration_minutes > 0 else "∞"
            job_name = f"YouTube {stream_settings.resolution} @ {stream_settings.fps}fps ({duration_str})"
            
            # Create job
            job_id = self._job_manager.create_job(
                job_type=JobType.LIVESTREAM,
                name=job_name,
                command=command,
                temp_files=temp_files,
                stream_duration_minutes=stream_settings.duration_minutes if stream_settings.duration_minutes > 0 else None
            )
            
            # Start job
            self._job_manager.start_job(job_id)
            
            # Show job monitor
            self._show_job_monitor()
            
            # Status message
            self._status_bar.showMessage(f"Livestream started: {job_name}")
            
            QMessageBox.information(
                self,
                "Livestream Started",
                f"Livestream has been started!\n\n"
                f"Resolution: {stream_settings.resolution}\n"
                f"FPS: {stream_settings.fps}\n"
                f"Bitrate: {stream_settings.bitrate_kbps} kbps\n\n"
                f"Check the Job Monitor to view status and logs."
            )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Livestream Error",
                f"Failed to start livestream:\n\n{str(e)}"
            )
    
    def _on_schedule_triggered(self, schedule: StreamSchedule) -> None:
        """
        Called when a scheduled stream triggers.
        
        Args:
            schedule: The triggered schedule.
        """
        # Show notification
        QMessageBox.information(
            self,
            "Scheduled Stream Starting",
            f"Starting scheduled stream: {schedule.name}\n\n"
            f"This stream will start automatically in 3 seconds..."
        )
        
        # Extract settings from schedule
        media_config_dict = schedule.media_config
        stream_settings_dict = schedule.stream_settings
        
        # Restore media config
        media_config = MediaConfig()
        for key, value in media_config_dict.items():
            if hasattr(media_config, key):
                setattr(media_config, key, value)
        
        # Validate configuration
        validation_errors = self._media_manager.validate_config()
        if validation_errors:
            QMessageBox.critical(
                self,
                "Scheduled Stream Error",
                f"Cannot start scheduled stream '{schedule.name}':\n\n" + "\n".join(f"• {e}" for e in validation_errors)
            )
            return
        
        # Create livestream settings
        stream_settings = LivestreamSettings(
            rtmp_url=stream_settings_dict.get('rtmp_url', 'rtmp://a.rtmp.youtube.com/live2/'),
            stream_key=stream_settings_dict.get('stream_key', ''),
            width=stream_settings_dict.get('width', 1920),
            height=stream_settings_dict.get('height', 1080),
            fps=stream_settings_dict.get('fps', 30),
            bitrate_kbps=stream_settings_dict.get('bitrate_kbps', 4500),
            audio_bitrate_kbps=stream_settings_dict.get('audio_bitrate_kbps', 128),
            duration_minutes=schedule.duration_minutes,
            encoding_method=stream_settings_dict.get('encoding_method')
        )
        
        try:
            # Build FFmpeg command
            builder = LivestreamBuilder(
                self._settings_manager.settings.ffmpeg_path,
                self._settings_manager.settings.ffprobe_path
            )
            
            command, temp_files = builder.build_command(media_config, stream_settings)
            
            # Create job name
            duration_str = f"{schedule.duration_minutes}min" if schedule.duration_minutes > 0 else "∞"
            job_name = f"[Scheduled] {schedule.name} ({duration_str})"
            
            # Create job
            job_id = self._job_manager.create_job(
                job_type=JobType.LIVESTREAM,
                name=job_name,
                command=command,
                temp_files=temp_files,
                stream_duration_minutes=schedule.duration_minutes if schedule.duration_minutes > 0 else None
            )
            
            # Start job
            self._job_manager.start_job(job_id)
            
            # Show job monitor
            self._show_job_monitor()
            
            # Status message
            self._status_bar.showMessage(f"Scheduled livestream started: {schedule.name}")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Scheduled Stream Error",
                f"Failed to start scheduled stream '{schedule.name}':\n\n{str(e)}"
            )
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save any pending settings
        self._settings_manager.save()
        
        # Shutdown scheduler
        self._stream_scheduler.shutdown()
        
        event.accept()
