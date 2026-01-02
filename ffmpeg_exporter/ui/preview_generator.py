"""
Preview Generator - Background thread for spectrum preview generation.
"""
from PySide6.QtCore import QThread, Signal
from core.ffmpeg_builder import FFmpegBuilder, ExportSettings, EncodingMethod
from core.media_manager import MediaConfig, LoopMode
import subprocess
import tempfile
import os


class PreviewGenerator(QThread):
    """Background thread for generating spectrum preview."""
    
    # Signals
    progress_update = Signal(str)  # Progress message
    preview_ready = Signal(str)  # Preview file path
    preview_failed = Signal(str)  # Error message
    
    def __init__(
        self,
        media_config: MediaConfig,
        ffmpeg_path: str,
        ffprobe_path: str,
        parent=None
    ):
        super().__init__(parent)
        self.media_config = media_config
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.temp_files = []
    
    def run(self):
        """Run preview generation in background."""
        error_log = []
        try:
            self.progress_update.emit("Preparing preview settings...")
            
            # Use FULL resolution for preview (same as export)
            # This ensures spectrum overlay positions are correct
            preview_settings = ExportSettings(
                width=1920,
                height=1080,
                fps=30,
                encoding_method=EncodingMethod.X264
            )
            
            # Create temp output file
            temp_output = tempfile.NamedTemporaryFile(suffix='_preview.mp4', delete=False)
            temp_output.close()
            preview_settings.output_directory = os.path.dirname(temp_output.name)
            preview_settings.output_filename = os.path.basename(temp_output.name)
            
            self.progress_update.emit("Building FFmpeg command...")
            
            # Build FFmpeg command (limit to 10 seconds)
            builder = FFmpegBuilder(self.ffmpeg_path, self.ffprobe_path)
            
            # Modify config for 10-second preview
            self.media_config.loop_mode = LoopMode.CUSTOM_DURATION
            self.media_config.custom_duration = 10.0  # 10 seconds only
            
            cmd, temp_files = builder.build_command(self.media_config, preview_settings)
            self.temp_files.extend(temp_files)
            
            # Log command for debugging
            print(f"\n{'='*60}")
            print("PREVIEW FFmpeg Command:")
            print(' '.join(cmd))
            print(f"{'='*60}\n")
            
            self.progress_update.emit("Rendering preview with spectrum...")
            
            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Read output line by line and collect errors
            for line in process.stdout:
                print(line.rstrip())  # Print to console for debugging
                error_log.append(line.rstrip())
                
                if "frame=" in line:
                    self.progress_update.emit("Encoding video...")
                elif "error" in line.lower() or "failed" in line.lower():
                    self.progress_update.emit(f"Warning: {line[:50]}...")
            
            process.wait()
            
            if process.returncode == 0:
                self.progress_update.emit("Preview ready!")
                self.preview_ready.emit(preview_settings.output_path)
            else:
                # Provide detailed error
                error_details = "\n".join(error_log[-20:])  # Last 20 lines
                self.preview_failed.emit(
                    f"FFmpeg encoding failed (code {process.returncode}).\n\n"
                    f"Last output:\n{error_details}"
                )
            
            # Cleanup temp files
            builder.cleanup_temp_files()
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.preview_failed.emit(f"Error: {str(e)}\n\nDetails:\n{error_trace}")

