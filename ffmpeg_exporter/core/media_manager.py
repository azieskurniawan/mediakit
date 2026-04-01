"""
Media Manager - Handles video and image file management.
"""
import os
import random
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class MediaMode(Enum):
    """Media source mode."""
    VIDEO_DIRECTORY = "video_directory"
    STATIC_IMAGE = "static_image"


class LoopMode(Enum):
    """Loop mode for media."""
    MATCH_AUDIO = "match_audio"  # Loop to match total audio duration
    CUSTOM_DURATION = "custom_duration"  # Loop to custom duration (HH:MM:SS)
    MULTIPLY_AUDIO = "multiply_audio"  # Loop to N times the audio duration


class AudioSource(Enum):
    """Audio source mode."""
    VIDEO_AUDIO = "video_audio"  # Use audio from video files
    AUDIO_DIRECTORY = "audio_directory"  # Use audio from audio directory (replace)
    MIX_BOTH = "mix_both"  # Mix video audio + audio directory


class OverlayPosition(Enum):
    """Overlay position presets (3x3 grid)."""
    # Top row
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    
    # Middle row
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    
    # Bottom row
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    
    # Custom positioning
    CUSTOM = "custom"


class VisualizerType(Enum):
    """Audio visualizer type."""
    NONE = "none"
    BAR_SPECTRUM = "bar_spectrum"            # Bar spectrum (Astrofox style)
    SOUND_WAVE = "sound_wave"                # Sound waveform (Astrofox style)
    CIRCULAR_SPECTRUM = "circular_spectrum"  # Future: circular bars
    LINE_SPECTRUM = "line_spectrum"          # Future: line spectrum


class VisualizerStyle(Enum):
    """Audio visualizer style options (OLD - for FFmpeg native filters)."""
    CUSTOM_BARS = "custom_bars"              # Custom Python renderer (BEST!)
    WAVEFORM_LINE = "waveform_line"          # showwaves mode=line
    WAVEFORM_POINT = "waveform_point"        # showwaves mode=point
    WAVEFORM_P2P = "waveform_p2p"            # showwaves mode=p2p
    SPECTRUM_BARS = "spectrum_bars"          # showfreqs mode=bar (limited control)
    SPECTRUM_LINE = "spectrum_line"          # showfreqs mode=line
    SPECTROGRAM = "spectrogram"              # showspectrum
    MUSICAL_CQT = "musical_cqt"              # showcqt
    STEREO_SCOPE = "stereo_scope"            # avectorscope


class BlendMode(Enum):
    """Overlay blend modes (like Photoshop)."""
    NORMAL = "normal"                # Default - no blending
    MULTIPLY = "multiply"            # Multiply (darken)
    SCREEN = "screen"                # Screen (lighten)
    OVERLAY = "overlay"              # Overlay (combination)
    DARKEN = "darken"                # Darken only
    LIGHTEN = "lighten"              # Lighten only (Brighten)
    COLOR_DODGE = "dodge"            # Color dodge
    COLOR_BURN = "burn"              # Color burn
    HARD_LIGHT = "hardlight"         # Hard light
    SOFT_LIGHT = "softlight"         # Soft light
    DIFFERENCE = "difference"        # Difference
    EXCLUSION = "exclusion"          # Exclusion
    LINEAR_LIGHT = "linearlight"     # Linear light (close to linear burn)
    VIVID_LIGHT = "vividlight"       # Vivid light
    PIN_LIGHT = "pinlight"           # Pin light
    HARD_MIX = "hardmix"             # Hard mix
    PHOENIX = "phoenix"              # Phoenix
    REFLECT = "reflect"              # Reflect
    GLOW = "glow"                    # Glow
    NEGATION = "negation"            # Negation
    HEAT = "heat"                    # Heat


