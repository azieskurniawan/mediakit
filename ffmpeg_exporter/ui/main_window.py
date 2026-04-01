"""
Main Window - Primary application window with tab navigation.
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from ui.media_panel import MediaPanel
from ui.effects_panel import EffectsPanel
from ui.text_timeline_panel import TextTimelinePanel
from ui.overlay_panel import OverlayPanel
from ui.visualizer_panel import VisualizerPanel
from ui.preview_panel import PreviewPanel
from ui.export_dialog import ExportDialog
from ui.settings_dialog import SettingsDialog
from ui.livestream_panel import LivestreamPanel
from ui.job_monitor_window import JobMonitorWindow
from ui.enhanced_panel import EnhancedPanel
from core.settings_manager import SettingsManager
from core.media_manager import MediaManager, MediaConfig, LoopMode, VisualizerType
from core.job_manager import JobManager, JobType
from core.ffmpeg_builder import FFmpegBuilder, ExportSettings
from core.livestream_builder import LivestreamBuilder, LivestreamSettings
from core.stream_scheduler import StreamScheduler, StreamSchedule
from core.video_enhancer import VideoEnhancer, EnhanceSettings


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Custom signal for cross-thread communication
    enhancement_job_finished = Signal(list, int)  # job_ids, next_index
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self._settings_manager = SettingsManager()
        self._media_manager = MediaManager()
        self._job_manager = JobManager()
        self._stream_scheduler = StreamScheduler(config_dir="ffmpeg_exporter/config")
        self._video_enhancer = VideoEnhancer(self._settings_manager.get_ffmpeg_path())
        
        # Set scheduler callback
        self._stream_scheduler.set_trigger_callback(self._on_schedule_triggered)
        
        # Job monitor window (created on demand)
        self._job_monitor_window = None
        
        # Connect custom signals
        self.enhancement_job_finished.connect(self._process_next_enhancement_job)
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        
        # Connect signals
        self._setup_connections()
        
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
        
        # Queue Panel button (NEW)
        queue_btn = QPushButton("📋")
        queue_btn.setObjectName("iconButton")
        queue_btn.setFixedSize(40, 40)
        queue_btn.setToolTip("Export Queue")
        queue_btn.clicked.connect(self._show_queue_panel)
        layout.addWidget(queue_btn)
        
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
        
        # Text Timeline tab (Multi-text with timing)
        self._text_timeline_panel = TextTimelinePanel()
        self._tab_widget.addTab(self._text_timeline_panel, "TEXT TIMELINE")
        
        # Overlay tab (blend modes + chroma key)
        self._overlay_panel = OverlayPanel()
        self._tab_widget.addTab(self._overlay_panel, "OVERLAY")
        
        # Visualizer tab (NEW)
        self._visualizer_panel = VisualizerPanel()
        self._visualizer_panel.preview_requested.connect(self._generate_visualizer_preview)
        self._visualizer_panel.live_play_requested.connect(self._open_live_visualizer_player)
        self._tab_widget.addTab(self._visualizer_panel, "VISUALIZER")
        
        # Enhanced tab
        self._enhanced_panel = EnhancedPanel(self._video_enhancer)
        self._enhanced_panel.enhance_requested.connect(self._start_enhancement)
        self._tab_widget.addTab(self._enhanced_panel, "ENHANCED")
        
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
    
    def _setup_connections(self) -> None:
        """Setup signal/slot connections between panels."""
        # Connect media panel video selection to preview panel
        self._media_panel.video_selected.connect(self._preview_panel.load_video)
        
        # Connect effects panel preview request
        self._effects_panel.preview_requested.connect(self._generate_spectrum_preview)
        
        # Sample audio titles for Now Playing preview (dari urutan audio di Media panel)
        from pathlib import Path
        self._effects_panel._get_sample_audio_titles = lambda: [
            Path(p).stem for p in (getattr(self._media_panel, '_audio_files', []) or [])[:3]
        ]
    
    def _check_ffmpeg_config(self) -> None:
        """Check if FFmpeg is configured."""
        if not self._settings_manager.settings.is_ffmpeg_configured():
            self._status_bar.showMessage("⚠ FFmpeg not configured - Go to Settings")
    
    def _toggle_preview(self, checked: bool) -> None:
        """Toggle preview panel visibility."""
        self._preview_panel.setVisible(checked)
    
    def _show_queue_panel(self) -> None:
        """Show export queue panel."""
        from ui.queue_panel import QueuePanel
        
        # Create queue panel window if not exists
        if not hasattr(self, '_queue_panel') or not self._queue_panel:
            self._queue_panel = QueuePanel(self)
        
        self._queue_panel.show()
        self._queue_panel.raise_()
        self._queue_panel.activateWindow()
    
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
        
        # Audio layers (sound effects)
        config.audio_layers = media_settings.get('audio_layers', [])
        
        # Video scale/zoom settings
        config.video_scale_enabled = media_settings.get('video_scale_enabled', False)
        config.video_scale_percent = media_settings.get('video_scale_percent', 150)
        
        # Video transition settings
        config.transition_enabled = media_settings.get('transition_enabled', False)
        config.transition_duration = media_settings.get('transition_duration', 1.0)
        config.transition_type = media_settings.get('transition_type', 'fade')
        
        # SFX on beat settings
        config.sfx_enabled = media_settings.get('sfx_enabled', False)
        config.sfx_file = media_settings.get('sfx_file', '')
        config.sfx_volume = media_settings.get('sfx_volume', 0.5)
        config.beat_times = media_settings.get('beat_times', [])
        
        # Get effects panel settings
        effects_settings = self._effects_panel.get_settings()
        config.logo_overlay = effects_settings.get('logo_overlay', config.logo_overlay)
        config.text_overlay = effects_settings.get('text_overlay', config.text_overlay)
        config.now_playing_config = effects_settings.get('now_playing_config', config.now_playing_config)
        config.audio_visualizer = effects_settings.get('audio_visualizer', config.audio_visualizer)
        config.subtitle_config = effects_settings.get('subtitle_config', config.subtitle_config)
        
        # Get animated text timeline settings
        config.animated_text_timeline = self._text_timeline_panel.get_settings()
        
        # Advanced overlays (blend modes + chroma key)
        config.overlays = self._overlay_panel.get_overlays()
        
        # Get visualizer config (NEW)
        config.visualizer = self._visualizer_panel.get_config()
        
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
    
    def _generate_spectrum_preview(self) -> None:
        """Generate a quick preview with spectrum visualization (in background)."""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        from ui.preview_generator import PreviewGenerator
        
        # Collect configuration
        media_config = self._collect_media_config()
        
        # Validate
        errors = self._media_manager.validate_config()
        if errors:
            QMessageBox.warning(
                self,
                "Cannot Generate Preview",
                "Please fix these issues first:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
            return
        
        # Create progress dialog
        self._preview_progress = QProgressDialog("Preparing preview...", "Cancel", 0, 0, self)
        self._preview_progress.setWindowTitle("Generating Preview")
        self._preview_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._preview_progress.setMinimumDuration(0)
        self._preview_progress.setCancelButton(None)  # No cancel for now
        self._preview_progress.setValue(0)
        self._preview_progress.show()
        
        # Create background thread
        self._preview_thread = PreviewGenerator(
            media_config=media_config,
            ffmpeg_path=self._settings_manager.get_ffmpeg_path(),
            ffprobe_path=self._settings_manager.get_ffprobe_path(),
            parent=self
        )
        
        # Connect signals
        self._preview_thread.progress_update.connect(self._on_preview_progress)
        self._preview_thread.preview_ready.connect(self._on_preview_ready)
        self._preview_thread.preview_failed.connect(self._on_preview_failed)
        
        # Start generation
        self._preview_thread.start()
    
    def _on_preview_progress(self, message: str) -> None:
        """Handle preview progress update."""
        if hasattr(self, '_preview_progress'):
            self._preview_progress.setLabelText(message)
    
    def _on_preview_ready(self, preview_path: str) -> None:
        """Handle preview generation completion."""
        from PySide6.QtWidgets import QMessageBox
        
        if hasattr(self, '_preview_progress'):
            self._preview_progress.close()
        
        # Load preview
        self._preview_panel.load_video(preview_path)
        
        QMessageBox.information(
            self,
            "Preview Ready! 🎬",
            "Preview with spectrum generated!\n\nClick ▶ PLAY button to view your result."
        )
    
    def _on_preview_failed(self, error_message: str) -> None:
        """Handle preview generation failure."""
        from PySide6.QtWidgets import QMessageBox
        
        if hasattr(self, '_preview_progress'):
            self._preview_progress.close()
        
        QMessageBox.critical(
            self,
            "Preview Failed",
            f"Failed to generate preview:\n\n{error_message}"
        )
    
    def _start_enhancement(self, video_paths: list, settings_dict: dict) -> None:
        """
        Start video enhancement jobs.
        
        Args:
            video_paths: List of video paths to enhance.
            settings_dict: Enhancement settings as dictionary.
        """
        from pathlib import Path
        
        # Create enhancement settings
        enhance_settings = EnhanceSettings(
            method=settings_dict['method'],
            preset=settings_dict['preset'],
            sharpen=settings_dict['sharpen'],
            denoise=settings_dict['denoise'],
            enhance_colors=settings_dict['enhance_colors'],
            upscale_factor=settings_dict['upscale_factor'],
            output_directory=settings_dict['output_directory'],
            use_gpu=settings_dict.get('use_gpu', True),  # Default to True
            bitrate_mode=settings_dict.get('bitrate_mode', 0),  # Default to Auto
            custom_bitrate=settings_dict.get('custom_bitrate', None)
        )
        
        # Create jobs for each video
        created_jobs = []
        for video_path in video_paths:
            filename = Path(video_path).stem
            output_filename = f"{filename}_enhanced.mp4"
            output_path = str(Path(enhance_settings.output_directory) / output_filename)
            
            # Create job name
            method_names = {
                'ffmpeg_fast': 'FFmpeg Fast',
                'ffmpeg_quality': 'FFmpeg Quality',
                'realesrgan_2x': 'AI 2x',
                'realesrgan_4x': 'AI 4x'
            }
            method_name = method_names.get(enhance_settings.method.value, 'Unknown')
            job_name = f"Enhance: {filename} ({method_name})"
            
            # Build command (we'll use a custom job type)
            # For now, store paths and settings as "command" for the job manager
            job_data = {
                'input_path': video_path,
                'output_path': output_path,
                'settings': enhance_settings
            }
            
            # Create job
            job_id = self._job_manager.create_job(
                job_type=JobType.EXPORT,  # Use EXPORT type for now
                name=job_name,
                command=[],  # Empty command, we'll process differently
                temp_files=[]
            )
            
            # Store job data for processing
            job = self._job_manager.get_job(job_id)
            if job:
                job.metadata = job_data
                created_jobs.append(job_id)
        
        # Start processing jobs sequentially
        if created_jobs:
            self._enhanced_panel.set_enabled(False)
            self._enhanced_panel.set_status(f"Processing {len(created_jobs)} video(s)...", "#64ffda")
            self._enhanced_panel.set_progress(0)
            
            # Process first job
            self._process_next_enhancement_job(created_jobs, 0)
    
    def _process_next_enhancement_job(self, job_ids: list, index: int) -> None:
        """Process enhancement jobs sequentially."""
        if index >= len(job_ids):
            # All jobs completed
            self._enhanced_panel.set_enabled(True)
            self._enhanced_panel.set_status("✅ All videos enhanced!", "#64ffda")
            self._enhanced_panel.set_progress(100)
            
            QMessageBox.information(
                self,
                "Enhancement Complete",
                f"Successfully enhanced {len(job_ids)} video(s)!"
            )
            return
        
        job_id = job_ids[index]
        job = self._job_manager.get_job(job_id)
        
        if not job or not hasattr(job, 'metadata'):
            # Skip invalid job
            self._process_next_enhancement_job(job_ids, index + 1)
            return
        
        job_data = job.metadata
        input_path = job_data['input_path']
        output_path = job_data['output_path']
        settings = job_data['settings']
        
        # Update UI
        self._enhanced_panel.set_status(f"Processing video {index + 1}/{len(job_ids)}...", "#64ffda")
        
        # Progress callback (thread-safe using signal)
        def progress_callback(current_frame, total_frames):
            if total_frames > 0:
                progress = int((current_frame / total_frames) * 100)
                base_progress = int((index / len(job_ids)) * 100)
                job_progress = int(progress / len(job_ids))
                total_progress = base_progress + job_progress
                
                # Update UI on main thread - will be called from worker thread but that's ok for simple value
                # We don't directly manipulate Qt objects
                try:
                    self._enhanced_panel.set_progress(total_progress)
                except:
                    pass  # Ignore threading errors
        
        # Start enhancement in background thread
        import threading
        
        # Store reference to prevent garbage collection
        self._current_enhancement_thread = None
        
        def enhance_thread():
            try:
                success = self._video_enhancer.enhance_video(
                    input_path,
                    output_path,
                    settings,
                    progress_callback
                )
                
                # Update job status
                if success:
                    job.status = 'completed'
                    print(f"✅ Enhanced: {output_path}")
                else:
                    job.status = 'failed'
                    print(f"❌ Failed: {input_path}")
                
                # Emit signal to process next job on main thread
                next_index = index + 1
                self.enhancement_job_finished.emit(job_ids, next_index)
                
            except Exception as e:
                import traceback
                print(f"Enhancement error: {e}")
                print(traceback.format_exc())
                job.status = 'failed'
                
                # Continue with next job
                next_index = index + 1
                self.enhancement_job_finished.emit(job_ids, next_index)
        
        # Start thread
        self._current_enhancement_thread = threading.Thread(target=enhance_thread, daemon=True)
        self._current_enhancement_thread.start()
    
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
    
    def _generate_visualizer_preview(self) -> None:
        """Generate visualizer preview (10 seconds)."""
        from PySide6.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
        from PySide6.QtCore import QThread
        from core.visualizer_preview import VisualizerPreviewGenerator
        from datetime import datetime
        import tempfile
        
        # Get audio files from media panel
        media_settings = self._media_panel.get_settings()
        audio_files = media_settings.get('audio_files', [])
        
        if not audio_files:
            QMessageBox.warning(
                self,
                "No Audio",
                "Please add audio files first in the MEDIA tab."
            )
            return
        
        # Get visualizer config
        visualizer_config = self._visualizer_panel.get_config()
        
        if visualizer_config.type == VisualizerType.NONE:
            QMessageBox.warning(
                self,
                "No Visualizer",
                "Please select a visualizer type (Bar Spectrum or Sound Wave)."
            )
            return
        
        # Ask for output directory only
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Folder for Visualizer Preview",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not output_dir:
            return
        
        # Auto-generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        viz_type = "bar_spectrum" if visualizer_config.type == VisualizerType.BAR_SPECTRUM else "sound_wave"
        output_filename = f"visualizer_preview_{viz_type}_{timestamp}.mp4"
        output_file = os.path.join(output_dir, output_filename)
        
        # Show progress dialog
        progress_dialog = QProgressDialog(
            "Generating visualizer preview...",
            "Cancel",
            0,
            100,
            self
        )
        progress_dialog.setWindowTitle("Preview Generator")
        progress_dialog.setModal(True)
        progress_dialog.show()
        
        # Generate preview
        try:
            ffmpeg_path = self._settings_manager.get_ffmpeg_path()
            generator = VisualizerPreviewGenerator(ffmpeg_path=ffmpeg_path)
            
            def progress_callback(progress: float, message: str):
                progress_dialog.setValue(int(progress * 100))
                progress_dialog.setLabelText(message)
                if progress_dialog.wasCanceled():
                    raise RuntimeError("Cancelled by user")
            
            success = generator.generate_preview(
                audio_files=audio_files,
                visualizer_config=visualizer_config,
                output_file=output_file,
                duration=60.0,  # Changed to 60 seconds (1 minute)
                fps=30,
                width=1920,
                height=1080,
                background_color="#000000",
                progress_callback=progress_callback
            )
            
            progress_dialog.close()
            
            if success:
                # Load in preview panel
                self._preview_panel.load_video(output_file)
                
                QMessageBox.information(
                    self,
                    "Preview Ready! 🎬",
                    f"Visualizer preview generated successfully!\n\n"
                    f"File: {output_filename}\n"
                    f"Location: {output_dir}\n\n"
                    f"Click ▶ PLAY to view."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Preview Failed",
                    "Failed to generate visualizer preview."
                )
        
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Preview generation error:\n\n{str(e)}"
            )
    
    def _open_live_visualizer_player(self) -> None:
        """Open live visualizer player window."""
        from PySide6.QtWidgets import QMessageBox, QDialog
        from ui.live_visualizer_player import LiveVisualizerPlayer
        
        # Get audio files
        media_settings = self._media_panel.get_settings()
        audio_files = media_settings.get('audio_files', [])
        
        if not audio_files:
            QMessageBox.warning(
                self,
                "No Audio",
                "Please add audio files first in the MEDIA tab."
            )
            return
        
        # Get visualizer config
        visualizer_config = self._visualizer_panel.get_config()
        
        if visualizer_config.type == VisualizerType.NONE:
            QMessageBox.warning(
                self,
                "No Visualizer",
                "Please select a visualizer type (Bar Spectrum or Sound Wave)."
            )
            return
        
        # Create live player dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Live Visualizer Player 🎵")
        dialog.setMinimumSize(900, 600)
        dialog.setModal(False)
        
        layout = QVBoxLayout(dialog)
        
        # Create live player widget
        live_player = LiveVisualizerPlayer()
        live_player.set_audio_files(audio_files)
        live_player.set_visualizer_config(visualizer_config)
        live_player.set_ffmpeg_path(self._settings_manager.get_ffmpeg_path())
        
        layout.addWidget(live_player)
        
        # Stop player when dialog is closed
        def on_dialog_finished():
            live_player._media_player.stop()
            live_player._render_timer.stop()
        
        dialog.finished.connect(on_dialog_finished)
        
        dialog.show()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save any pending settings
        self._settings_manager.save()
        
        # Shutdown scheduler
        self._stream_scheduler.shutdown()
        
        event.accept()
