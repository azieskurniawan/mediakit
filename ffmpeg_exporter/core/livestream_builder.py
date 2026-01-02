"""
Livestream Builder - Constructs FFmpeg commands for livestreaming.
"""
import os
import tempfile
from typing import List, Tuple, Optional
from dataclasses import dataclass

from core.media_manager import MediaConfig, MediaMode, AudioSource
from core.audio_utils import AudioUtils
from core.ffmpeg_builder import ExportSettings, EncodingMethod


@dataclass
class LivestreamSettings:
    """Livestream configuration settings."""
    # Stream destination
    rtmp_url: str = "rtmp://a.rtmp.youtube.com/live2/"
    stream_key: str = ""
    
    # Video settings
    width: int = 1920
    height: int = 1080
    fps: int = 30
    bitrate_kbps: int = 4500
    
    # Audio settings
    audio_bitrate_kbps: int = 128
    
    # Duration (0 = infinite)
    duration_minutes: int = 0
    
    # Encoding
    encoding_method: EncodingMethod = EncodingMethod.NVENC
    
    @property
    def full_rtmp_url(self) -> str:
        """Get full RTMP URL with stream key."""
        if not self.stream_key:
            return ""
        return f"{self.rtmp_url}{self.stream_key}"
    
    @property
    def resolution(self) -> str:
        """Get resolution string."""
        return f"{self.width}x{self.height}"