@dataclass
class LogoOverlay:
    """Logo overlay settings."""
    enabled: bool = False
    filepath: str = ""
    size_percent: int = 15  # Size as percentage of video width
    position: OverlayPosition = OverlayPosition.TOP_RIGHT
    x_offset: int = 20
    y_offset: int = 20
    
    def get_overlay_filter(self, video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg overlay filter string.
        
        Args:
            video_width: Target video width.
            video_height: Target video height.
            
        Returns:
            FFmpeg overlay filter string.
        """
        if not self.enabled or not self.filepath:
            return ""
        
        # Calculate logo width based on percentage
        logo_width = int(video_width * self.size_percent / 100)
        
        # Get position coordinates
        x, y = self._get_position_coords(video_width, video_height, logo_width)
        
        return f"overlay={x}:{y}"
    
    def get_scale_filter(self, video_width: int) -> str:
        """Get scale filter for the logo."""
        logo_width = int(video_width * self.size_percent / 100)
        return f"scale={logo_width}:-1"
    
    def _get_position_coords(self, video_width: int, video_height: int, logo_width: int) -> tuple:
        """Calculate position coordinates based on preset."""
        logo_height = logo_width  # Approximate, will be aspect-preserved
        
        if self.position == OverlayPosition.TOP_LEFT:
            return (self.x_offset, self.y_offset)
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"W-w-{self.x_offset}", self.y_offset)
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (self.x_offset, f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"W-w-{self.x_offset}", f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_CENTER:
            # Bottom Center with offset support
            # X: Centered + Offset (positive = right, negative = left)
            # Y: Bottom - Offset (positive = up)
            return (f"(W-w)/2+{self.x_offset}", f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            # Center with offset support
            # X: Centered + Offset
            # Y: Centered + Offset
            return (f"(W-w)/2+{self.x_offset}", f"(H-h)/2+{self.y_offset}")
        else:  # CUSTOM
            return (self.x_offset, self.y_offset)


@dataclass
class TextOverlay:
    """Text overlay settings."""
    enabled: bool = False
    text: str = ""
    font_file: str = ""
    font_size: int = 48
    font_color: str = "white"
    position: OverlayPosition = OverlayPosition.TOP_RIGHT
    x_offset: int = 20
    y_offset: int = 20
    
    def get_drawtext_filter(self, video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg drawtext filter string.
        
        Args:
            video_width: Target video width.
            video_height: Target video height.
            
        Returns:
            FFmpeg drawtext filter string.
        """
        if not self.enabled or not self.text:
            return ""
        
        # Escape special characters in text
        escaped_text = self.text.replace("'", "\\'").replace(":", "\\:")
        
        # Get position expression
        x_expr, y_expr = self._get_position_expression()
        
        # Build filter
        filter_parts = [
            f"text='{escaped_text}'",
            f"fontsize={self.font_size}",
            f"fontcolor={self.font_color}",
            f"x={x_expr}",
            f"y={y_expr}"
        ]
        
        if self.font_file and os.path.isfile(self.font_file):
            # Escape backslashes and colons in path for FFmpeg
            escaped_path = self.font_file.replace("\\", "/").replace(":", "\\:")
            filter_parts.insert(1, f"fontfile='{escaped_path}'")
        
        return "drawtext=" + ":".join(filter_parts)
    
    def _get_position_expression(self) -> tuple:
        """Get FFmpeg position expressions."""
        if self.position == OverlayPosition.TOP_LEFT:
            return (str(self.x_offset), str(self.y_offset))
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"w-text_w-{self.x_offset}", str(self.y_offset))
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (str(self.x_offset), f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"w-text_w-{self.x_offset}", f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            return ("(w-text_w)/2", "(h-text_h)/2")
        else:  # CUSTOM
            return (str(self.x_offset), str(self.y_offset))


@dataclass
class NowPlayingConfig:
    """Now Playing overlay: shows current song title from audio filename (in order)."""
    enabled: bool = False
    font_file: str = ""
    font_size: int = 36
    font_color: str = "white"
    position: OverlayPosition = OverlayPosition.BOTTOM_CENTER
    x_offset: int = 0
    y_offset: int = 40
    # Mulai tampil setelah (detik). Misal cover video 10 detik → set 11 agar now playing dari detik 11.
    start_offset_seconds: float = 0.0
    
    def _get_position_expression(self) -> tuple:
        """Get FFmpeg position expressions (same logic as TextOverlay)."""
        if self.position == OverlayPosition.TOP_LEFT:
            return (str(self.x_offset), str(self.y_offset))
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"w-text_w-{self.x_offset}", str(self.y_offset))
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (str(self.x_offset), f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"w-text_w-{self.x_offset}", f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_CENTER:
            return (f"(w-text_w)/2+{self.x_offset}", f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            return (f"(w-text_w)/2+{self.x_offset}", f"(h-text_h)/2+{self.y_offset}")
        else:  # CUSTOM
            return (str(self.x_offset), str(self.y_offset))
    
    def get_drawtext_filter_timed(
        self,
        video_width: int,
        video_height: int,
        start_time: float,
        end_time: float,
        title_text: str
    ) -> str:
        """
        Generate FFmpeg drawtext filter for a time segment (now playing).
        Text is shown only when t is between start_time and end_time.
        """
        if not self.enabled or not title_text:
            return ""
        escaped = title_text.replace("'", "\\'").replace(":", "\\:")
        x_expr, y_expr = self._get_position_expression()
        filter_parts = [
            f"text='{escaped}'",
            f"fontsize={self.font_size}",
            f"fontcolor={self.font_color}",
            f"x={x_expr}",
            f"y={y_expr}",
            f"enable='between(t\\,{start_time}\\,{end_time})'"
        ]
        if self.font_file and os.path.isfile(self.font_file):
            escaped_path = self.font_file.replace("\\", "/").replace(":", "\\:")
            filter_parts.insert(1, f"fontfile='{escaped_path}'")
        return "drawtext=" + ":".join(filter_parts)


@dataclass
class BarSpectrumConfig:
    """Bar Spectrum visualizer settings (Astrofox style)."""
    enabled: bool = True
    
    # FFT Settings
    max_db: int = -12          # Range: -40 to 0 (Astrofox: maxDecibels)
    min_frequency: int = 0     # Hz
    max_frequency: int = 6000  # Hz (default 6kHz)
    smoothing: float = 0.5     # 0.0 - 0.99
    normalize: bool = True     # Astrofox default: True for BarSpectrum
    
    # Size
    width: int = 770
    height: int = 240
    shadow_height: int = 100
    
    # Bar Settings
    bar_width_auto: bool = True
    bar_width: int = 10        # Only if not auto
    bar_spacing_auto: bool = True
    bar_spacing: int = 2       # Only if not auto
    
    # Colors (gradient support)
    bar_color_start: str = "#FFFFFF"
    bar_color_end: str = "#FFFFFF"
    shadow_color_start: str = "#333333"
    shadow_color_end: str = "#000000"
    
    # Position
    x: int = 0
    y: int = 0
    rotation: int = 0
    opacity: float = 1.0


@dataclass
class SoundWaveConfig:
    """Sound Wave visualizer settings (Astrofox style)."""
    enabled: bool = True
    
    # Wave Settings
    line_width: int = 1
    wavelength: float = 0.0    # 0.0 - 1.0
    smoothing: float = 0.0     # 0.0 - 0.99
    
    # Style
    stroke: bool = True
    stroke_color: str = "#FFFFFF"
    fill: bool = False
    fill_color: str = "#FFFFFF"
    taper_edges: bool = False
    
    # Size
    width: int = 854
    height: int = 240
    
    # Position
    x: int = 0
    y: int = 0
    rotation: int = 0
    opacity: float = 1.0


@dataclass
class VisualizerConfig:
    """Audio visualizer configuration (NEW - Astrofox style)."""
    type: VisualizerType = VisualizerType.NONE
    bar_spectrum: BarSpectrumConfig = field(default_factory=BarSpectrumConfig)
    sound_wave: SoundWaveConfig = field(default_factory=SoundWaveConfig)


@dataclass
class SubtitleConfig:
    """Subtitle/Lyrics settings from SRT files."""
    enabled: bool = False
    
    # Styling
    font_file: str = ""
    font_size: int = 28
    font_color: str = "white"
    outline_color: str = "black"
    outline_width: int = 2
    
    # Position (FFmpeg alignment: 1-9, where 1=bottom-left, 2=bottom-center, 5=center, etc.)
    # 7 8 9 (top)
    # 4 5 6 (middle)
    # 1 2 3 (bottom)
    alignment: int = 2  # Bottom center
    margin_v: int = 60  # Vertical margin (pixels from edge)
    margin_h: int = 20  # Horizontal margin (pixels from edge)
    
    # Background box (optional)
    background_enabled: bool = False
    background_color: str = "black"
    background_opacity: float = 0.5  # 0.0 to 1.0


@dataclass
class AudioVisualizerConfig:
    """Audio visualizer settings (OLD - FFmpeg native filters)."""
    enabled: bool = False
    style: VisualizerStyle = VisualizerStyle.CUSTOM_BARS  # Default to custom renderer!
    color: str = "#3b82f6"  # Blue color
    min_db: int = -90  # Minimum dB level
    max_db: int = 200  # Maximum dB level
    x_position: int = 0  # X coordinate
    y_position: int = 880  # Y coordinate (bottom of 1080p)
    width: int = 1920  # Visualizer width
    height: int = 200  # Visualizer height
    bar_count: int = 50  # Number of bars (for spectrum styles)
    
    def get_visualizer_filter(self, audio_input: str = "0:a") -> str:
        """
        Generate FFmpeg audio visualizer filter string.
        
        Args:
            audio_input: Audio input stream reference (e.g., "0:a", "[aout]")
            
        Returns:
            FFmpeg filter string for audio visualization.
            Returns empty string if using custom Python renderer.
        """
        if not self.enabled:
            return ""
        
        # Custom bars uses Python renderer, not FFmpeg filter
        if self.style == VisualizerStyle.CUSTOM_BARS:
            return ""  # Will be handled separately
        
        # Ensure audio_input has proper brackets
        if not audio_input.startswith('['):
            audio_input = f"[{audio_input}]"
        
        # Convert hex color to FFmpeg format (0xRRGGBB)
        color_hex = self.color.lstrip('#')
        ffmpeg_color = f"0x{color_hex}"
        
        size = f"{self.width}x{self.height}"
        
        # Build filter based on style
        if self.style == VisualizerStyle.WAVEFORM_LINE:
            return f"{audio_input}showwaves=s={size}:mode=line:colors={ffmpeg_color}:rate=30[viz]"
        
        elif self.style == VisualizerStyle.WAVEFORM_POINT:
            return f"{audio_input}showwaves=s={size}:mode=point:colors={ffmpeg_color}:rate=30[viz]"
        
        elif self.style == VisualizerStyle.WAVEFORM_P2P:
            return f"{audio_input}showwaves=s={size}:mode=p2p:colors={ffmpeg_color}:rate=30[viz]"
        
        elif self.style == VisualizerStyle.SPECTRUM_BARS:
            # Simple waveform bars (showwaves mode=cline) for EXACT bar count control
            # showfreqs does NOT support exact bar count - it shows all frequencies
            # Alternative: use showwaves which is simpler but controllable
            # For EXACT bars, we need custom Python renderer (feature request!)
            colors_gradient = f"{ffmpeg_color}|{ffmpeg_color}|{ffmpeg_color}"
            # Note: FFmpeg showfreqs shows ALL frequency bins, cannot limit to exact count
            # This is a limitation of FFmpeg filters
            return f"{audio_input}showwaves=s={size}:mode=cline:colors={ffmpeg_color}:rate=30[viz]"
        
        elif self.style == VisualizerStyle.SPECTRUM_LINE:
            # Frequency line graph with solid color
            colors_gradient = f"{ffmpeg_color}|{ffmpeg_color}|{ffmpeg_color}"
            win_size = min(4096, max(512, self.bar_count * 40))
            return f"{audio_input}showfreqs=s={size}:mode=line:colors={colors_gradient}:fscale=log:win_size={win_size}:rate=30[viz]"
        
        elif self.style == VisualizerStyle.SPECTROGRAM:
            # Advanced spectrogram with custom color scheme
            # Color modes: channel, intensity, rainbow, moreland, nebulae, fire, fiery, fruit, cool, magma, green, viridis, plasma, cividis, terrain
            # Use intensity for custom color, or preset schemes
            # Check if custom color or use preset
            if self.color in ['#3b82f6', '#ef4444', '#10b981']:
                # Custom color - use intensity mode with gain
                gain = 2.0  # Boost visibility
                return f"{audio_input}showspectrum=s={size}:mode=combined:color=intensity:scale=log:slide=scroll:fscale=log:saturation=1:gain={gain}:rate=30[viz]"
            else:
                # For other colors, use fire/rainbow presets for best effect
                return f"{audio_input}showspectrum=s={size}:mode=combined:color=fire:scale=log:slide=scroll:fscale=log:saturation=1:rate=30[viz]"
        
        elif self.style == VisualizerStyle.MUSICAL_CQT:
            # High-quality musical frequency display with custom color
            # bar_g/sono_g control gain, bar_v/sono_v control volume
            # Higher values = more sensitive
            # Use custom color by converting to RGB values
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            # Create color expression for showcqt
            # st(0,r); st(1,g); st(2,b) sets RGB values
            basefreq = 27.5  # A0 note
            endfreq = 14080  # Musical range
            return f"{audio_input}showcqt=s={size}:fps=30:bar_g=2:sono_g=4:bar_v={self.bar_count/10}:sono_v=17:basefreq={basefreq}:endfreq={endfreq}:tlength='st(0,{r});st(1,{g});st(2,{b});0.17':fontcolor={ffmpeg_color}[viz]"
        
        elif self.style == VisualizerStyle.STEREO_SCOPE:
            # Circular stereo visualization
            size_square = f"{self.height}x{self.height}"  # Make it square
            return f"{audio_input}avectorscope=s={size_square}:r=30:zoom=1.5:draw=dot:scale=lin[viz]"
        
        # Default to spectrum bars
        return f"{audio_input}showfreqs=s={size}:mode=bar:colors={ffmpeg_color}:fscale=log:rate=30[viz]"
    
    def get_overlay_position(self) -> str:
        """Get overlay position for placing visualizer on video."""
        # Enable alpha channel support for transparency
        return f"overlay={self.x_position}:{self.y_position}:format=auto"


@dataclass
class AudioLayer:
    """Configuration for an audio layer (sound effect)."""
    file_path: str = ""
    volume: float = 1.0  # 0.0 to 2.0
    loop: bool = False
    delay_seconds: float = 0.0  # Start delay
    fade_in: float = 0.0  # Fade in duration
    fade_out: float = 0.0  # Fade out duration
    enabled: bool = True


@dataclass
class OverlayConfig:
    """Advanced overlay configuration with blend modes and chroma key."""
    enabled: bool = True
    filepath: str = ""
    
    # Blend mode settings
    blend_mode: BlendMode = BlendMode.NORMAL
    opacity: float = 1.0  # 0.0 to 1.0
    
    # Chroma key settings (optional)
    chroma_key_enabled: bool = False
    key_color: str = "#00FF00"  # Default green screen
    similarity: float = 0.3      # Color similarity threshold (0.01-1.0)
    blend: float = 0.1           # Edge blending (0.0-1.0)
    
    # Timing (loop or custom duration)
    loop: bool = True            # Loop for entire video duration
    start_time: float = 0.0      # Start time in seconds (if not looping)
    duration: float = 0.0        # Duration in seconds (0 = until end)
    
    # Position and size
    size_percent: int = 30       # Size as percentage of video width
    position: OverlayPosition = OverlayPosition.BOTTOM_LEFT
    x_offset: int = 20
    y_offset: int = 20
    
    def hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string for FFmpeg."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # FFmpeg format: 0xRRGGBB
            return f"0x{r:02X}{g:02X}{b:02X}"
        return "0x00FF00"  # Default green
    
    def get_chromakey_filter(self) -> str:
        """
        Generate FFmpeg chromakey filter string.
        Uses colorkey for better control.
        
        Returns:
            FFmpeg colorkey filter string.
        """
        if not self.filepath or not self.chroma_key_enabled:
            return ""
        
        rgb_color = self.hex_to_rgb(self.key_color)
        
        # colorkey filter: colorkey=color:similarity:blend
        return f"colorkey={rgb_color}:{self.similarity}:{self.blend}"
    
    def get_blend_mode_filter(self) -> str:
        """
        Generate FFmpeg blend mode filter.
        
        Returns:
            Blend mode parameter for overlay filter.
        """
        if self.blend_mode == BlendMode.NORMAL:
            return ""
        
        # FFmpeg blend mode names
        return self.blend_mode.value
    
    def get_scale_filter(self, video_width: int) -> str:
        """Get scale filter for the overlay."""
        overlay_width = int(video_width * self.size_percent / 100)
        return f"scale={overlay_width}:-1"
    
    def get_overlay_filter(self, video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg overlay filter string with opacity.
        Note: Blend modes require separate 'blend' filter which is complex for positioned overlays.
        For now, we only support opacity via alpha channel.
        
        Args:
            video_width: Target video width.
            video_height: Target video height.
            
        Returns:
            FFmpeg overlay filter string.
        """
        if not self.filepath:
            return ""
        
        # Get position coordinates
        x, y = self._get_position_coords(video_width, video_height)
        
        # DEBUG: Print coordinates for troubleshooting
        print(f"[OVERLAY DEBUG] Position: {self.position.value}, Size: {self.size_percent}%")
        print(f"[OVERLAY DEBUG] Coordinates: x={x}, y={y}")
        
        # Build overlay filter (without blend mode - that requires separate filter)
        overlay_str = f"overlay={x}:{y}"
        
        # Add timing if not looping
        if not self.loop and self.duration > 0:
            overlay_str += f":enable='between(t,{self.start_time},{self.start_time + self.duration})'"
        
        print(f"[OVERLAY DEBUG] Filter: {overlay_str}")
        return overlay_str
    
    def _get_position_coords(self, video_width: int, video_height: int) -> tuple:
        """Calculate position coordinates based on preset (3x3 grid)."""
        overlay_width = int(video_width * self.size_percent / 100)
        overlay_height = overlay_width  # Approximate
        
        # Top row
        if self.position == OverlayPosition.TOP_LEFT:
            return (str(self.x_offset), str(self.y_offset))
        elif self.position == OverlayPosition.TOP_CENTER:
            return ("(W-w)/2", str(self.y_offset))
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"W-w-{self.x_offset}", str(self.y_offset))
        
        # Middle row
        elif self.position == OverlayPosition.CENTER_LEFT:
            return (str(self.x_offset), "(H-h)/2")
        elif self.position == OverlayPosition.CENTER:
            return ("(W-w)/2", "(H-h)/2")
        elif self.position == OverlayPosition.CENTER_RIGHT:
            return (f"W-w-{self.x_offset}", "(H-h)/2")
        
        # Bottom row
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (str(self.x_offset), f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_CENTER:
            return ("(W-w)/2", f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"W-w-{self.x_offset}", f"H-h-{self.y_offset}")
        
        # Custom
        else:  # CUSTOM
            return (str(self.x_offset), str(self.y_offset))


# Legacy alias for backward compatibility
ChromaKeyOverlay = OverlayConfig


@dataclass
class AnimatedTextItem:
    """Single animated text with timeline."""
    text: str = ""
    start_time: float = 0.0  # Start time in seconds
    duration: float = 5.0    # How long text appears (seconds)
    fade_in: float = 1.0     # Fade in duration (seconds)
    fade_out: float = 1.0    # Fade out duration (seconds)
    
    # Styling (same as TextOverlay)
    font_file: str = ""
    font_size: int = 48
    font_color: str = "white"
    position: OverlayPosition = OverlayPosition.CENTER
    x_offset: int = 0
    y_offset: int = 0
    
    # Animation options
    enabled: bool = True
    shadow: bool = True      # Text shadow for better readability
    box: bool = False        # Background box
    box_color: str = "black@0.5"  # Semi-transparent black
    
    # Text wrapping
    max_width: int = 0       # Maximum width in pixels (0 = no wrapping)
    
    def get_end_time(self) -> float:
        """Calculate end time."""
        return self.start_time + self.duration
    
    def _wrap_text(self, text: str, max_width_px: int, font_size: int) -> str:
        """
        Manually wrap text by estimating character width.
        FFmpeg drawtext doesn't have built-in word wrap, so we do it manually.
        
        Args:
            text: Text to wrap
            max_width_px: Maximum width in pixels
            font_size: Font size in pixels
            
        Returns:
            Text with manual line breaks (\n)
        """
        if max_width_px <= 0:
            return text
        
        # Estimate: monospace ~ 0.6 * font_size, proportional ~ 0.5 * font_size avg
        avg_char_width = font_size * 0.5
        max_chars_per_line = int(max_width_px / avg_char_width)
        
        if max_chars_per_line <= 0:
            return text
        
        # Word wrap
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            # +1 for space
            if current_length + word_length + (1 if current_line else 0) <= max_chars_per_line:
                current_line.append(word)
                current_length += word_length + (1 if len(current_line) > 1 else 0)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\\n'.join(lines)  # FFmpeg uses \n for line breaks
    
    def get_drawtext_filter(self) -> str:
        """Generate FFmpeg drawtext filter with fade in/out."""
        if not self.enabled or not self.text:
            return ""
        
        # Apply text wrapping if max_width is set
        text_to_use = self._wrap_text(self.text, self.max_width, self.font_size) if self.max_width > 0 else self.text
        
        # Escape special characters
        escaped_text = text_to_use.replace("'", "\\'").replace(":", "\\:")
        
        # Position expression
        x_expr, y_expr = self._get_position_expression()
        
        # Timeline enable expression
        enable_expr = f"between(t,{self.start_time},{self.get_end_time()})"
        
        # Alpha (opacity) expression with fade in/out
        fade_in_end = self.start_time + self.fade_in
        fade_out_start = self.get_end_time() - self.fade_out
        
        alpha_expr = (
            f"if(lt(t,{fade_in_end}),"
            f"(t-{self.start_time})/{self.fade_in},"
            f"if(lt(t,{fade_out_start}),1,"
            f"(1-(t-{fade_out_start})/{self.fade_out})))"
        )
        
        # Build filter parts
        filter_parts = [
            f"text='{escaped_text}'",
            f"fontsize={self.font_size}",
            f"fontcolor={self.font_color}",
            f"x={x_expr}",
            f"y={y_expr}",
            f"enable='{enable_expr}'",
            f"alpha='{alpha_expr}'"
        ]
        
        if self.font_file and os.path.isfile(self.font_file):
            escaped_path = self.font_file.replace("\\", "/").replace(":", "\\:")
            filter_parts.insert(1, f"fontfile='{escaped_path}'")
        
        if self.shadow:
            filter_parts.append("shadowx=2")
            filter_parts.append("shadowy=2")
            filter_parts.append("shadowcolor=black@0.5")
        
        if self.box:
            filter_parts.append("box=1")
            filter_parts.append(f"boxcolor={self.box_color}")
            filter_parts.append("boxborderw=10")
        
        return "drawtext=" + ":".join(filter_parts)
    
    def _get_position_expression(self) -> tuple:
        """Get FFmpeg position expressions."""
        if self.position == OverlayPosition.TOP_LEFT:
            return (str(self.x_offset), str(self.y_offset))
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"w-text_w-{self.x_offset}", str(self.y_offset))
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (str(self.x_offset), f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"w-text_w-{self.x_offset}", f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            return ("(w-text_w)/2", "(h-text_h)/2")
        else:  # CUSTOM
            return (str(self.x_offset), str(self.y_offset))


@dataclass
class AnimatedTextTimeline:
    """Timeline for multiple animated texts."""
    enabled: bool = False
    items: List[AnimatedTextItem] = field(default_factory=list)
    
    def get_all_filters(self) -> List[str]:
        """Get all drawtext filters for enabled items."""
        filters = []
        for item in self.items:
            if item.enabled:
                filter_str = item.get_drawtext_filter()
                if filter_str:
                    filters.append(filter_str)
        return filters
    
    def sort_by_time(self):
        """Sort items by start time."""
        self.items.sort(key=lambda x: x.start_time)


@dataclass
class MediaConfig:
    """Media configuration for export."""
    mode: MediaMode = MediaMode.VIDEO_DIRECTORY
    
    # Video files mode - list of selected video files (in order)
    video_files: List[str] = field(default_factory=list)
    cover_video: str = ""  # Optional cover video (plays first)
    
    # Static image mode
    static_image: str = ""
    
    # Audio - list of selected audio files (in order)
    audio_files: List[str] = field(default_factory=list)
    audio_source: AudioSource = AudioSource.AUDIO_DIRECTORY  # Audio source mode
    audio_mix_video_volume: float = 1.0  # Volume for video audio when mixing (0.0-1.0)
    audio_mix_music_volume: float = 1.0  # Volume for music audio when mixing (0.0-1.0)
    
    # Multi-layer audio (sound effects)
    audio_layers: List[AudioLayer] = field(default_factory=list)
    
    # Loop settings
    loop_mode: LoopMode = LoopMode.MATCH_AUDIO
    custom_duration: float = 0.0  # Duration in seconds for CUSTOM_DURATION mode
    audio_multiplier: int = 1  # Multiplier for MULTIPLY_AUDIO mode
    
    # Video Scale/Zoom (for watermark removal)
    video_scale_enabled: bool = False
    video_scale_percent: int = 150  # 100-200% (1.0x - 2.0x zoom)
    
    # Video Transitions (xfade between videos)
    transition_enabled: bool = False
    transition_duration: float = 1.0  # Duration in seconds (0.5 - 3.0)
    transition_type: str = "fade"  # fade, fadeblack, fadewhite, wipeleft, etc.
    
    # Overlays
    logo_overlay: LogoOverlay = field(default_factory=LogoOverlay)
    text_overlay: TextOverlay = field(default_factory=TextOverlay)
    now_playing_config: NowPlayingConfig = field(default_factory=NowPlayingConfig)
    audio_visualizer: AudioVisualizerConfig = field(default_factory=AudioVisualizerConfig)
    
    # Subtitles/Lyrics
    subtitle_config: SubtitleConfig = field(default_factory=SubtitleConfig)
    
    # NEW: Astrofox-style visualizer
    visualizer: VisualizerConfig = field(default_factory=VisualizerConfig)
    
    # Advanced overlays (blend modes + chroma key)
    overlays: List[OverlayConfig] = field(default_factory=list)
    
    # Legacy alias for backward compatibility
    @property
    def chroma_key_overlays(self):
        """Legacy property for backward compatibility."""
        return self.overlays
    
    @chroma_key_overlays.setter
    def chroma_key_overlays(self, value):
        """Legacy setter for backward compatibility."""
        self.overlays = value
    
    # Multi-text timeline
    animated_text_timeline: AnimatedTextTimeline = field(default_factory=AnimatedTextTimeline)
    
    # Sound effect on beat (legacy, kept for compatibility)
    sfx_enabled: bool = False
    sfx_file: str = ""
    sfx_volume: float = 0.5  # 0.0 to 1.0
    beat_times: List[float] = field(default_factory=list)  # Beat positions in seconds
    
    def get_target_duration(self, audio_total_duration: float) -> float:
        """
        Calculate target duration based on loop mode.
        
        Args:
            audio_total_duration: Total duration of all audio files.
            
        Returns:
            Target duration in seconds.
        """
        if self.loop_mode == LoopMode.MATCH_AUDIO:
            return audio_total_duration
        elif self.loop_mode == LoopMode.CUSTOM_DURATION:
            return self.custom_duration
        else:  # MULTIPLY_AUDIO
            return audio_total_duration * self.audio_multiplier


class MediaManager:
    """Manages media files for the exporter."""
    
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
    
    def __init__(self):
        """Initialize MediaManager."""
        self._config = MediaConfig()
    
    @property
    def config(self) -> MediaConfig:
        """Get current media configuration."""
        return self._config
    
    @config.setter
    def config(self, value: MediaConfig) -> None:
        """Set media configuration."""
        self._config = value
    
    def get_video_files(self, directory: str, shuffle: bool = True) -> List[str]:
        """
        Get all video files from directory.
        
        Args:
            directory: Path to video directory.
            shuffle: Whether to randomize order.
            
        Returns:
            List of video file paths.
        """
        video_files = []
        dir_path = Path(directory)
        
        if dir_path.is_dir():
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix.lower() in self.VIDEO_EXTENSIONS:
                    video_files.append(str(file))
        
        if shuffle:
            random.shuffle(video_files)
        else:
            video_files.sort()
        
        return video_files
    
    def get_ordered_video_list(self, video_files: List[str], cover_video: Optional[str] = None) -> List[str]:
        """
        Get ordered list of videos with cover video first.
        
        Args:
            video_files: List of video file paths.
            cover_video: Optional cover video path (placed first).
            
        Returns:
            Ordered list of video file paths.
        """
        videos = video_files.copy()
        
        # Remove cover video from list if present
        if cover_video and cover_video in videos:
            videos.remove(cover_video)
        
        # Insert cover video at the beginning
        if cover_video and os.path.isfile(cover_video):
            videos.insert(0, cover_video)
        
        return videos
    
    def is_valid_video(self, filepath: str) -> bool:
        """Check if file is a valid video file."""
        path = Path(filepath)
        return path.is_file() and path.suffix.lower() in self.VIDEO_EXTENSIONS
    
    def is_valid_image(self, filepath: str) -> bool:
        """Check if file is a valid image file."""
        path = Path(filepath)
        return path.is_file() and path.suffix.lower() in self.IMAGE_EXTENSIONS
    
    def get_audio_files(self) -> List[str]:
        """
        Get list of audio files from config.
        
        Returns:
            List of audio file paths.
        """
        return self._config.audio_files.copy()
    
    def get_total_audio_duration(self, ffprobe_path: str = "ffprobe") -> float:
        """
        Calculate total duration of all audio files.
        
        Args:
            ffprobe_path: Path to ffprobe executable.
            
        Returns:
            Total duration in seconds.
        """
        from core.audio_utils import AudioUtils
        
        audio_utils = AudioUtils(ffprobe_path)
        total = 0.0
        for filepath in self._config.audio_files:
            duration = audio_utils.get_duration(filepath)
            if duration:
                total += duration
        return total
    
    def validate_config(self) -> List[str]:
        """
        Validate current media configuration.
        
        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        
        if self._config.mode == MediaMode.VIDEO_DIRECTORY:
            if not self._config.video_files:
                errors.append("No video files selected.")
            else:
                # Check if all video files exist
                for filepath in self._config.video_files:
                    if not os.path.isfile(filepath):
                        errors.append(f"Video file not found: {os.path.basename(filepath)}")
                        break
            
            if self._config.cover_video and not os.path.isfile(self._config.cover_video):
                errors.append("Cover video file does not exist.")
        
        elif self._config.mode == MediaMode.STATIC_IMAGE:
            if not self._config.static_image:
                errors.append("Static image is not set.")
            elif not self.is_valid_image(self._config.static_image):
                errors.append("Static image file is invalid or does not exist.")
        
        # Validate audio based on audio_source mode
        if self._config.audio_source == AudioSource.VIDEO_AUDIO:
            # Using video audio - no audio files needed
            pass
        else:
            # Using audio directory or mix both - need audio files
            if not self._config.audio_files:
                errors.append("No audio files selected.")
            else:
                # Check if all audio files exist
                for filepath in self._config.audio_files:
                    if not os.path.isfile(filepath):
                        errors.append(f"Audio file not found: {os.path.basename(filepath)}")
                        break
        
        # Validate loop settings
        if self._config.loop_mode == LoopMode.CUSTOM_DURATION:
            if self._config.custom_duration <= 0:
                errors.append("Custom duration must be greater than 0.")
        
        # Validate overlays
        if self._config.logo_overlay.enabled:
            if not self._config.logo_overlay.filepath:
                errors.append("Logo overlay is enabled but no file is selected.")
            elif not self.is_valid_image(self._config.logo_overlay.filepath):
                errors.append("Logo overlay file is invalid or does not exist.")
        
        if self._config.text_overlay.enabled:
            if not self._config.text_overlay.text:
                errors.append("Text overlay is enabled but no text is entered.")
        
        return errors
