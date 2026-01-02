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

from core.media_manager import MediaConfig, MediaMode, MediaManager, LoopMode, AudioSource, VisualizerStyle
from core.audio_utils import AudioUtils
from core.spectrum_renderer import SpectrumRenderer


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
            spectrum_input_idx=spectrum_input_idx
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
        concat_file = self._create_concat_file(videos, target_duration, loop=True)
        
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
            spectrum_input_idx=spectrum_input_idx
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
        spectrum_input_idx: Optional[int] = None
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
        
        # Final output
        if filters:
            # Replace last output label with [vout]
            last_filter = filters[-1]
            last_bracket = last_filter.rfind('[')
            if last_bracket != -1:
                filters[-1] = last_filter[:last_bracket] + "[vout]"
            
            return ";".join(filters)
        
        return ""
    
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
        videos = self._media_manager.get_ordered_video_list(
            media_config.video_files,
            media_config.cover_video if media_config.cover_video else None
        )
        
        if not videos:
            raise ValueError("No video files selected")
        
        if len(videos) < 2:
            # If only 1 video, fallback to traditional concat
            return self._build_video_traditional_concat(media_config, export_settings)
        
        # Get video durations
        video_durations = []
        for video in videos:
            duration = self._audio_utils.get_duration(video) or 5.0
            video_durations.append(duration)
        
        # Build command
        cmd = [self._ffmpeg_path, '-y']
        
        # Add all video inputs
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
                target_duration = sum(video_durations)
                spectrum_video = self._generate_custom_spectrum(
                    spectrum_audio_source,
                    media_config,
                    target_duration
                )
                if spectrum_video:
                    cmd.extend(['-stream_loop', '-1', '-i', spectrum_video])
                    spectrum_input_idx = next_input_idx
                    next_input_idx += 1
        
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
        
        # Build xfade filter chain for video
        transition_duration = media_config.transition_duration
        transition_type = media_config.transition_type
        
        xfade_filters = []
        current_output = "[0:v]"
        cumulative_offset = 0.0
        
        for i in range(len(videos) - 1):
            # Calculate offset (when to start transition)
            offset = cumulative_offset + video_durations[i] - transition_duration
            
            # Next input
            next_input = f"[{i+1}:v]"
            output_label = f"[v{i}]" if i < len(videos) - 2 else "[vxfade]"
            
            # Build xfade filter
            xfade_filter = f"{current_output}{next_input}xfade=transition={transition_type}:duration={transition_duration}:offset={offset}{output_label}"
            xfade_filters.append(xfade_filter)
            
            # Update for next iteration
            current_output = output_label
            cumulative_offset = offset + transition_duration
        
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
        
        # Add audio visualizer overlay if enabled
        if spectrum_input_idx is not None:
            viz_overlay = media_config.audio_visualizer.get_overlay_position()
            xfade_filters.append(f"{current_output}[{spectrum_input_idx}:v]{viz_overlay}[withviz]")
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
        self._add_encoding_params(cmd, export_settings)
        
        # Output
        cmd.append(export_settings.output_path)
        
        return cmd
    
    def _create_concat_file(
        self,
        videos: List[str],
        target_duration: float,
        loop: bool
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
        
        # Always add cover video first (index 0) without looping
        if video_durations:
            first_video, first_duration = video_durations[0]
            concat_content.append(f"file '{first_video}'")
            current_duration += first_duration
            video_index = 1
        
        # Add remaining videos, looping if needed
        while current_duration < target_duration and video_durations:
            if video_index >= len(video_durations):
                if loop:
                    video_index = 1 if len(video_durations) > 1 else 0
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