class LivestreamBuilder:
    """Builds FFmpeg commands for livestreaming."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize livestream builder.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable.
            ffprobe_path: Path to FFprobe executable.
        """
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._audio_utils = AudioUtils(ffprobe_path)
        self._temp_files: List[str] = []
    
    def build_command(
        self,
        media_config: MediaConfig,
        stream_settings: LivestreamSettings
    ) -> Tuple[List[str], List[str]]:
        """
        Build FFmpeg command for livestreaming.
        
        Args:
            media_config: Media configuration.
            stream_settings: Livestream settings.
            
        Returns:
            Tuple of (command list, list of temp files to cleanup).
        """
        self._temp_files = []
        
        if not stream_settings.stream_key:
            raise ValueError("Stream key is required")
        
        if media_config.mode == MediaMode.STATIC_IMAGE:
            cmd = self._build_image_stream_command(media_config, stream_settings)
        else:
            cmd = self._build_video_stream_command(media_config, stream_settings)
        
        return cmd, self._temp_files
    
    def _build_image_stream_command(
        self,
        media_config: MediaConfig,
        stream_settings: LivestreamSettings
    ) -> List[str]:
        """Build command for streaming static image."""
        # Static image with VIDEO_AUDIO doesn't make sense
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            raise ValueError("VIDEO_AUDIO mode not supported for static image streaming. Please select audio files.")
        
        # Get audio source - for streaming, we want infinite loop
        audio_source = self._get_looped_audio_source(media_config)
        
        cmd = [self._ffmpeg_path]
        
        # Re-encode flag for realtime streaming
        cmd.extend(['-re'])
        
        # Input 0: looped image
        cmd.extend(['-loop', '1', '-i', media_config.static_image])
        
        # Track input indices
        next_input_idx = 1
        audio_input_idx = None
        
        # Input 1: looped audio
        if audio_source is not None:
            is_audio_concat = audio_source.endswith('.txt')
            if is_audio_concat:
                cmd.extend(['-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', audio_source])
            else:
                cmd.extend(['-stream_loop', '-1', '-i', audio_source])
            audio_input_idx = next_input_idx
            next_input_idx += 1
        
        # Build audio filter
        audio_filter, audio_map = self._build_audio_filter_for_stream(
            media_config,
            video_input_idx=0,  # Image is input 0
            audio_input_idx=audio_input_idx
        )
        
        # Determine audio stream reference for visualizer
        if audio_input_idx is not None:
            audio_stream_ref = f"{audio_input_idx}:a"
        else:
            audio_stream_ref = "0:a"
        
        # Build filter complex for overlays (including visualizer)
        filter_complex = self._build_filter_complex(
            media_config, 
            stream_settings, 
            input_is_image=True,
            audio_stream_ref=audio_stream_ref
        )
        
        # Combine filters
        all_filters = []
        if filter_complex:
            all_filters.append(filter_complex)
        if audio_filter:
            all_filters.append(audio_filter)
        
        if all_filters:
            cmd.extend(['-filter_complex', ";".join(all_filters)])
            cmd.extend(['-map', '[vout]', '-map', audio_map])
        elif filter_complex:
            cmd.extend(['-filter_complex', filter_complex])
            cmd.extend(['-map', '[vout]', '-map', audio_map])
        else:
            # Simple scale
            cmd.extend([
                '-vf', f"scale={stream_settings.width}:{stream_settings.height}:force_original_aspect_ratio=decrease,pad={stream_settings.width}:{stream_settings.height}:(ow-iw)/2:(oh-ih)/2,fps={stream_settings.fps}"
            ])
            cmd.extend(['-map', '0:v', '-map', audio_map])
        
        # Add encoding options for streaming
        cmd.extend(self._get_streaming_options(stream_settings))
        
        # Duration (if specified)
        if stream_settings.duration_minutes > 0:
            cmd.extend(['-t', str(stream_settings.duration_minutes * 60)])
        
        # Output to RTMP
        cmd.extend(['-f', 'flv', stream_settings.full_rtmp_url])
        
        return cmd
    
    def _build_video_stream_command(
        self,
        media_config: MediaConfig,
        stream_settings: LivestreamSettings
    ) -> List[str]:
        """Build command for streaming video directory."""
        # Get audio source - infinite loop (can be None for VIDEO_AUDIO mode)
        audio_source = self._get_looped_audio_source(media_config)
        
        # Get video files
        videos = media_config.video_files
        if not videos:
            raise ValueError("No video files selected")
        
        # Add cover video if specified
        if media_config.cover_video and os.path.exists(media_config.cover_video):
            videos = [media_config.cover_video] + videos
        
        # Create concat file for infinite loop
        concat_file = self._create_infinite_concat_file(videos)
        
        cmd = [self._ffmpeg_path]
        
        # Re-encode flag for realtime streaming
        cmd.extend(['-re'])
        
        # Input 0: video concat file with infinite loop
        cmd.extend(['-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', concat_file])
        
        # Track input indices
        next_input_idx = 1
        audio_input_idx = None
        
        # Input 1: looped audio (if using AUDIO_DIRECTORY or MIX_BOTH)
        if audio_source is not None:
            is_audio_concat = audio_source.endswith('.txt')
            if is_audio_concat:
                cmd.extend(['-stream_loop', '-1', '-f', 'concat', '-safe', '0', '-i', audio_source])
            else:
                cmd.extend(['-stream_loop', '-1', '-i', audio_source])
            audio_input_idx = next_input_idx
            next_input_idx += 1
        
        # Input: logo if enabled
        logo_input_idx = None
        if media_config.logo_overlay.enabled and media_config.logo_overlay.filepath:
            cmd.extend(['-i', media_config.logo_overlay.filepath])
            logo_input_idx = next_input_idx
            next_input_idx += 1
        
        # Check if we can use stream copy (no overlays, no re-encoding needed)
        has_overlays = (
            (media_config.logo_overlay.enabled and media_config.logo_overlay.filepath) or
            (media_config.text_overlay.enabled and media_config.text_overlay.text) or
            (media_config.audio_visualizer.enabled)
        )
        
        # Check if we need audio mixing
        needs_audio_mixing = (media_config.audio_source == AudioSource.MIX_BOTH)
        
        # OPTIMIZATION: Use stream copy if possible
        if not has_overlays and not needs_audio_mixing and media_config.audio_source == AudioSource.VIDEO_AUDIO:
            # Pure stream copy mode - super fast!
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
            cmd.extend(['-map', '0:v', '-map', '0:a'])
        else:
            # Need to re-encode
            # Build audio filter based on audio source mode
            audio_filter, audio_map = self._build_audio_filter_for_stream(
                media_config,
                video_input_idx=0,
                audio_input_idx=audio_input_idx
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
            
            # Build filter complex for video overlays (including visualizer)
            filter_complex = self._build_filter_complex(
                media_config, 
                stream_settings,
                input_is_image=False,
                logo_input_idx=logo_input_idx,
                audio_stream_ref=audio_stream_ref
            )
            
            # Combine all filters
            all_filters = []
            if filter_complex:
                all_filters.append(filter_complex)
            if audio_filter:
                all_filters.append(audio_filter)
            
            if all_filters:
                cmd.extend(['-filter_complex', ";".join(all_filters)])
                cmd.extend(['-map', '[vout]', '-map', audio_map])
            elif filter_complex:
                cmd.extend(['-filter_complex', filter_complex])
                cmd.extend(['-map', '[vout]', '-map', audio_map])
            else:
                # Simple scale
                cmd.extend([
                    '-vf', f"scale={stream_settings.width}:{stream_settings.height}:force_original_aspect_ratio=decrease,pad={stream_settings.width}:{stream_settings.height}:(ow-iw)/2:(oh-ih)/2,fps={stream_settings.fps}"
                ])
                cmd.extend(['-map', '0:v', '-map', audio_map])
            
            # Add encoding options for streaming
            cmd.extend(self._get_streaming_options(stream_settings))
        
        # Duration (if specified)
        if stream_settings.duration_minutes > 0:
            cmd.extend(['-t', str(stream_settings.duration_minutes * 60)])
        
        # Output to RTMP
        cmd.extend(['-f', 'flv', stream_settings.full_rtmp_url])
        
        return cmd
    
    def _build_filter_complex(
        self,
        media_config: MediaConfig,
        stream_settings: LivestreamSettings,
        input_is_image: bool = False,
        logo_input_idx: Optional[int] = None,
        audio_stream_ref: str = "0:a"
    ) -> str:
        """Build filter_complex string for overlays."""
        filters = []
        current_output = "[0:v]"
        
        # Scale to target resolution
        scale_filter = f"{current_output}scale={stream_settings.width}:{stream_settings.height}:force_original_aspect_ratio=decrease,pad={stream_settings.width}:{stream_settings.height}:(ow-iw)/2:(oh-ih)/2,fps={stream_settings.fps}[scaled]"
        filters.append(scale_filter)
        current_output = "[scaled]"
        
        # Add logo overlay if enabled
        if media_config.logo_overlay.enabled and media_config.logo_overlay.filepath and logo_input_idx is not None:
            logo_scale = media_config.logo_overlay.get_scale_filter(stream_settings.width)
            logo_overlay = media_config.logo_overlay.get_overlay_filter(
                stream_settings.width, stream_settings.height
            )
            
            filters.append(f"[{logo_input_idx}:v]{logo_scale}[logo]")
            filters.append(f"{current_output}[logo]{logo_overlay}[withlogo]")
            current_output = "[withlogo]"
        
        # Add text overlay if enabled
        if media_config.text_overlay.enabled and media_config.text_overlay.text:
            drawtext = media_config.text_overlay.get_drawtext_filter(
                stream_settings.width, stream_settings.height
            )
            filters.append(f"{current_output}{drawtext}[withtext]")
            current_output = "[withtext]"
        
        # Add audio visualizer if enabled
        if media_config.audio_visualizer.enabled:
            # Generate visualizer video from audio
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
    
    def _get_looped_audio_source(self, media_config: MediaConfig) -> Optional[str]:
        """
        Get audio source for infinite streaming based on audio_source mode.
        If multiple files, create concat file.
        
        Returns None if using VIDEO_AUDIO mode.
        """
        # If using video audio only, return None
        if media_config.audio_source == AudioSource.VIDEO_AUDIO:
            return None
        
        audio_files = media_config.audio_files
        
        if not audio_files and media_config.audio_source != AudioSource.VIDEO_AUDIO:
            raise ValueError("No audio files selected")
        
        # If only one audio file, return it directly (will be looped with -stream_loop -1)
        if len(audio_files) == 1:
            return audio_files[0]
        
        # Multiple files - create concat file
        concat_content = []
        for audio_file in audio_files:
            concat_content.append(f"file '{audio_file}'")
        
        concat_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='_audio_stream.txt',
            delete=False,
            encoding='utf-8'
        )
        concat_file.write('\n'.join(concat_content))
        concat_file.close()
        
        self._temp_files.append(concat_file.name)
        return concat_file.name
    
    def _build_audio_filter_for_stream(
        self,
        media_config: MediaConfig,
        video_input_idx: int,
        audio_input_idx: Optional[int]
    ) -> Tuple[str, str]:
        """
        Build audio filter for livestream based on audio source mode.
        
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
            
            # Create amix filter for streaming
            filter_str = (
                f"[{video_input_idx}:a]volume={video_vol}[va];"
                f"[{audio_input_idx}:a]volume={music_vol}[ma];"
                f"[va][ma]amix=inputs=2:duration=first:normalize=0[aout]"
            )
            return filter_str, "[aout]"
        
        # Default: use audio directory
        return "", f"{audio_input_idx}:a" if audio_input_idx is not None else f"{video_input_idx}:a"
    
    def _create_infinite_concat_file(self, videos: List[str]) -> str:
        """Create concat file for video list."""
        concat_content = []
        for video in videos:
            concat_content.append(f"file '{video}'")
        
        concat_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='_video_stream.txt',
            delete=False,
            encoding='utf-8'
        )
        concat_file.write('\n'.join(concat_content))
        concat_file.close()
        
        self._temp_files.append(concat_file.name)
        return concat_file.name
    
    def _get_streaming_options(self, stream_settings: LivestreamSettings) -> List[str]:
        """Get FFmpeg encoding options optimized for streaming."""
        options = []
        method = stream_settings.encoding_method
        
        if method == EncodingMethod.NVENC or method == EncodingMethod.NVENC_HQ:
            # NVIDIA GPU encoding for streaming
            options.extend(['-c:v', 'h264_nvenc'])
            options.extend(['-preset', 'p4' if method == EncodingMethod.NVENC else 'p6'])
            options.extend(['-tune', 'll'])  # Low latency
            options.extend(['-rc', 'cbr'])  # Constant bitrate for streaming
            options.extend(['-b:v', f'{stream_settings.bitrate_kbps}k'])
            options.extend(['-maxrate', f'{stream_settings.bitrate_kbps}k'])
            options.extend(['-bufsize', f'{stream_settings.bitrate_kbps * 2}k'])
        else:
            # CPU encoding (x264)
            options.extend(['-c:v', 'libx264'])
            options.extend(['-preset', 'ultrafast'])  # Fastest for realtime (changed from veryfast)
            options.extend(['-tune', 'zerolatency'])  # Low latency
            options.extend(['-b:v', f'{stream_settings.bitrate_kbps}k'])
            options.extend(['-maxrate', f'{stream_settings.bitrate_kbps}k'])
            options.extend(['-bufsize', f'{stream_settings.bitrate_kbps * 2}k'])
        
        # Keyframe interval (2 seconds for YouTube)
        options.extend(['-g', str(stream_settings.fps * 2)])
        options.extend(['-keyint_min', str(stream_settings.fps)])
        
        # Pixel format
        options.extend(['-pix_fmt', 'yuv420p'])
        
        # Audio codec
        options.extend(['-c:a', 'aac'])
        options.extend(['-b:a', f'{stream_settings.audio_bitrate_kbps}k'])
        options.extend(['-ar', '44100'])
        
        return options
    
    @staticmethod
    def get_youtube_presets() -> dict:
        """Get recommended settings for YouTube streaming."""
        return {
            "YouTube 1080p 60fps": LivestreamSettings(
                width=1920, height=1080, fps=60,
                bitrate_kbps=9000,
                audio_bitrate_kbps=128
            ),
            "YouTube 1080p 30fps": LivestreamSettings(
                width=1920, height=1080, fps=30,
                bitrate_kbps=4500,
                audio_bitrate_kbps=128
            ),
            "YouTube 720p 60fps": LivestreamSettings(
                width=1280, height=720, fps=60,
                bitrate_kbps=6000,
                audio_bitrate_kbps=128
            ),
            "YouTube 720p 30fps": LivestreamSettings(
                width=1280, height=720, fps=30,
                bitrate_kbps=3000,
                audio_bitrate_kbps=128
            ),
        }

