"""
FFmpeg Builder - Constructs FFmpeg commands for video export.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.media_manager import MediaConfig, MediaMode, MediaManager, LoopMode, AudioSource, VisualizerStyle, BlendMode, VisualizerType
from core.audio_utils import AudioUtils
from core.spectrum_renderer import SpectrumRenderer
from core.audio_analyzer import AudioAnalyzer
from core.visualizer_renderer import VisualizerRenderer


class VideoCodec(Enum):
    """Video codec options."""
    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"


class EncodingMethod(Enum):
    """Encoding method/device options."""
    COPY = "copy"  # Stream copy (fastest, no re-encoding)
    NVENC = "nvenc"  # NVIDIA GPU Fast
    NVENC_HQ = "nvenc_hq"  # NVIDIA GPU High Quality
    X264 = "x264"  # CPU Standard
    X264_HQ = "x264_hq"  # CPU High Quality
    
    @classmethod
    def get_display_name(cls, method: 'EncodingMethod') -> str:
        """Get display name for encoding method."""
        names = {
            cls.COPY: "copy = Cepat (Stream Copy)",
            cls.NVENC: "nvenc = GPU NVIDIA Fast",
            cls.NVENC_HQ: "nvenc_hq = GPU NVIDIA High Quality (Anti-glitch)",
            cls.X264: "x264 = CPU Standard",
            cls.X264_HQ: "x264_hq = CPU High Quality (Anti-glitch, lambat)",
        }
        return names.get(method, method.value)
    
    @classmethod
    def get_all_display_names(cls) -> list:
        """Get all display names."""
        return [cls.get_display_name(m) for m in cls]


class AudioCodec(Enum):
    """Audio codec options."""
    AAC = "aac"
    MP3 = "libmp3lame"
    OPUS = "libopus"


class RateControl(Enum):
    """Rate control mode."""
    CRF = "crf"
    CBR = "cbr"
    VBR = "vbr"


@dataclass
class ExportSettings:
    """Export configuration settings."""
    # Resolution
    width: int = 1920
    height: int = 1080
    
    # Frame rate
    fps: int = 30
    
    # Encoding method (GPU/CPU)
    encoding_method: EncodingMethod = EncodingMethod.NVENC_HQ
    
    # Video encoding
    video_codec: VideoCodec = VideoCodec.H264
    rate_control: RateControl = RateControl.CRF
    crf_value: int = 23  # Lower = higher quality
    bitrate_kbps: int = 4000  # Default bitrate (kbps)
    
    # Audio encoding
    audio_codec: AudioCodec = AudioCodec.AAC
    audio_bitrate_kbps: int = 192
    
    # Output
    output_filename: str = "output.mp4"
    output_directory: str = ""
    
    @property
    def resolution(self) -> str:
        """Get resolution string."""
        return f"{self.width}x{self.height}"
    
    @property
    def output_path(self) -> str:
        """Get full output path."""
        return os.path.join(self.output_directory, self.output_filename)


class FFmpegBuilder:
    """Builds FFmpeg commands for video export."""
    
    # Windows command line length limit is ~8191 characters
    MAX_COMMAND_LENGTH = 7000  # Use 7000 to be safe
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize FFmpeg builder.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable.
            ffprobe_path: Path to FFprobe executable.
        """
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._audio_utils = AudioUtils(ffprobe_path)
        self._media_manager = MediaManager()
        self._temp_files: List[str] = []
        
        # NEW: Visualizer support (Astrofox-style)
        self._audio_analyzer = AudioAnalyzer(ffmpeg_path, ffprobe_path)
        self._visualizer_renderer = VisualizerRenderer()
    
    @property
    def ffmpeg_path(self) -> str:
        """Get FFmpeg path."""
        return self._ffmpeg_path
    
    @ffmpeg_path.setter
    def ffmpeg_path(self, path: str) -> None:
        """Set FFmpeg path."""
        self._ffmpeg_path = path
    
    @property
    def ffprobe_path(self) -> str:
        """Get FFprobe path."""
        return self._ffprobe_path
    
    @ffprobe_path.setter
    def ffprobe_path(self, path: str) -> None:
        """Set FFprobe path."""
        self._ffprobe_path = path
        self._audio_utils.ffprobe_path = path
    
    def build_command(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> Tuple[List[str], List[str]]:
        """
        Build FFmpeg command based on configuration.
        
        Args:
            media_config: Media configuration.
            export_settings: Export settings.
            
        Returns:
            Tuple of (command list, list of temp files to cleanup).
        """
        self._temp_files = []
        
        if media_config.mode == MediaMode.STATIC_IMAGE:
            cmd = self._build_image_mode_command(media_config, export_settings)
        else:
            cmd = self._build_video_mode_command(media_config, export_settings)
        
        return cmd, self._temp_files
    
    def _build_image_mode_command(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> List[str]:
        """Build command for static image mode."""
        # Get audio source (can be None for VIDEO_AUDIO mode - but doesn't make sense for static image)
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            raise ValueError("VIDEO_AUDIO mode not supported for static image mode. Please select audio files.")
        
        audio_source, audio_duration = self._get_audio_source(media_config)
        
        # Calculate target duration based on loop mode
        target_duration = self._get_target_duration(media_config, audio_duration)
        
        cmd = [self._ffmpeg_path, '-y']
        
        # Input 0: looped image
        cmd.extend(['-loop', '1', '-i', media_config.static_image])
        
        # Track input indices
        next_input_idx = 1
        audio_input_idx = None
        
        # Input 1: audio (if using AUDIO_DIRECTORY or MIX_BOTH - but MIX doesn't make sense for image)
        if audio_source is not None:
            is_audio_concat = audio_source.endswith('.txt')
            if is_audio_concat:
                cmd.extend(['-f', 'concat', '-safe', '0', '-i', audio_source])
            else:
                cmd.extend(['-i', audio_source])
            audio_input_idx = next_input_idx
            next_input_idx += 1
        
        # Generate custom spectrum video if enabled
        spectrum_input_idx = None
        if media_config.audio_visualizer.enabled and media_config.audio_visualizer.style == VisualizerStyle.CUSTOM_BARS:
            spectrum_video = self._generate_custom_spectrum(
                audio_source,
                media_config,
                target_duration
            )
            if spectrum_video:
                # Add spectrum video as input with loop
                cmd.extend(['-stream_loop', '-1', '-i', spectrum_video])
                spectrum_input_idx = next_input_idx
                next_input_idx += 1
        
        # TODO: NEW Visualizer (Astrofox-style) - For full export integration
        # Generate visualizer video if enabled
        visualizer_input_idx = None
        if media_config.visualizer.type != VisualizerType.NONE:
            from core.visualizer_preview import VisualizerPreviewGenerator
            import tempfile
            
            # Generate visualizer video for full duration
            visualizer_generator = VisualizerPreviewGenerator(self._ffmpeg_path)
            
            # Create temp output file
            temp_viz_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_viz_video.close()
            self._temp_files.append(temp_viz_video.name)
            
            print(f"Generating visualizer video for export (duration: {target_duration}s)...")
            
            success = visualizer_generator.generate_preview(
                audio_files=media_config.audio_files if media_config.audio_files else [],
                visualizer_config=media_config.visualizer,
                output_file=temp_viz_video.name,
                duration=target_duration,
                fps=export_settings.fps,
                width=export_settings.width,
                height=export_settings.height,
                background_color="#00000000",  # Transparent background
                progress_callback=None
            )
            
            if success:
                # Add visualizer video as input with loop
                cmd.extend(['-stream_loop', '-1', '-i', temp_viz_video.name])
                visualizer_input_idx = next_input_idx
                next_input_idx += 1
                print(f"Visualizer video generated successfully")
            else:
                print("Failed to generate visualizer video")
        
        # Input: SFX if enabled
        sfx_input_idx = None
        if media_config.sfx_enabled and media_config.sfx_file and media_config.beat_times:
            cmd.extend(['-i', media_config.sfx_file])
            sfx_input_idx = next_input_idx
            next_input_idx += 1
        
        # Input: Audio layers (sound effects)
        audio_layer_indices = []
        if media_config.audio_layers:
            for layer_config in media_config.audio_layers:
                if layer_config.enabled and layer_config.file_path:
                    cmd.extend(['-i', layer_config.file_path])
                    audio_layer_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Input: Advanced overlays (blend modes + chroma key)
        overlay_input_indices = []
        if media_config.overlays:
            for overlay_config in media_config.overlays:
                if overlay_config.enabled and overlay_config.filepath:
                    # Apply input looping if configured
                    if overlay_config.loop:
                        cmd.extend(['-stream_loop', '-1'])
                        
                    cmd.extend(['-i', overlay_config.filepath])
                    overlay_input_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Build audio filter (for static image, only AUDIO_DIRECTORY makes sense)
        audio_filter, audio_map = self._build_audio_filter(
            media_config,
            video_input_idx=0,  # Image is input 0, but it doesn't have audio
            audio_input_idx=audio_input_idx,
            audio_layer_indices=audio_layer_indices
        )
        
        # Determine audio stream reference for visualizer
        # For static image, audio is at input 1 (after image at 0)
        if audio_input_idx is not None:
            audio_stream_ref = f"{audio_input_idx}:a"
        else:
            audio_stream_ref = "0:a"
        
        # Build filter complex (including visualizer)
        filter_complex = self._build_filter_complex(
            media_config, export_settings,
            input_is_image=True,
            audio_stream_ref=audio_stream_ref,
            spectrum_input_idx=spectrum_input_idx,
            visualizer_input_idx=visualizer_input_idx,
            chroma_key_input_indices=overlay_input_indices if overlay_input_indices else None,
            target_duration=target_duration
        )
        
        # Build SFX filter if enabled
        sfx_filter = ""
        if sfx_input_idx is not None and audio_input_idx is not None:
            sfx_filter = self._create_sfx_filter(media_config, audio_input_idx, sfx_input_idx)
            if sfx_filter:
                audio_map = "[aout]"
        
        # Combine all filters
        all_filters = []
        if filter_complex:
            all_filters.append(filter_complex)
        if audio_filter:
            all_filters.append(audio_filter)
        if sfx_filter:
            all_filters.append(sfx_filter)
        
        if all_filters:
            self._add_filter_complex(cmd, ";".join(all_filters))
            cmd.extend(['-map', '[vout]', '-map', audio_map])
        elif filter_complex:
            self._add_filter_complex(cmd, filter_complex)
            cmd.extend(['-map', '[vout]', '-map', audio_map])
        else:
            # Simple scale filter
            cmd.extend([
                '-vf', f"scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2"
            ])
            cmd.extend(['-map', '0:v', '-map', audio_map])
        
        # Duration
        cmd.extend(['-t', str(target_duration)])
        
        # Add encoding options
        cmd.extend(self._get_encoding_options(export_settings))
        
        # Output
        cmd.append(export_settings.output_path)
        
        return cmd
    
    def _build_video_mode_command(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> List[str]:
        """Build command for video directory mode."""
        # Check if transitions are enabled
        use_transitions = (
            media_config.transition_enabled and 
            len(media_config.video_files) > 1
        )
        
        if use_transitions:
            # Use xfade transition method
            return self._build_video_with_transitions(media_config, export_settings)
        else:
            # Use traditional concat method
            return self._build_video_traditional_concat(media_config, export_settings)
    
    def _build_video_traditional_concat(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> List[str]:
        """Build command for video directory mode (traditional concat method)."""
        # Get audio source (can be None for VIDEO_AUDIO mode)
        audio_source, audio_duration = self._get_audio_source(media_config)
        
        # Calculate target duration based on loop mode
        # For VIDEO_AUDIO mode, we need to calculate from video duration
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            # Use video duration as reference
            video_files = media_config.video_files
            if video_files:
                audio_duration = self._audio_utils.get_duration(video_files[0]) or 60.0
            else:
                audio_duration = 60.0  # Default fallback
        
        target_duration = self._get_target_duration(media_config, audio_duration)
        
        # Get video files
        videos = self._media_manager.get_ordered_video_list(
            media_config.video_files,
            media_config.cover_video if media_config.cover_video else None
        )
        
        if not videos:
            raise ValueError("No video files selected")
        
        # Create concat file for videos
        has_cover = bool(media_config.cover_video)
        concat_file = self._create_concat_file(videos, target_duration, loop=True, has_cover=has_cover)
        
        cmd = [self._ffmpeg_path, '-y']
        
        # Input 0: video concat file
        cmd.extend(['-f', 'concat', '-safe', '0', '-i', concat_file])
        
        # Track input indices
        next_input_idx = 1
        audio_input_idx = None
        
        # Input 1: audio (if using AUDIO_DIRECTORY or MIX_BOTH)
        if audio_source is not None:
            is_audio_concat = audio_source.endswith('.txt')
            if is_audio_concat:
                cmd.extend(['-f', 'concat', '-safe', '0', '-i', audio_source])
            else:
                cmd.extend(['-i', audio_source])
            audio_input_idx = next_input_idx
            next_input_idx += 1
        
        # Generate custom spectrum video if enabled
        spectrum_input_idx = None
        if media_config.audio_visualizer.enabled and media_config.audio_visualizer.style == VisualizerStyle.CUSTOM_BARS:
            # Determine which audio to analyze
            spectrum_audio_source = audio_source if audio_source else (videos[0] if videos else None)
            if spectrum_audio_source:
                spectrum_video = self._generate_custom_spectrum(
                    spectrum_audio_source,
                    media_config,
                    target_duration
                )
                if spectrum_video:
                    # Add spectrum video as input with loop
                    cmd.extend(['-stream_loop', '-1', '-i', spectrum_video])
                    spectrum_input_idx = next_input_idx
                    next_input_idx += 1
        
        # NEW: Generate Astrofox visualizer video if enabled
        visualizer_input_idx = None
        if media_config.visualizer.type != VisualizerType.NONE:
            from core.visualizer_preview import VisualizerPreviewGenerator
            import tempfile
            
            # Generate visualizer video for full duration
            visualizer_generator = VisualizerPreviewGenerator(self._ffmpeg_path)
            
            # Create temp output file
            temp_viz_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_viz_video.close()
            self._temp_files.append(temp_viz_video.name)
            
            print(f"Generating visualizer video for export (duration: {target_duration}s)...")
            
            success = visualizer_generator.generate_preview(
                audio_files=media_config.audio_files if media_config.audio_files else [],
                visualizer_config=media_config.visualizer,
                output_file=temp_viz_video.name,
                duration=target_duration,
                fps=export_settings.fps,
                width=export_settings.width,
                height=export_settings.height,
                background_color="#00000000",  # Transparent background
                progress_callback=None
            )
            
            if success:
                # Add visualizer video as input with loop
                cmd.extend(['-stream_loop', '-1', '-i', temp_viz_video.name])
                visualizer_input_idx = next_input_idx
                next_input_idx += 1
                print(f"Visualizer video generated successfully")
            else:
                print("Failed to generate visualizer video")
        
        # Input: logo if enabled
        logo_input_idx = None
        if media_config.logo_overlay.enabled and media_config.logo_overlay.filepath:
            cmd.extend(['-i', media_config.logo_overlay.filepath])
            logo_input_idx = next_input_idx
            next_input_idx += 1
        
        # Input: SFX if enabled
        sfx_input_idx = None
        if media_config.sfx_enabled and media_config.sfx_file and media_config.beat_times:
            cmd.extend(['-i', media_config.sfx_file])
            sfx_input_idx = next_input_idx
            next_input_idx += 1
        
        # Input: Audio layers (sound effects)
        audio_layer_indices = []
        if media_config.audio_layers:
            for layer_config in media_config.audio_layers:
                if layer_config.enabled and layer_config.file_path:
                    cmd.extend(['-i', layer_config.file_path])
                    audio_layer_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Input: Advanced overlays (blend modes + chroma key)
        overlay_input_indices = []
        if media_config.overlays:
            for overlay_config in media_config.overlays:
                if overlay_config.enabled and overlay_config.filepath:
                    # Apply input looping if configured
                    if overlay_config.loop:
                        cmd.extend(['-stream_loop', '-1'])
                        
                    cmd.extend(['-i', overlay_config.filepath])
                    overlay_input_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Build audio filter based on audio source mode
        audio_filter, audio_map = self._build_audio_filter(
            media_config, 
            video_input_idx=0,
            audio_input_idx=audio_input_idx,
            audio_layer_indices=audio_layer_indices
        )
        
        # Determine audio stream reference for visualizer
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            audio_stream_ref = "0:a"
        elif media_config.audio_source == AudioSource.AUDIO_DIRECTORY and audio_input_idx is not None:
            audio_stream_ref = f"{audio_input_idx}:a"
        elif media_config.audio_source == AudioSource.MIX_BOTH:
            # Use the mixed audio output
            audio_stream_ref = "[aout]" if audio_filter else "0:a"
        else:
            audio_stream_ref = "0:a"
        
        # Build video filter complex (including visualizer)
        filter_complex = self._build_filter_complex(
            media_config, export_settings,
            input_is_image=False,
            logo_input_idx=logo_input_idx,
            audio_stream_ref=audio_stream_ref,
            spectrum_input_idx=spectrum_input_idx,
            visualizer_input_idx=visualizer_input_idx,
            chroma_key_input_indices=overlay_input_indices if overlay_input_indices else None,
            target_duration=target_duration
        )
        
        # Build SFX filter if enabled (needs to work with audio filter)
        sfx_filter = ""
        if sfx_input_idx is not None:
            # For SFX, we need to use the audio that's been selected/mixed
            # This is complex - for now, skip SFX if using MIX_BOTH
            if media_config.audio_source != AudioSource.MIX_BOTH and audio_input_idx is not None:
                sfx_filter = self._create_sfx_filter(media_config, audio_input_idx, sfx_input_idx)
                if sfx_filter:
                    audio_map = "[aout]"
        
        # Combine all filters
        all_filters = []
        if filter_complex:
            all_filters.append(filter_complex)
        if audio_filter:
            all_filters.append(audio_filter)
        if sfx_filter:
            all_filters.append(sfx_filter)
        
        if all_filters:
            self._add_filter_complex(cmd, ";".join(all_filters))
            cmd.extend(['-map', '[vout]', '-map', audio_map])
        else:
            # Simple scale + audio mapping
            cmd.extend([
                '-vf', f"scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2"
            ])
            cmd.extend(['-map', '0:v', '-map', audio_map])
        
        # Duration
        cmd.extend(['-t', str(target_duration)])
        
        # Shortest
        cmd.extend(['-shortest'])
        
        # Add encoding options
        cmd.extend(self._get_encoding_options(export_settings))
        
        # Output
        cmd.append(export_settings.output_path)
        
        return cmd
    
    def _build_filter_complex(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings,
        input_is_image: bool = False,
        logo_input_idx: Optional[int] = None,
        audio_stream_ref: str = "0:a",
        spectrum_input_idx: Optional[int] = None,
        visualizer_input_idx: Optional[int] = None,
        chroma_key_input_indices: Optional[List[int]] = None,
        target_duration: float = 0.0
    ) -> str:
        """Build filter_complex string."""
        filters = []
        current_output = "[0:v]"
        
        # Apply video scale/zoom first (for watermark removal)
        if media_config.video_scale_enabled and media_config.video_scale_percent > 100:
            zoom_factor = media_config.video_scale_percent / 100.0
            # Method: Scale up then crop back to original size (center crop)
            # This effectively zooms in and removes edges (watermarks)
            scale_zoom = f"{current_output}scale=iw*{zoom_factor}:ih*{zoom_factor},crop=iw/{zoom_factor}:ih/{zoom_factor}[zoomed]"
            filters.append(scale_zoom)
            current_output = "[zoomed]"
        
        # Scale to target resolution
        scale_filter = f"{current_output}scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2,fps={export_settings.fps}[scaled]"
        filters.append(scale_filter)
        current_output = "[scaled]"
        
        # Add logo overlay if enabled
        if media_config.logo_overlay.enabled and media_config.logo_overlay.filepath and logo_input_idx is not None:
            logo_scale = media_config.logo_overlay.get_scale_filter(export_settings.width)
            logo_overlay = media_config.logo_overlay.get_overlay_filter(
                export_settings.width, export_settings.height
            )
            
            filters.append(f"[{logo_input_idx}:v]{logo_scale}[logo]")
            filters.append(f"{current_output}[logo]{logo_overlay}[withlogo]")
            current_output = "[withlogo]"
        elif media_config.logo_overlay.enabled and media_config.logo_overlay.filepath and input_is_image:
            # For image mode, logo is input 2 (after image at 0 and audio at 1)
            # But we need to add it as a separate input - handled differently
            pass
        
        # Add text overlay if enabled (legacy single text)
        if media_config.text_overlay.enabled and media_config.text_overlay.text:
            drawtext = media_config.text_overlay.get_drawtext_filter(
                export_settings.width, export_settings.height
            )
            filters.append(f"{current_output}{drawtext}[withtext]")
            current_output = "[withtext]"
        
        # Add animated text timeline (multi-text with timing)
        if media_config.animated_text_timeline.enabled:
            text_filters = media_config.animated_text_timeline.get_all_filters()
            for idx, text_filter in enumerate(text_filters):
                filters.append(f"{current_output}{text_filter}[text{idx}]")
                current_output = f"[text{idx}]"
        
        # Add subtitle/lyrics from SRT files
        if media_config.subtitle_config.enabled and media_config.audio_files:
            # Find SRT files for each audio
            srt_files = []
            for audio_file in media_config.audio_files:
                srt_path = self._find_srt_for_audio(audio_file)
                if srt_path:
                    srt_files.append(srt_path)
                    print(f"✓ Found SRT: {srt_path}")
                else:
                    print(f"✗ No SRT for: {audio_file}")
            
            print(f"\nTotal SRT files found: {len(srt_files)} / {len(media_config.audio_files)}")
            
            if srt_files:
                subtitle_filter = self._build_subtitle_filter(media_config, srt_files)
                if subtitle_filter:
                    print(f"Subtitle filter: {subtitle_filter[:100]}...")
                    filters.append(f"{current_output}{subtitle_filter}[withsub]")
                    current_output = "[withsub]"
                else:
                    print("Warning: Subtitle filter is empty!")
            else:
                print("Warning: No SRT files found, subtitle disabled")
        
        # Add audio visualizer if enabled
        if media_config.audio_visualizer.enabled:
            # Check if custom spectrum video input exists
            if spectrum_input_idx is not None and media_config.audio_visualizer.style == VisualizerStyle.CUSTOM_BARS:
                # Overlay custom spectrum video
                viz_overlay = media_config.audio_visualizer.get_overlay_position()
                filters.append(f"{current_output}[{spectrum_input_idx}:v]{viz_overlay}[withviz]")
                current_output = "[withviz]"
            else:
                # Use FFmpeg built-in visualizer filters
                viz_filter = media_config.audio_visualizer.get_visualizer_filter(audio_stream_ref)
                if viz_filter:
                    filters.append(viz_filter)
                    
                    # Overlay visualizer on video
                    viz_overlay = media_config.audio_visualizer.get_overlay_position()
                    filters.append(f"{current_output}[viz]{viz_overlay}[withviz]")
                    current_output = "[withviz]"
        
        # Add chroma key overlays
        if chroma_key_input_indices and media_config.overlays:
            for idx, (overlay_config, input_idx) in enumerate(zip(media_config.overlays, chroma_key_input_indices)):
                if overlay_config.enabled and overlay_config.filepath:
                    input_stream = f"[{input_idx}:v]"
                    
                    # Always apply trim to target duration if it's set
                    # This ensures overlay respects the project duration (cuts if too long)
                    if target_duration > 0:
                        filters.append(f"{input_stream}trim=duration={target_duration}:start=0,setpts=PTS-STARTPTS[ck{idx}_trimmed]")
                        input_stream = f"[ck{idx}_trimmed]"
                    
                    # Scale overlay
                    overlay_scale = overlay_config.get_scale_filter(export_settings.width)
                    filters.append(f"{input_stream}{overlay_scale}[ck{idx}_scaled]")
                    
                    current_overlay = f"[ck{idx}_scaled]"
                    
                    # Apply chroma key (colorkey filter) if enabled
                    if overlay_config.chroma_key_enabled:
                        chromakey_filter = overlay_config.get_chromakey_filter()
                        if chromakey_filter:
                            filters.append(f"{current_overlay}{chromakey_filter}[ck{idx}_keyed]")
                            current_overlay = f"[ck{idx}_keyed]"
                    
                    # Apply opacity if < 1.0 (using colorchannelmixer to adjust alpha)
                    if overlay_config.opacity < 1.0:
                        opacity_val = overlay_config.opacity
                        filters.append(f"{current_overlay}format=yuva420p,colorchannelmixer=aa={opacity_val}[ck{idx}_alpha]")
                        current_overlay = f"[ck{idx}_alpha]"
                    
                    # Apply blend mode if not NORMAL
                    if overlay_config.blend_mode != BlendMode.NORMAL:
                        blend_mode = overlay_config.blend_mode.value
                        
                        # For blend mode with positioning:
                        # 1. Create a transparent canvas matching video size
                        # 2. Overlay the scaled overlay onto canvas at desired position
                        # 3. Blend the canvas with the video
                        
                        # Get position coordinates
                        overlay_pos = overlay_config.get_overlay_filter(export_settings.width, export_settings.height)
                        
                        # Create transparent canvas and overlay positioned content
                        filters.append(f"color=c=black@0.0:s={export_settings.width}x{export_settings.height}:d={target_duration}[canvas{idx}]")
                        filters.append(f"[canvas{idx}]{current_overlay}{overlay_pos}[positioned{idx}]")
                        
                        # Now blend with video
                        filters.append(f"{current_output}[positioned{idx}]blend=all_mode={blend_mode}[ck{idx}]")
                        current_output = f"[ck{idx}]"
                    else:
                        # Normal overlay (with position)
                        overlay_pos = overlay_config.get_overlay_filter(export_settings.width, export_settings.height)
                        filters.append(f"{current_output}{current_overlay}{overlay_pos}[ck{idx}]")
                        current_output = f"[ck{idx}]"
        
        # NEW: Add Astrofox visualizer overlay (LAST - so it's on top)
        if visualizer_input_idx is not None:
            # Overlay visualizer video (already rendered with correct size and transparency)
            filters.append(f"{current_output}[{visualizer_input_idx}:v]overlay=0:0[withviz]")
            current_output = "[withviz]"
        
        # Final output
        if filters:
            # Replace last output label with [vout]
            last_filter = filters[-1]
            last_bracket = last_filter.rfind('[')
            if last_bracket != -1:
                filters[-1] = last_filter[:last_bracket] + "[vout]"
            
            return ";".join(filters)
        
        return ""
    
    def _find_srt_for_audio(self, audio_path: str) -> Optional[str]:
        """
        Find SRT file with same name as audio file.
        
        Args:
            audio_path: Path to audio file (or concat file)
            
        Returns:
            Path to SRT file if found, None otherwise.
        """
        # If audio_path is a concat file, skip
        if audio_path.endswith('.txt'):
            return None
        
        audio_file = Path(audio_path)
        srt_path = audio_file.with_suffix('.srt')
        
        if srt_path.exists():
            return str(srt_path)
        
        return None
    
    def _build_subtitle_filter(self, media_config: MediaConfig, srt_files: List[str]) -> str:
        """
        Build FFmpeg subtitle filter for multiple SRT files.
        
        Args:
            media_config: Media configuration with subtitle settings.
            srt_files: List of SRT file paths (in order, matching audio files).
            
        Returns:
            FFmpeg subtitles filter string, or empty if no subtitles.
        """
        if not media_config.subtitle_config.enabled or not srt_files:
            return ""
        
        sub_config = media_config.subtitle_config
        
        # Build force_style parameter for subtitle styling
        # FFmpeg color format: &HBBGGRR& (BGR, not RGB!)
        def color_to_ffmpeg(color_str: str) -> str:
            """Convert color name/hex to FFmpeg format."""
            # Try to parse as hex first
            if color_str.startswith('#'):
                hex_color = color_str.lstrip('#')
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return f"&H{b:02X}{g:02X}{r:02X}&"
            
            # Named colors to FFmpeg format
            color_map = {
                'white': '&HFFFFFF&',
                'black': '&H000000&',
                'red': '&H0000FF&',
                'green': '&H00FF00&',
                'blue': '&HFF0000&',
                'yellow': '&H00FFFF&',
            }
            return color_map.get(color_str.lower(), '&HFFFFFF&')
        
        font_color = color_to_ffmpeg(sub_config.font_color)
        outline_color = color_to_ffmpeg(sub_config.outline_color)
        
        # Build force_style string
        force_style_parts = [
            f"FontSize={sub_config.font_size}",
            f"PrimaryColour={font_color}",
            f"OutlineColour={outline_color}",
            f"Outline={sub_config.outline_width}",
            f"Alignment={sub_config.alignment}",
            f"MarginV={sub_config.margin_v}",
        ]
        
        if sub_config.font_file and os.path.isfile(sub_config.font_file):
            font_name = Path(sub_config.font_file).stem
            force_style_parts.insert(0, f"FontName={font_name}")
        
        force_style = ','.join(force_style_parts)
        
        # For multiple SRT files, we'll concatenate them into one temp file
        # with adjusted timings
        if len(srt_files) > 1:
            # Create merged SRT with adjusted timings
            merged_srt = self._merge_srt_files(srt_files, media_config)
            if merged_srt:
                srt_to_use = merged_srt
            else:
                # If merge failed, use first SRT only
                srt_to_use = srt_files[0]
        else:
            srt_to_use = srt_files[0]
        
        # Escape path for FFmpeg (Windows paths)
        escaped_path = str(srt_to_use).replace('\\', '/').replace(':', '\\:')
        
        # Build subtitles filter
        subtitle_filter = f"subtitles='{escaped_path}':force_style='{force_style}'"
        
        return subtitle_filter
    
    def _merge_srt_files(self, srt_files: List[str], media_config: MediaConfig) -> Optional[str]:
        """
        Merge multiple SRT files into one with adjusted timings.
        Each SRT file corresponds to one audio file in sequence.
        
        Args:
            srt_files: List of SRT file paths.
            media_config: Media configuration.
            
        Returns:
            Path to merged SRT file, or None if failed.
        """
        try:
            # Calculate cumulative offsets based on audio file durations
            audio_files = media_config.audio_files
            if len(audio_files) != len(srt_files):
                # Mismatch - cannot merge properly
                return None
            
            cumulative_offset = 0.0
            merged_content = []
            subtitle_index = 1
            
            for audio_file, srt_file in zip(audio_files, srt_files):
                # Get audio duration
                audio_duration = self._audio_utils.get_duration(audio_file)
                if not audio_duration:
                    audio_duration = 180.0  # Default 3 minutes
                
                # Read SRT file
                if not os.path.exists(srt_file):
                    cumulative_offset += audio_duration
                    continue
                
                with open(srt_file, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                
                # Parse SRT and adjust timings
                import re
                
                # SRT format:
                # 1
                # 00:00:10,500 --> 00:00:13,000
                # Text here
                
                pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
                
                def adjust_timestamp(timestamp: str, offset_seconds: float) -> str:
                    """Adjust SRT timestamp by offset."""
                    # Parse: HH:MM:SS,mmm
                    parts = timestamp.split(',')
                    time_parts = parts[0].split(':')
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    milliseconds = int(parts[1])
                    
                    # Convert to total seconds
                    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
                    
                    # Add offset
                    total_seconds += offset_seconds
                    
                    # Convert back
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    milliseconds = int((total_seconds % 1) * 1000)
                    
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                
                for match in re.finditer(pattern, srt_content, re.DOTALL):
                    start_time = adjust_timestamp(match.group(2), cumulative_offset)
                    end_time = adjust_timestamp(match.group(3), cumulative_offset)
                    text = match.group(4).strip()
                    
                    merged_content.append(f"{subtitle_index}\n{start_time} --> {end_time}\n{text}\n\n")
                    subtitle_index += 1
                
                # Update offset for next audio
                cumulative_offset += audio_duration
            
            if not merged_content:
                return None
            
            # Write merged SRT to temp file
            temp_srt = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.srt',
                delete=False,
                encoding='utf-8'
            )
            temp_srt.write(''.join(merged_content))
            temp_srt.close()
            
            self._temp_files.append(temp_srt.name)
            return temp_srt.name
            
        except Exception as e:
            print(f"Warning: Failed to merge SRT files: {e}")
            return None
    
    def _get_audio_source(self, media_config: MediaConfig) -> Tuple[str, float]:
        """
        Get audio source for export based on audio_source mode.
        
        Returns:
            Tuple of (audio file path or concat file, SINGLE PASS duration).
            Returns None, 0.0 if using VIDEO_AUDIO mode.
        """
        # If using video audio only, return None
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            # We'll use audio from video, duration doesn't matter for this
            return None, 0.0
        
        audio_files = media_config.audio_files
        
        # For AUDIO_DIRECTORY and MIX_BOTH, we need audio files
        if not audio_files and media_config.audio_source != AudioSource.VIDEO_AUDIO:
            raise ValueError("No audio files selected")
        
        # Calculate single pass audio duration (without looping)
        single_pass_duration = 0.0
        for filepath in audio_files:
            duration = self._audio_utils.get_duration(filepath)
            if duration:
                single_pass_duration += duration
        
        if single_pass_duration <= 0 and media_config.audio_source != AudioSource.VIDEO_AUDIO:
            raise ValueError("Could not determine audio duration")
        
        # Determine how many times to loop audio based on loop mode
        loop_count = 1
        if media_config.loop_mode == LoopMode.MULTIPLY_AUDIO:
            loop_count = media_config.audio_multiplier
        
        # If only one audio file and no looping needed, return it directly
        if len(audio_files) == 1 and loop_count == 1:
            return audio_files[0], single_pass_duration
        
        # Step 1: If multiple audio files, merge them into one first
        if len(audio_files) > 1:
            merged_audio = self._merge_audio_files(audio_files)
        else:
            merged_audio = audio_files[0]
        
        # Step 2: If looping is needed, create concat file for the merged audio
        if loop_count > 1:
            looped_audio = self._create_looped_audio_concat(merged_audio, loop_count)
            return looped_audio, single_pass_duration
        
        # Return merged audio (no looping needed)
        return merged_audio, single_pass_duration
    
    def _build_audio_filter(
        self,
        media_config: MediaConfig,
        video_input_idx: int,
        audio_input_idx: Optional[int],
        audio_layer_indices: List[int] = []
    ) -> Tuple[str, str]:
        """
        Build audio filter based on audio source mode, including multi-layer audio support.
        
        Args:
            media_config: Media configuration
            video_input_idx: Index of video input
            audio_input_idx: Index of audio directory input (can be None for VIDEO_AUDIO mode)
            audio_layer_indices: List of indices for audio layer inputs (sound effects)
            
        Returns:
            Tuple of (filter_string, audio_map_output)
            - filter_string: FFmpeg filter to add to filter_complex (empty if no filter needed)
            - audio_map_output: What to map for audio (e.g., "1:a", "[aout]")
        """
        # First, get base audio
        base_filter, base_ref = self._build_base_audio_filter(
            media_config, video_input_idx, audio_input_idx
        )
        
        # If no audio layers, return base audio
        if not audio_layer_indices or not media_config.audio_layers:
            return base_filter, base_ref
        
        # Build multi-layer audio mix
        filters = []
        if base_filter:
            filters.append(base_filter)
        
        # Process each audio layer
        inputs_for_mix = [base_ref if base_ref.startswith('[') else f'[{base_ref}]']
        
        for idx, (layer_idx, layer_config) in enumerate(zip(audio_layer_indices, media_config.audio_layers)):
            if not layer_config.enabled:
                continue
            
            layer_label = f"sfx{idx}"
            layer_filters = []
            
            # Start with layer input
            current_ref = f"{layer_idx}:a"
            
            # Apply delay if needed
            if layer_config.delay_seconds > 0:
                delay_filter = f"[{current_ref}]adelay={int(layer_config.delay_seconds * 1000)}[{layer_label}_delay]"
                layer_filters.append(delay_filter)
                current_ref = f"{layer_label}_delay"
            
            # Apply fade in
            if layer_config.fade_in > 0:
                fade_in_filter = f"[{current_ref}]afade=t=in:st=0:d={layer_config.fade_in}[{layer_label}_fin]"
                layer_filters.append(fade_in_filter)
                current_ref = f"{layer_label}_fin"
            
            # Apply fade out (if needed)
            if layer_config.fade_out > 0:
                # Note: fade out timing depends on total duration, applied later in full pipeline
                pass
            
            # Apply volume
            vol_filter = f"[{current_ref}]volume={layer_config.volume}[{layer_label}_vol]"
            layer_filters.append(vol_filter)
            current_ref = f"{layer_label}_vol"
            
            # Apply loop if needed
            if layer_config.loop:
                loop_filter = f"[{current_ref}]aloop=loop=-1:size=2e+09[{layer_label}_loop]"
                layer_filters.append(loop_filter)
                current_ref = f"{layer_label}_loop"
            
            filters.extend(layer_filters)
            inputs_for_mix.append(f"[{current_ref}]")
        
        # Mix all audio inputs
        num_inputs = len(inputs_for_mix)
        if num_inputs > 1:
            mix_filter = f"{''.join(inputs_for_mix)}amix=inputs={num_inputs}:duration=first:normalize=0[aout]"
            filters.append(mix_filter)
            return ";".join(filters), "[aout]"
        else:
            # Only base audio, no mixing needed
            return base_filter, base_ref
    
    def _build_base_audio_filter(
        self,
        media_config: MediaConfig,
        video_input_idx: int,
        audio_input_idx: Optional[int]
    ) -> Tuple[str, str]:
        """
        Build base audio filter (without layers) based on audio source mode.
        
        Returns:
            Tuple of (filter_string, audio_map_output)
        """
        audio_source = media_config.audio_source
        
        if audio_source == AudioSource.VIDEO_AUDIO:
            # Use audio from video only
            return "", f"{video_input_idx}:a"
        
        elif audio_source == AudioSource.AUDIO_DIRECTORY:
            # Use audio from audio directory only (replace video audio)
            if audio_input_idx is None:
                raise ValueError("Audio input index required for AUDIO_DIRECTORY mode")
            return "", f"{audio_input_idx}:a"
        
        elif audio_source == AudioSource.MIX_BOTH:
            # Mix video audio + background music
            if audio_input_idx is None:
                raise ValueError("Audio input index required for MIX_BOTH mode")
            
            video_vol = media_config.audio_mix_video_volume
            music_vol = media_config.audio_mix_music_volume
            
            # Create amix filter
            filter_str = (
                f"[{video_input_idx}:a]volume={video_vol}[va];"
                f"[{audio_input_idx}:a]volume={music_vol}[ma];"
                f"[va][ma]amix=inputs=2:duration=first:normalize=0[aout]"
            )
            return filter_str, "[aout]"
        
        # Default: use audio directory
        return "", f"{audio_input_idx}:a" if audio_input_idx is not None else f"{video_input_idx}:a"
    
    def _merge_audio_files(self, audio_files: List[str]) -> str:
        """
        Merge multiple audio files into one temporary file using FFmpeg.
        Uses filter_complex concat to handle different audio formats properly.
        """
        # Create temp output file
        temp_output = tempfile.NamedTemporaryFile(
            suffix='.mp3',
            delete=False
        )
        temp_output.close()
        self._temp_files.append(temp_output.name)
        
        # Build FFmpeg command with filter_complex for proper merging
        cmd = [self._ffmpeg_path, '-y']
        
        # Add all input files
        for filepath in audio_files:
            cmd.extend(['-i', filepath])
        
        # Build concat filter - handles different formats/sample rates
        n = len(audio_files)
        filter_inputs = ''.join([f'[{i}:a]' for i in range(n)])
        filter_str = f'{filter_inputs}concat=n={n}:v=0:a=1[aout]'
        
        self._add_filter_complex(cmd, filter_str)
        cmd.extend(['-map', '[aout]'])
        cmd.extend(['-c:a', 'libmp3lame', '-q:a', '2'])  # Good quality MP3
        cmd.append(temp_output.name)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise ValueError(f"Failed to merge audio files: {error_msg}")
        
        return temp_output.name
    
    def _create_looped_audio_concat(self, audio_file: str, loop_count: int) -> str:
        """
        Create concat file that loops a single audio file N times.
        This is used after merging multiple audio files into one.
        """
        concat_content = []
        for _ in range(loop_count):
            concat_content.append(f"file '{audio_file}'")
        
        concat_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='_audio_loop.txt',
            delete=False,
            encoding='utf-8'
        )
        concat_file.write('\n'.join(concat_content))
        concat_file.close()
        
        self._temp_files.append(concat_file.name)
        return concat_file.name
    
    def _create_sfx_filter(
        self,
        media_config: MediaConfig,
        audio_input_idx: int,
        sfx_input_idx: int
    ) -> str:
        """
        Create FFmpeg filter for overlaying sound effect at beat times.
        
        Uses adelay filter to position SFX at each beat, then amix to combine.
        """
        if not media_config.sfx_enabled or not media_config.beat_times:
            return ""
        
        beat_times = media_config.beat_times
        sfx_volume = media_config.sfx_volume
        
        # Limit beats to avoid extremely long filter
        max_beats = 200
        if len(beat_times) > max_beats:
            beat_times = beat_times[:max_beats]
        
        n_beats = len(beat_times)
        filters = []
        
        # Step 1: Split SFX into multiple copies
        split_outputs = "".join([f"[s{i}]" for i in range(n_beats)])
        filters.append(f"[{sfx_input_idx}:a]asplit={n_beats}{split_outputs}")
        
        # Step 2: Apply delay to each SFX copy
        delayed_outputs = []
        for i, beat_time in enumerate(beat_times):
            delay_ms = int(beat_time * 1000)
            filters.append(f"[s{i}]adelay={delay_ms}|{delay_ms}[d{i}]")
            delayed_outputs.append(f"[d{i}]")
        
        # Step 3: Mix all SFX copies together first (without main audio)
        if n_beats > 1:
            sfx_mix_inputs = "".join(delayed_outputs)
            filters.append(f"{sfx_mix_inputs}amix=inputs={n_beats}:normalize=0[sfx_mixed]")
            sfx_output = "[sfx_mixed]"
        else:
            sfx_output = delayed_outputs[0]
        
        # Step 4: Adjust SFX volume
        filters.append(f"{sfx_output}volume={sfx_volume}[sfx_vol]")
        
        # Step 5: Mix main audio with SFX using amerge + pan for proper stereo mixing
        # Or use amix with weights to preserve main audio volume
        # weights: main audio = 1.0, sfx = 1.0 (volumes already adjusted)
        filters.append(
            f"[{audio_input_idx}:a][sfx_vol]amix=inputs=2:duration=first:normalize=0:weights=1 1[aout]"
        )
        
        return ";".join(filters)
    
    def _get_target_duration(self, media_config: MediaConfig, audio_duration: float) -> float:
        """Calculate target duration based on loop mode."""
        return media_config.get_target_duration(audio_duration)
    
    def _build_video_with_transitions(
        self,
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> List[str]:
        """Build command for video with xfade transitions."""
        # Get audio source
        audio_source, audio_duration = self._get_audio_source(media_config)
        
        # Get video files (no looping for xfade, just use videos as-is)
        original_videos = self._media_manager.get_ordered_video_list(
            media_config.video_files,
            media_config.cover_video if media_config.cover_video else None
        )
        
        if not original_videos:
            raise ValueError("No video files selected")
        
        if len(original_videos) < 2:
            # If only 1 video, fallback to traditional concat
            return self._build_video_traditional_concat(media_config, export_settings)
        
        # Get video durations
        original_video_durations = []
        for video in original_videos:
            duration = self._audio_utils.get_duration(video) or 5.0
            original_video_durations.append(duration)
        
        # Calculate how many times we need to repeat videos to match audio duration
        # This is crucial for looping to work properly with overlays
        transition_duration = media_config.transition_duration
        single_cycle_duration = sum(original_video_durations) - (transition_duration * (len(original_videos) - 1))
        
        if audio_duration and single_cycle_duration > 0:
            # Calculate how many times to repeat the video sequence
            # When repeating, we lose one transition_duration at the junction
            effective_cycle_duration = single_cycle_duration - transition_duration
            
            if effective_cycle_duration > 0:
                num_repeats = int(audio_duration / effective_cycle_duration) + 2
            else:
                # Fallback if transition consumes almost all duration
                num_repeats = int(audio_duration / single_cycle_duration) + 4
                
            print(f"[XFADE LOOP] Audio: {audio_duration}s, Single cycle: {single_cycle_duration}s, Effective add: {effective_cycle_duration}s, Repeating {num_repeats}x")
            
            # Repeat video list to match audio duration
            videos = []
            video_durations = []
            for _ in range(num_repeats):
                videos.extend(original_videos)
                video_durations.extend(original_video_durations)
        else:
            # No audio or can't calculate, use original
            videos = original_videos
            video_durations = original_video_durations
        
        print(f"[XFADE LOOP] Total videos for xfade: {len(videos)}, Total duration: {sum(video_durations)}s")
        
        # Calculate total video duration (accounting for xfades)
        if videos:
            total_video_duration = sum(video_durations) - (transition_duration * (len(videos) - 1))
        else:
            total_video_duration = 0.0
            
        print(f"[XFADE LOOP] Calculated output duration: {total_video_duration}s")
        
        # NEW: Handle Large Number of Videos by Rendering Intermediate Chunks
        # Limit inputs to prevent OOM errors (typically happens around 30-50 inputs)
        MAX_INPUTS_PER_PASS = 20
        
        if len(videos) > MAX_INPUTS_PER_PASS:
            print(f"\n[XFADE] ⚠️ Too many videos ({len(videos)}) for single pass. Switching to incremental rendering...")
            
            # Create a simplified export settings for intermediate renders (maintain quality)
            intermediate_settings = ExportSettings(
                width=export_settings.width,
                height=export_settings.height,
                fps=export_settings.fps,
                # Use high bitrate/quality for intermediate
                rate_control=RateControl.CRF,
                crf_value=18,
                video_codec=VideoCodec.H264,
                encoding_method=export_settings.encoding_method
            )
            
            # Process in chunks
            # Start with the first batch
            current_processed_video = None
            
            # We process first batch (0..N-1), render to temp
            # Then process [temp, N..N+M-1], render to temp
            # ...
            
            # Calculate batch size (N)
            # We reserve 1 input for the previous chunk (except for first batch)
            batch_size = MAX_INPUTS_PER_PASS
            
            # Initial batch
            chunk_videos = videos[:batch_size]
            remaining_videos = videos[batch_size:]
            chunk_durations = video_durations[:batch_size]
            remaining_durations = video_durations[batch_size:]
            
            batch_idx = 0
            
            while True:
                batch_idx += 1
                print(f"[XFADE] Rendering chunk {batch_idx}: {len(chunk_videos)} videos...")
                
                # Keep track of previous chunk for cleanup
                prev_processed_video = current_processed_video
                
                # Render this chunk
                temp_chunk = self._render_xfade_chunk(
                    chunk_videos, 
                    chunk_durations, 
                    media_config, 
                    intermediate_settings
                )
                
                current_processed_video = temp_chunk
                
                # Cleanup previous chunk if it was a temp file
                if prev_processed_video and prev_processed_video in self._temp_files:
                    try:
                        if os.path.exists(prev_processed_video):
                            os.remove(prev_processed_video)
                            print(f"[XFADE] Cleaned up intermediate chunk: {prev_processed_video}")
                            # We remove it from _temp_files so cleanup_temp_files() doesn't try to delete it again
                            self._temp_files.remove(prev_processed_video)
                    except Exception as e:
                        print(f"[XFADE] Warning: Failed to cleanup chunk: {e}")
                
                if not remaining_videos:
                    break
                    
                # Setup next batch
                # Next batch inputs: [current_processed_video] + next set of videos
                # But we can only take (MAX_INPUTS - 1) new videos
                next_batch_size = MAX_INPUTS_PER_PASS - 1
                
                next_videos = remaining_videos[:next_batch_size]
                next_durations = remaining_durations[:next_batch_size]
                
                # Update remaining
                remaining_videos = remaining_videos[next_batch_size:]
                remaining_durations = remaining_durations[next_batch_size:]
                
                # Construct input list for next iteration
                chunk_videos = [current_processed_video] + next_videos
                
                # Need duration of processed chunk
                chunk_dur = self._audio_utils.get_duration(current_processed_video)
                chunk_durations = [chunk_dur] + next_durations
            
            # Now we have a single video file containing the entire xfaded sequence
            videos = [current_processed_video]
            video_durations = [self._audio_utils.get_duration(current_processed_video)]
            print(f"[XFADE] ✅ Incremental rendering complete. Final video: {current_processed_video}")
            
        # Build command
        cmd = [self._ffmpeg_path, '-y']
        
        # Add all video inputs (including repeated ones)
        for video in videos:
            cmd.extend(['-i', video])
        
        # Track input indices
        next_input_idx = len(videos)
        audio_input_idx = None
        
        # Add audio input if needed
        if audio_source is not None:
            is_audio_concat = audio_source.endswith('.txt')
            if is_audio_concat:
                cmd.extend(['-f', 'concat', '-safe', '0', '-i', audio_source])
            else:
                cmd.extend(['-i', audio_source])
            audio_input_idx = next_input_idx
            next_input_idx += 1
        
        # Generate custom spectrum if enabled
        spectrum_input_idx = None
        if media_config.audio_visualizer.enabled and media_config.audio_visualizer.style == VisualizerStyle.CUSTOM_BARS:
            spectrum_audio_source = audio_source if audio_source else (videos[0] if videos else None)
            if spectrum_audio_source:
                spectrum_video = self._generate_custom_spectrum(
                    spectrum_audio_source,
                    media_config,
                    total_video_duration
                )
                if spectrum_video:
                    cmd.extend(['-stream_loop', '-1', '-i', spectrum_video])
                    spectrum_input_idx = next_input_idx
                    next_input_idx += 1
        
        # NEW: Generate Astrofox visualizer video if enabled
        visualizer_input_idx = None
        if media_config.visualizer.type != VisualizerType.NONE:
            from core.visualizer_preview import VisualizerPreviewGenerator
            import tempfile
            
            # Generate visualizer video for full duration
            temp_viz_video = tempfile.NamedTemporaryFile(
                suffix='.mp4',
                delete=False,
                dir=tempfile.gettempdir()
            )
            temp_viz_video.close()
            
            viz_gen = VisualizerPreviewGenerator()
            success = viz_gen.generate_full_video(
                audio_path=audio_source if audio_source else videos[0],
                output_path=temp_viz_video.name,
                config=media_config.visualizer,
                duration=total_video_duration,
                width=export_settings.width,
                height=export_settings.height
            )
            
            if success:
                # Add visualizer video as input with loop
                cmd.extend(['-stream_loop', '-1', '-i', temp_viz_video.name])
                visualizer_input_idx = next_input_idx
                next_input_idx += 1
                print(f"Visualizer video generated successfully")
            else:
                print("Failed to generate visualizer video")
        
        # Add logo input if enabled
        logo_input_idx = None
        if media_config.logo_overlay.enabled and media_config.logo_overlay.filepath:
            cmd.extend(['-i', media_config.logo_overlay.filepath])
            logo_input_idx = next_input_idx
            next_input_idx += 1
        
        # Input: Audio layers (sound effects)
        audio_layer_indices = []
        if media_config.audio_layers:
            for layer_config in media_config.audio_layers:
                if layer_config.enabled and layer_config.file_path:
                    cmd.extend(['-i', layer_config.file_path])
                    audio_layer_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Input: Advanced overlays (blend modes + chroma key)
        overlay_input_indices = []
        if media_config.overlays:
            for overlay_config in media_config.overlays:
                if overlay_config.enabled and overlay_config.filepath:
                    # Apply input looping if configured
                    if overlay_config.loop:
                        cmd.extend(['-stream_loop', '-1'])
                        
                    cmd.extend(['-i', overlay_config.filepath])
                    overlay_input_indices.append(next_input_idx)
                    next_input_idx += 1
        
        # Build xfade filter chain for video
        transition_duration = media_config.transition_duration
        transition_type = media_config.transition_type
        
        xfade_filters = []
        current_output = "[0:v]"
        # Track duration of the current video stream as we build it
        # Starts with the first video's duration
        current_stream_duration = video_durations[0]
        print(f"[XFADE] Building chain with {len(videos)} videos. V0 duration: {current_stream_duration:.2f}s")
        
        for i in range(len(videos) - 1):
            # Combining current stream with videos[i+1]
            next_idx = i + 1
            next_dur = video_durations[next_idx]
            
            # Calculate offset: Transition starts transition_duration BEFORE the end of current stream
            offset = current_stream_duration - transition_duration
            
            # Safety check: Ensure offset is positive (first video must be longer than transition)
            if offset < 0:
                print(f"[XFADE WARNING] Video {i} is shorter than transition! Duration: {current_stream_duration}, Transition: {transition_duration}")
                offset = 0
            
            # Next input
            next_input = f"[{next_idx}:v]"
            output_label = f"[v{i}]" if i < len(videos) - 2 else "[vxfade]"
            
            # Build xfade filter
            xfade_filter = f"{current_output}{next_input}xfade=transition={transition_type}:duration={transition_duration}:offset={offset:.3f}{output_label}"
            xfade_filters.append(xfade_filter)
            
            # Update current stream duration
            # New duration = Old duration + Next duration - Transition duration
            current_stream_duration = current_stream_duration + next_dur - transition_duration
            
            # Update output label for next iteration
            current_output = output_label
        
        # Apply video scale/zoom if enabled
        if media_config.video_scale_enabled and media_config.video_scale_percent > 100:
            zoom_factor = media_config.video_scale_percent / 100.0
            scale_zoom = f"[vxfade]scale=iw*{zoom_factor}:ih*{zoom_factor},crop=iw/{zoom_factor}:ih/{zoom_factor}[vzoomed]"
            xfade_filters.append(scale_zoom)
            current_output = "[vzoomed]"
        else:
            current_output = "[vxfade]"
        
        # Scale to output resolution and apply fps
        final_scale = f"{current_output}scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2,fps={export_settings.fps}[vscaled]"
        xfade_filters.append(final_scale)
        current_output = "[vscaled]"
        
        # Add logo overlay if enabled
        if logo_input_idx is not None:
            logo_scale = media_config.logo_overlay.get_scale_filter(export_settings.width)
            logo_overlay = media_config.logo_overlay.get_overlay_filter(
                export_settings.width, export_settings.height
            )
            xfade_filters.append(f"[{logo_input_idx}:v]{logo_scale}[logo]")
            xfade_filters.append(f"{current_output}[logo]{logo_overlay}[withlogo]")
            current_output = "[withlogo]"
        
        # Add text overlay if enabled
        if media_config.text_overlay.enabled and media_config.text_overlay.text:
            drawtext = media_config.text_overlay.get_drawtext_filter(
                export_settings.width, export_settings.height
            )
            xfade_filters.append(f"{current_output}{drawtext}[withtext]")
            current_output = "[withtext]"
        
        # Add animated text timeline
        if media_config.animated_text_timeline.enabled:
            text_filters = media_config.animated_text_timeline.get_all_filters()
            for idx, text_filter in enumerate(text_filters):
                xfade_filters.append(f"{current_output}{text_filter}[text{idx}]")
                current_output = f"[text{idx}]"
        
        # Add audio visualizer overlay if enabled
        if spectrum_input_idx is not None:
            viz_overlay = media_config.audio_visualizer.get_overlay_position()
            xfade_filters.append(f"{current_output}[{spectrum_input_idx}:v]{viz_overlay}[withviz]")
            current_output = "[withviz]"
        
        # Add chroma key overlays
        if overlay_input_indices and media_config.overlays:
            for idx, (overlay_config, input_idx) in enumerate(zip(media_config.overlays, overlay_input_indices)):
                if overlay_config.enabled and overlay_config.filepath:
                    # Input stream
                    input_stream = f"[{input_idx}:v]"
                    
                    # Apply trim to target duration to ensure it matches audio duration exactly
                    # This handles:
                    # 1. Trimming if overlay > target (e.g. 15m overlay on 10m audio)
                    # 2. Preventing infinite loop if -stream_loop is used
                    # 3. Looping is handled by -stream_loop on input side (if enabled)
                    if total_video_duration > 0:
                        xfade_filters.append(f"{input_stream}trim=duration={total_video_duration}:start=0,setpts=PTS-STARTPTS[ck{idx}_trimmed]")
                        current_overlay = f"[ck{idx}_trimmed]"
                    else:
                        current_overlay = input_stream
                    
                    # Scale overlay
                    overlay_scale = overlay_config.get_scale_filter(export_settings.width)
                    xfade_filters.append(f"{current_overlay}{overlay_scale}[ck{idx}_scaled]")
                    
                    current_overlay = f"[ck{idx}_scaled]"
                    
                    # Apply chroma key if enabled
                    if overlay_config.chroma_key_enabled:
                        chromakey_filter = overlay_config.get_chromakey_filter()
                        if chromakey_filter:
                            xfade_filters.append(f"{current_overlay}{chromakey_filter}[ck{idx}_keyed]")
                            current_overlay = f"[ck{idx}_keyed]"
                    
                    # Apply opacity if < 1.0
                    if overlay_config.opacity < 1.0:
                        opacity_val = overlay_config.opacity
                        xfade_filters.append(f"{current_overlay}format=yuva420p,colorchannelmixer=aa={opacity_val}[ck{idx}_alpha]")
                        current_overlay = f"[ck{idx}_alpha]"
                    
                    # Apply blend mode if not NORMAL
                    if overlay_config.blend_mode != BlendMode.NORMAL:
                        blend_mode = overlay_config.blend_mode.value
                        
                        # For blend mode with positioning:
                        # Create transparent canvas and position overlay on it, then blend
                        overlay_pos = overlay_config.get_overlay_filter(export_settings.width, export_settings.height)
                        
                        xfade_filters.append(f"color=c=black@0.0:s={export_settings.width}x{export_settings.height}:d={total_video_duration}[canvas{idx}]")
                        xfade_filters.append(f"[canvas{idx}]{current_overlay}{overlay_pos}[positioned{idx}]")
                        xfade_filters.append(f"{current_output}[positioned{idx}]blend=all_mode={blend_mode}[ck{idx}]")
                        current_output = f"[ck{idx}]"
                    else:
                        # Normal overlay (with position)
                        overlay_pos = overlay_config.get_overlay_filter(export_settings.width, export_settings.height)
                        # shortest=1 removed as it truncates. Trimming handled by input trim above.
                        xfade_filters.append(f"{current_output}{current_overlay}{overlay_pos}[ck{idx}]")
                        current_output = f"[ck{idx}]"
        
        # NEW: Add Astrofox visualizer overlay (LAST - so it's on top)
        if visualizer_input_idx is not None:
            # Overlay visualizer video (already rendered with correct size and transparency)
            xfade_filters.append(f"{current_output}[{visualizer_input_idx}:v]overlay=0:0[withviz]")
            current_output = "[withviz]"
        
        # Final output
        final_filter = xfade_filters[-1]
        xfade_filters[-1] = final_filter.rsplit('[', 1)[0] + '[vout]'
        
        # Handle audio with layer support
        audio_filter, audio_map = self._build_audio_filter(
            media_config,
            video_input_idx=0,  # First video
            audio_input_idx=audio_input_idx,
            audio_layer_indices=audio_layer_indices
        )
        
        # Build complete filter_complex
        all_filters = xfade_filters.copy()
        
        if audio_filter:
            all_filters.append(audio_filter)
            audio_map_to_use = audio_map
        elif audio_input_idx is not None:
            audio_map_to_use = f'{audio_input_idx}:a'
        else:
            # Mix audio from all video inputs
            if len(videos) > 1:
                audio_mix = ''.join([f'[{i}:a]' for i in range(len(videos))])
                audio_mix += f'amix=inputs={len(videos)}[aout]'
                all_filters.append(audio_mix)
                audio_map_to_use = '[aout]'
            else:
                audio_map_to_use = '0:a'
        
        # Add filter_complex with file fallback for long commands
        self._add_filter_complex(cmd, ';'.join(all_filters))
        
        # Map video and audio
        cmd.extend(['-map', '[vout]'])
        cmd.extend(['-map', audio_map_to_use])
        
        # Encoding settings
        cmd.extend(self._get_encoding_options(export_settings))
        
        # Output
        cmd.append(export_settings.output_path)
        
        return cmd
    
    def _render_xfade_chunk(
        self, 
        videos: List[str], 
        video_durations: List[float],
        media_config: MediaConfig,
        export_settings: ExportSettings
    ) -> str:
        """
        Render a chunk of videos with xfade transitions to a temporary file.
        Used to prevent OOM when processing many videos.
        """
        if not videos:
            raise ValueError("No videos to render in chunk")
            
        # Create temp output file
        temp_output = tempfile.NamedTemporaryFile(
            suffix='_chunk.mp4',
            delete=False,
            dir=tempfile.gettempdir()
        )
        temp_output.close()
        self._temp_files.append(temp_output.name)
        
        # Build command for this chunk (VIDEO ONLY, NO AUDIO)
        cmd = [self._ffmpeg_path, '-y']
        
        for video in videos:
            cmd.extend(['-i', video])
            
        # Build xfade filter chain
        transition_duration = media_config.transition_duration
        transition_type = media_config.transition_type
        
        xfade_filters = []
        current_output = "[0:v]"
        current_stream_duration = video_durations[0]
        
        for i in range(len(videos) - 1):
            next_idx = i + 1
            next_dur = video_durations[next_idx]
            
            offset = current_stream_duration - transition_duration
            if offset < 0: offset = 0
            
            next_input = f"[{next_idx}:v]"
            output_label = f"[v{i}]" if i < len(videos) - 2 else "[vout]"
            
            xfade_filter = f"{current_output}{next_input}xfade=transition={transition_type}:duration={transition_duration}:offset={offset:.3f}{output_label}"
            xfade_filters.append(xfade_filter)
            
            current_output = output_label
            current_stream_duration = current_stream_duration + next_dur - transition_duration
            
        # If no xfades (single video), just copy
        if not xfade_filters:
            # Just copy the video if it's the only one
            if len(videos) == 1:
                import shutil
                try:
                    shutil.copy2(videos[0], temp_output.name)
                    return temp_output.name
                except:
                    # Fallback to re-encode
                    cmd = [self._ffmpeg_path, '-y', '-i', videos[0], '-c:v', 'copy', '-an', temp_output.name]
            else:
                # Should not happen given logic
                pass
        else:
            # Apply filters
            # Note: We do NOT apply scale/overlay here, only xfade
            # This keeps it raw/clean for the final pass
            
            # Ensure pixel format consistency
            # Convert to consistent format to avoid errors when mixing formats
            # xfade requires consistent inputs, but we assume inputs are similar
            # If not, we might need pre-scaling. 
            # Ideally, we should add scale filters to inputs if sizes differ.
            
            # For now, assume inputs are compatible (or add scale to inputs)
            # Let's add simple scaling to inputs to ensure they match target resolution
            # This is safer for intermediate chunks
            
            # Rebuild command with pre-scaling
            cmd = [self._ffmpeg_path, '-y']
            input_labels = []
            
            for idx, video in enumerate(videos):
                cmd.extend(['-i', video])
                # Scale each input
                input_labels.append(f"[{idx}:v]")
            
            # Apply scaling to all inputs first? 
            # Or just assume they work? 
            # If we scale here, we double-scale in final pass.
            # But xfade fails if resolutions differ.
            # Best approach: Scale inputs to target resolution within this filter graph
            
            scaled_filters = []
            
            # Redefine the loop with scaling
            current_output = "[v0_scaled]"
            scaled_filters.append(f"[0:v]scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2,setsar=1[v0_scaled]")
            
            # Track duration
            current_stream_duration = video_durations[0]
            
            for i in range(len(videos) - 1):
                next_idx = i + 1
                next_dur = video_durations[next_idx]
                
                # Scale next input
                scaled_filters.append(f"[{next_idx}:v]scale={export_settings.width}:{export_settings.height}:force_original_aspect_ratio=decrease,pad={export_settings.width}:{export_settings.height}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{next_idx}_scaled]")
                next_input = f"[v{next_idx}_scaled]"
                
                offset = current_stream_duration - transition_duration
                if offset < 0: offset = 0
                
                output_label = f"[v{i}_xf]" if i < len(videos) - 2 else "[vout]"
                
                xfade_filter = f"{current_output}{next_input}xfade=transition={transition_type}:duration={transition_duration}:offset={offset:.3f}{output_label}"
                scaled_filters.append(xfade_filter)
                
                current_output = output_label
                current_stream_duration = current_stream_duration + next_dur - transition_duration
            
            self._add_filter_complex(cmd, ";".join(scaled_filters))
            cmd.extend(['-map', '[vout]'])
            
            # Encoding settings for intermediate
            # High quality, no audio
            cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', '-an'])
            cmd.append(temp_output.name)
            
        # Execute chunk render
        try:
            print(f"   Executing chunk render ({len(videos)} inputs)...")
            # Don't show window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )
            return temp_output.name
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print(f"❌ Chunk render failed: {error_msg}")
            raise ValueError(f"Failed to render video chunk: {error_msg}")

    def _create_concat_file(
        self,
        videos: List[str],
        target_duration: float,
        loop: bool,
        has_cover: bool = False
    ) -> str:
        """Create concat file for video concatenation."""
        # Calculate total video duration
        total_duration = 0.0
        video_durations = []
        
        for video in videos:
            duration = self._audio_utils.get_duration(video)
            if duration:
                video_durations.append((video, duration))
                total_duration += duration
        
        if not video_durations:
            raise ValueError("Could not determine video durations")
        
        # Build concat file content
        concat_content = []
        current_duration = 0.0
        video_index = 0
        
        # If there is a cover video, add it first (index 0) without looping
        if has_cover and video_durations:
            first_video, first_duration = video_durations[0]
            concat_content.append(f"file '{first_video}'")
            current_duration += first_duration
            video_index = 1
        
        # Add remaining videos, looping if needed
        while current_duration < target_duration and video_durations:
            if video_index >= len(video_durations):
                if loop:
                    # If has cover, skip index 0 when looping
                    video_index = 1 if has_cover and len(video_durations) > 1 else 0
                else:
                    break
            
            video, duration = video_durations[video_index]
            concat_content.append(f"file '{video}'")
            current_duration += duration
            video_index += 1
        
        # Write concat file
        concat_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        )
        concat_file.write('\n'.join(concat_content))
        concat_file.close()
        
        self._temp_files.append(concat_file.name)
        return concat_file.name
    
    def _get_encoding_options(self, export_settings: ExportSettings) -> List[str]:
        """Get encoding options for FFmpeg based on encoding method."""
        options = []
        method = export_settings.encoding_method
        
        if method == EncodingMethod.COPY:
            # Stream copy - no re-encoding (fastest)
            options.extend(['-c:v', 'copy'])
            options.extend(['-c:a', 'copy'])
            return options
        
        elif method == EncodingMethod.NVENC:
            # NVIDIA GPU Fast encoding
            options.extend(['-c:v', 'h264_nvenc'])
            options.extend(['-preset', 'p4'])  # Fast preset
            options.extend(['-tune', 'hq'])
            options.extend(['-rc', 'vbr'])
            options.extend(['-cq', '23'])
            options.extend(['-b:v', f'{export_settings.bitrate_kbps}k'])
            options.extend(['-maxrate', f'{int(export_settings.bitrate_kbps * 1.5)}k'])
            options.extend(['-bufsize', f'{export_settings.bitrate_kbps * 2}k'])
            # Keyframe interval for streaming (2 seconds)
            options.extend(['-g', str(export_settings.fps * 2)])
            options.extend(['-keyint_min', str(export_settings.fps)])
        
        elif method == EncodingMethod.NVENC_HQ:
            # NVIDIA GPU High Quality (Anti-glitch)
            # Uses CBR for predictable bitrate that respects user setting
            options.extend(['-c:v', 'h264_nvenc'])
            options.extend(['-preset', 'p7'])  # Slowest/highest quality preset
            options.extend(['-tune', 'hq'])
            options.extend(['-rc', 'cbr'])  # CBR to respect user's bitrate setting
            options.extend(['-b:v', f'{export_settings.bitrate_kbps}k'])
            options.extend(['-maxrate', f'{export_settings.bitrate_kbps}k'])
            options.extend(['-bufsize', f'{export_settings.bitrate_kbps * 2}k'])
            # Anti-glitch: More B-frames and reference frames
            options.extend(['-bf', '3'])
            options.extend(['-refs', '4'])
            # Keyframe interval for streaming (2 seconds)
            options.extend(['-g', str(export_settings.fps * 2)])
            options.extend(['-keyint_min', str(export_settings.fps)])
        
        elif method == EncodingMethod.X264:
            # CPU Standard encoding
            options.extend(['-c:v', 'libx264'])
            options.extend(['-preset', 'medium'])
            if export_settings.rate_control == RateControl.CRF:
                options.extend(['-crf', '23'])
            else:
                options.extend(['-b:v', f'{export_settings.bitrate_kbps}k'])
            # Keyframe interval for streaming (2 seconds)
            options.extend(['-g', str(export_settings.fps * 2)])
            options.extend(['-keyint_min', str(export_settings.fps)])
        
        elif method == EncodingMethod.X264_HQ:
            # CPU High Quality (slower, anti-glitch)
            options.extend(['-c:v', 'libx264'])
            options.extend(['-preset', 'slow'])
            options.extend(['-tune', 'film'])
            if export_settings.rate_control == RateControl.CRF:
                options.extend(['-crf', '18'])  # Higher quality
            else:
                options.extend(['-b:v', f'{export_settings.bitrate_kbps}k'])
            # Anti-glitch: More B-frames and reference frames
            options.extend(['-bf', '3'])
            options.extend(['-refs', '5'])
            # Keyframe interval for streaming (2 seconds)
            options.extend(['-g', str(export_settings.fps * 2)])
            options.extend(['-keyint_min', str(export_settings.fps)])
        
        # Pixel format (for compatibility)
        options.extend(['-pix_fmt', 'yuv420p'])
        
        # Audio codec
        options.extend(['-c:a', export_settings.audio_codec.value])
        options.extend(['-b:a', f'{export_settings.audio_bitrate_kbps}k'])
        
        # Additional options for compatibility
        options.extend(['-movflags', '+faststart'])
        
        return options
    
    def _generate_custom_spectrum(
        self,
        audio_source: str,
        media_config: MediaConfig,
        duration: float
    ) -> Optional[str]:
        """
        Generate custom spectrum visualization using Python renderer.
        
        Args:
            audio_source: Path to audio file.
            media_config: Media configuration with visualizer settings.
            duration: Duration in seconds.
            
        Returns:
            Path to generated spectrum video, or None if failed.
        """
        if not media_config.audio_visualizer.enabled:
            return None
        
        if media_config.audio_visualizer.style != VisualizerStyle.CUSTOM_BARS:
            return None
        
        try:
            print(f"\n{'='*60}")
            print(f"🎨 Generating Custom Spectrum:")
            print(f"   Audio: {audio_source}")
            print(f"   Size: {media_config.audio_visualizer.width}x{media_config.audio_visualizer.height}")
            print(f"   Bars: {media_config.audio_visualizer.bar_count}")
            print(f"   Color: {media_config.audio_visualizer.color}")
            print(f"{'='*60}\n")
            
            # Create temp output file (MOV for alpha channel support)
            temp_output = tempfile.NamedTemporaryFile(
                suffix='_spectrum.mov',
                delete=False
            )
            temp_output.close()
            self._temp_files.append(temp_output.name)
            
            # Initialize renderer
            print("   Loading audio...")
            renderer = SpectrumRenderer(audio_source)
            
            # Convert hex color to RGB
            rgb_color = SpectrumRenderer.hex_to_rgb(media_config.audio_visualizer.color)
            
            # Generate spectrum video
            print("   Rendering spectrum frames...")
            spectrum_path = renderer.create_spectrum_video(
                output_path=temp_output.name,
                width=media_config.audio_visualizer.width,
                height=media_config.audio_visualizer.height,
                bar_count=media_config.audio_visualizer.bar_count,
                color=rgb_color,
                fps=30
            )
            
            print(f"   ✅ Spectrum generated: {spectrum_path}")
            print(f"{'='*60}\n")
            
            return spectrum_path
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"\n{'='*60}")
            print(f"❌ FAILED to generate custom spectrum!")
            print(f"   Error: {e}")
            print(f"   Traceback:\n{error_trace}")
            print(f"{'='*60}\n")
            raise  # Re-raise to propagate error to user
    
    
    def _add_filter_complex(self, cmd: List[str], filter_complex: str) -> None:
        """
        Add filter_complex to command. Use file if too long to avoid Windows cmd line limit.
        
        Args:
            cmd: Command list to append to
            filter_complex: Filter complex string
        """
        # Estimate command length
        cmd_str = ' '.join(cmd) + f' -filter_complex {filter_complex}'
        
        if len(cmd_str) > self.MAX_COMMAND_LENGTH:
            # Use filter script file to avoid Windows command line length limit
            # Create temporary filter script file
            filter_script = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.txt', 
                delete=False,
                encoding='utf-8'
            )
            filter_script.write(filter_complex)
            filter_script.close()
            
            # Track for cleanup
            self._temp_files.append(filter_script.name)
            
            # Use -filter_complex_script instead
            cmd.extend(['-filter_complex_script', filter_script.name])
        else:
            # Normal inline filter_complex
            cmd.extend(['-filter_complex', filter_complex])
    
    def cleanup_temp_files(self) -> None:
        """Remove temporary files created during build."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass
        self._temp_files = []
    
    @staticmethod
    def get_preset_settings(preset_name: str) -> ExportSettings:
        """Get export settings for a named preset."""
        presets = {
            "YouTube 1080p (FHD)": ExportSettings(
                width=1920, height=1080, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=18,
                bitrate_kbps=4000,  # Default bitrate
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=192
            ),
            "YouTube 1440p (2K/QHD)": ExportSettings(
                width=2560, height=1440, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=18,
                bitrate_kbps=16000,
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=256
            ),
            "YouTube 720p (HD)": ExportSettings(
                width=1280, height=720, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=20,
                bitrate_kbps=5000,
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=128
            ),
            "YouTube 4K (UHD)": ExportSettings(
                width=3840, height=2160, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=18,
                bitrate_kbps=35000,
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=320
            ),
            "Instagram (Square)": ExportSettings(
                width=1080, height=1080, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=18,
                bitrate_kbps=6000,
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=128
            ),
            "TikTok (Vertical)": ExportSettings(
                width=1080, height=1920, fps=30,
                video_codec=VideoCodec.H264,
                rate_control=RateControl.CRF,
                crf_value=18,
                bitrate_kbps=6000,
                audio_codec=AudioCodec.AAC,
                audio_bitrate_kbps=128
            ),
        }
        return presets.get(preset_name, ExportSettings())
    
    @staticmethod
    def get_available_presets() -> List[str]:
        """Get list of available preset names."""
        return [
            "YouTube 1080p (FHD)",
            "YouTube 1440p (2K/QHD)",
            "YouTube 720p (HD)",
            "YouTube 4K (UHD)",
            "Instagram (Square)",
            "TikTok (Vertical)",
        ]
