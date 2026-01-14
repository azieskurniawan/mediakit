"""
Visualizer Renderer - Render spectrum bars and sound waves.
Inspired by Astrofox's canvas rendering.
"""
import numpy as np
from PIL import Image, ImageDraw
from typing import Tuple, Optional
import colorsys


class VisualizerRenderer:
    """Render audio visualizations to images."""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def interpolate_color(
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        t: float
    ) -> Tuple[int, int, int]:
        """
        Interpolate between two RGB colors.
        
        Args:
            color1: First RGB color.
            color2: Second RGB color.
            t: Interpolation factor (0-1).
            
        Returns:
            Interpolated RGB color.
        """
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        return (r, g, b)
    
    def render_bar_spectrum(
        self,
        spectrum_data: np.ndarray,
        width: int,
        height: int,
        shadow_height: int = 100,
        bar_width_auto: bool = True,
        bar_width: int = 10,
        bar_spacing_auto: bool = True,
        bar_spacing: int = 2,
        bar_color_start: str = "#FFFFFF",
        bar_color_end: str = "#FFFFFF",
        shadow_color_start: str = "#333333",
        shadow_color_end: str = "#000000",
        opacity: float = 1.0,
        normalize: bool = True
    ) -> Image.Image:
        """
        Render bar spectrum visualization (like Astrofox CanvasBars).
        
        Args:
            spectrum_data: Normalized spectrum values (0-1).
            width: Canvas width.
            height: Canvas height (for bars only, excluding shadow).
            shadow_height: Shadow/reflection height.
            bar_width_auto: Auto-calculate bar width.
            bar_width: Manual bar width (if not auto).
            bar_spacing_auto: Auto-calculate bar spacing.
            bar_spacing: Manual bar spacing (if not auto).
            bar_color_start: Gradient start color (hex).
            bar_color_end: Gradient end color (hex).
            shadow_color_start: Shadow gradient start color (hex).
            shadow_color_end: Shadow gradient end color (hex).
            opacity: Overall opacity (0-1).
            normalize: Normalize bar heights to max value (Astrofox default: true).
            
        Returns:
            PIL Image with rendered spectrum bars.
        """
        total_height = height + shadow_height
        img = Image.new('RGBA', (width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        bars = len(spectrum_data)
        
        # Normalize spectrum data if enabled (like Astrofox)
        if normalize and len(spectrum_data) > 0:
            max_val = np.max(spectrum_data)
            if max_val > 0:
                spectrum_data = spectrum_data / max_val
        
        # Calculate bar dimensions (like Astrofox)
        if bar_width_auto and bar_spacing_auto:
            bar_spacing = width / bars / 2
            bar_width = bar_spacing
        elif bar_spacing_auto and not bar_width_auto:
            bar_spacing = (width - bars * bar_width) / bars
            if bar_spacing <= 0:
                bar_spacing = 1
        elif not bar_spacing_auto and bar_width_auto:
            bar_width = (width - bars * bar_spacing) / bars
            if bar_width <= 0:
                bar_width = 1
        
        bar_size = bar_width + bar_spacing
        
        # Convert colors
        bar_rgb_start = self.hex_to_rgb(bar_color_start)
        bar_rgb_end = self.hex_to_rgb(bar_color_end)
        shadow_rgb_start = self.hex_to_rgb(shadow_color_start)
        shadow_rgb_end = self.hex_to_rgb(shadow_color_end)
        
        # Draw bars
        for i in range(bars):
            x = i * bar_size
            
            if x >= width:
                break
            
            # Bar height based on spectrum data
            bar_height = spectrum_data[i] * height
            
            # Interpolate color based on height (gradient)
            t = bar_height / height if height > 0 else 0
            bar_color = self.interpolate_color(bar_rgb_start, bar_rgb_end, t)
            
            # Apply opacity
            alpha = int(opacity * 255)
            bar_color_rgba = bar_color + (alpha,)
            
            # Draw bar (from bottom up)
            if bar_height > 0:
                draw.rectangle(
                    [x, height - bar_height, x + bar_width, height],
                    fill=bar_color_rgba
                )
            
            # Draw shadow/reflection (from top down)
            if shadow_height > 0:
                shadow_bar_height = spectrum_data[i] * shadow_height
                shadow_t = shadow_bar_height / shadow_height if shadow_height > 0 else 0
                shadow_color = self.interpolate_color(shadow_rgb_start, shadow_rgb_end, shadow_t)
                shadow_color_rgba = shadow_color + (alpha,)
                
                if shadow_bar_height > 0:
                    draw.rectangle(
                        [x, height, x + bar_width, height + shadow_bar_height],
                        fill=shadow_color_rgba
                    )
        
        return img
    
    def render_sound_wave(
        self,
        waveform_data: np.ndarray,
        width: int,
        height: int,
        line_width: int = 1,
        wavelength: float = 0.0,
        stroke: bool = True,
        stroke_color: str = "#FFFFFF",
        fill: bool = False,
        fill_color: str = "#FFFFFF",
        taper_edges: bool = False,
        opacity: float = 1.0
    ) -> Image.Image:
        """
        Render sound wave visualization (like Astrofox CanvasWave).
        
        Args:
            waveform_data: Normalized waveform values (0-1).
            width: Canvas width.
            height: Canvas height.
            line_width: Line thickness.
            wavelength: Wavelength compression (0-1, 0=no compression).
            stroke: Draw stroke line.
            stroke_color: Stroke color (hex).
            fill: Fill below waveform.
            fill_color: Fill color (hex).
            taper_edges: Smooth edges to midpoint.
            opacity: Overall opacity (0-1).
            
        Returns:
            PIL Image with rendered waveform.
        """
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        midpoint = height / 2
        
        # Calculate points for waveform
        num_points = len(waveform_data)
        
        # Apply wavelength compression (reduce number of points)
        if wavelength > 0:
            wavelength_max = 0.25  # Like Astrofox
            compressed_points = int(width / (wavelength * wavelength_max * width))
            if compressed_points < num_points:
                # Downsample
                indices = np.linspace(0, num_points - 1, compressed_points).astype(int)
                waveform_data = waveform_data[indices]
                num_points = compressed_points
        
        # Create point list for drawing
        step = width / (num_points - 1) if num_points > 1 else width
        points = []
        
        for i, value in enumerate(waveform_data):
            x = i * step
            # Convert 0-1 to actual y coordinate (inverted because PIL y=0 is top)
            y = height - (value * height)
            points.append((x, y))
        
        # Taper edges to midpoint
        if taper_edges and len(points) >= 2:
            points[0] = (points[0][0], midpoint)
            points[-1] = (points[-1][0], midpoint)
        
        # Convert colors
        stroke_rgb = self.hex_to_rgb(stroke_color)
        fill_rgb = self.hex_to_rgb(fill_color)
        alpha = int(opacity * 255)
        
        # Draw fill if enabled
        if fill and len(points) >= 2:
            # Create polygon: waveform + bottom line
            fill_points = points.copy()
            fill_points.append((width, midpoint))
            fill_points.append((0, midpoint))
            draw.polygon(fill_points, fill=fill_rgb + (alpha,))
        
        # Draw stroke if enabled
        if stroke and len(points) >= 2:
            try:
                draw.line(points, fill=stroke_rgb + (alpha,), width=line_width, joint='curve')
            except Exception as e:
                # Fallback if curve drawing fails
                print(f"Line drawing error: {e}, using default joint")
                draw.line(points, fill=stroke_rgb + (alpha,), width=line_width)
        
        return img
    
    def rotate_image(self, img: Image.Image, angle: int) -> Image.Image:
        """
        Rotate image.
        
        Args:
            img: Input image.
            angle: Rotation angle in degrees.
            
        Returns:
            Rotated image.
        """
        if angle == 0:
            return img
        
        return img.rotate(-angle, expand=True, fillcolor=(0, 0, 0, 0))
    
    def composite_visualizer(
        self,
        visualizer_img: Image.Image,
        base_img: Image.Image,
        x: int,
        y: int,
        rotation: int = 0
    ) -> Image.Image:
        """
        Composite visualizer onto base image.
        
        Args:
            visualizer_img: Visualizer image (RGBA).
            base_img: Base video frame image.
            x: X position (can be negative).
            y: Y position (can be negative).
            rotation: Rotation angle in degrees.
            
        Returns:
            Composited image.
        """
        # Rotate if needed
        if rotation != 0:
            visualizer_img = self.rotate_image(visualizer_img, rotation)
        
        # Composite at position
        result = base_img.copy()
        result.paste(visualizer_img, (x, y), visualizer_img)
        
        return result

