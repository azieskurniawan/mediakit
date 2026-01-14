"""
Visualizer Preview Generator - Generate preview videos for visualizers.
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
import numpy as np

from core.audio_analyzer import AudioAnalyzer
from core.visualizer_renderer import VisualizerRenderer
from core.media_manager import VisualizerConfig, VisualizerType


class VisualizerPreviewGenerator:
    """Generate preview videos for audio visualizers."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize preview generator.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable.
        """
        self.ffmpeg_path = ffmpeg_path
        self.analyzer = AudioAnalyzer(ffmpeg_path=ffmpeg_path)
        self.renderer = VisualizerRenderer()
    
    def generate_preview(
        self,
        audio_files: List[str],
        visualizer_config: VisualizerConfig,
        output_file: str,
        duration: float = 10.0,
        fps: int = 30,
        width: int = 1920,
        height: int = 1080,
        background_color: str = "#000000",
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Generate a preview video with visualizer (first 10 seconds of all audio).
        
        Strategy: Concat first 10 seconds from each audio, then generate visualizer.
        
        Args:
            audio_files: List of audio file paths.
            visualizer_config: Visualizer configuration.
            output_file: Output video file path.
            duration: Total preview duration in seconds.
            fps: Frames per second.
            width: Video width.
            height: Video height.
            background_color: Background color (hex).
            progress_callback: Optional callback for progress updates.
            
        Returns:
            True if successful, False otherwise.
        """
        if visualizer_config.type == VisualizerType.NONE or not audio_files:
            return False
        
        try:
            # Create temporary concat audio file
            temp_audio = self._concat_audio_samples(audio_files, duration)
            
            if not temp_audio:
                return False
            
            # Generate frames with visualizer
            total_frames = int(duration * fps)
            temp_frames_dir = tempfile.mkdtemp()
            
            # Initialize smoothing buffers
            spectrum_buffer = np.array([])
            waveform_buffer = np.array([])
            
            for frame_idx in range(total_frames):
                frame_time = frame_idx / fps
                
                try:
                    # Get max_db from config for consistent byte mapping
                    if visualizer_config.type == VisualizerType.BAR_SPECTRUM:
                        max_db_config = visualizer_config.bar_spectrum.max_db
                    else:
                        max_db_config = -30  # Default for sound wave
                    
                    # Analyze audio at this frame time
                    # IMPORTANT: Pass min_db/max_db for consistent byte conversion
                    spectrum_byte, waveform_samples = self.analyzer.analyze_audio_for_frame(
                        temp_audio,
                        frame_time,
                        fft_size=2048,
                        sample_window=0.05,
                        min_db=-100,  # Astrofox default
                        max_db=max_db_config
                    )
                    
                    # Create base frame (background)
                    # Support transparent background for overlay
                    if background_color == "#00000000":
                        frame_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    else:
                        frame_img = Image.new('RGB', (width, height), background_color)
                    
                    # Render visualizer based on type
                    if visualizer_config.type == VisualizerType.BAR_SPECTRUM:
                        viz_img = self._render_bar_spectrum_frame(
                            spectrum_byte,
                            visualizer_config.bar_spectrum,
                            spectrum_buffer
                        )
                    elif visualizer_config.type == VisualizerType.SOUND_WAVE:
                        viz_img = self._render_sound_wave_frame(
                            waveform_samples,
                            visualizer_config.sound_wave,
                            waveform_buffer
                        )
                    else:
                        viz_img = None
                    
                    # Composite visualizer onto frame
                    if viz_img:
                        if visualizer_config.type == VisualizerType.BAR_SPECTRUM:
                            x = visualizer_config.bar_spectrum.x
                            y = visualizer_config.bar_spectrum.y
                            rotation = visualizer_config.bar_spectrum.rotation
                        else:  # SOUND_WAVE
                            x = visualizer_config.sound_wave.x
                            y = visualizer_config.sound_wave.y
                            rotation = visualizer_config.sound_wave.rotation
                        
                        # Apply rotation if needed
                        if rotation != 0:
                            viz_img = viz_img.rotate(-rotation, expand=True, fillcolor=(0, 0, 0, 0))
                        
                        # Paste visualizer onto frame at position
                        frame_img.paste(viz_img, (x, y), viz_img)
                    
                    # Save frame
                    frame_path = os.path.join(temp_frames_dir, f"frame_{frame_idx:06d}.png")
                    frame_img.save(frame_path)
                    
                    # Progress callback
                    if progress_callback:
                        progress = (frame_idx + 1) / total_frames
                        progress_callback(progress, f"Rendering frame {frame_idx + 1}/{total_frames}")
                
                except Exception as e:
                    print(f"Error rendering frame {frame_idx}: {e}")
                    continue
            
            # Encode frames to video with audio
            success = self._encode_video(
                temp_frames_dir,
                temp_audio,
                output_file,
                fps,
                width,
                height
            )
            
            # Cleanup
            self._cleanup_temp_files(temp_audio, temp_frames_dir)
            
            return success
            
        except Exception as e:
            print(f"Preview generation failed: {e}")
            return False
    
    def _concat_audio_samples(
        self,
        audio_files: List[str],
        total_duration: float
    ) -> Optional[str]:
        """
        Concatenate first N seconds from each audio file.
        
        Args:
            audio_files: List of audio files.
            total_duration: Total duration to extract.
            
        Returns:
            Path to temporary concatenated audio file, or None if failed.
        """
        if not audio_files:
            return None
        
        try:
            # Calculate duration per audio
            duration_per_audio = total_duration / len(audio_files)
            
            # Create temp concat file list
            concat_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_audio_files = []
            
            for audio_file in audio_files:
                # Extract first N seconds
                temp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                temp_audio.close()
                temp_audio_files.append(temp_audio.name)
                
                cmd = [
                    self.ffmpeg_path,
                    '-v', 'error',
                    '-i', audio_file,
                    '-t', str(duration_per_audio),
                    '-c:a', 'libmp3lame',
                    '-q:a', '2',
                    temp_audio.name
                ]
                
                subprocess.run(cmd, check=True)
                
                # Add to concat list
                concat_list.write(f"file '{temp_audio.name}'\n")
            
            concat_list.close()
            
            # Concatenate all audio files
            output_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            output_audio.close()
            
            cmd = [
                self.ffmpeg_path,
                '-v', 'error',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list.name,
                '-c', 'copy',
                output_audio.name
            ]
            
            subprocess.run(cmd, check=True)
            
            # Cleanup temp files
            os.unlink(concat_list.name)
            for temp_file in temp_audio_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            return output_audio.name
            
        except Exception as e:
            print(f"Audio concatenation failed: {e}")
            return None
    
    def _render_bar_spectrum_frame(
        self,
        spectrum_byte: np.ndarray,
        config,
        smoothing_buffer: np.ndarray
    ) -> Image.Image:
        """Render bar spectrum for a single frame."""
        # Calculate actual number of bins based on frequency range (like Astrofox)
        sample_rate = self.analyzer.sample_rate
        fft_size = 2048
        freq_per_bin = sample_rate / fft_size  # ~21.5 Hz per bin
        
        # Calculate bins in frequency range
        min_bin = int(config.min_frequency / freq_per_bin)
        max_bin = int(config.max_frequency / freq_per_bin)
        num_bins = max_bin - min_bin
        
        # Clamp to reasonable range
        num_bins = max(1, min(num_bins, 500))
        
        # Parse spectrum with correct bin count (EXACT Astrofox algorithm)
        spectrum_normalized = self.analyzer.parse_fft_spectrum(
            spectrum_byte,
            min_db=-100,  # Astrofox default
            max_db=config.max_db,
            min_freq=config.min_frequency,
            max_freq=config.max_frequency,
            num_bins=num_bins,  # Use frequency-based bin count, not width-based!
            smoothing=config.smoothing,
            smoothing_buffer=smoothing_buffer,
            normalize=config.normalize  # Astrofox default: True for BarSpectrum
        )
        
        # Render bars
        return self.renderer.render_bar_spectrum(
            spectrum_normalized,
            config.width,
            config.height,
            shadow_height=config.shadow_height,
            bar_width_auto=config.bar_width_auto,
            bar_width=config.bar_width,
            bar_spacing_auto=config.bar_spacing_auto,
            bar_spacing=config.bar_spacing,
            bar_color_start=config.bar_color_start,
            bar_color_end=config.bar_color_end,
            shadow_color_start=config.shadow_color_start,
            shadow_color_end=config.shadow_color_end,
            opacity=config.opacity,
            normalize=config.normalize
        )
    
    def _render_sound_wave_frame(
        self,
        waveform_samples: np.ndarray,
        config,
        smoothing_buffer: np.ndarray
    ) -> Image.Image:
        """Render sound wave for a single frame."""
        # Parse waveform
        waveform_normalized = self.analyzer.parse_waveform(
            waveform_samples,
            num_points=config.width,
            smoothing=config.smoothing,
            smoothing_buffer=smoothing_buffer
        )
        
        # Render waveform
        return self.renderer.render_sound_wave(
            waveform_normalized,
            config.width,
            config.height,
            line_width=config.line_width,
            wavelength=config.wavelength,
            stroke=config.stroke,
            stroke_color=config.stroke_color,
            fill=config.fill,
            fill_color=config.fill_color,
            taper_edges=config.taper_edges,
            opacity=config.opacity
        )
    
    def _encode_video(
        self,
        frames_dir: str,
        audio_file: str,
        output_file: str,
        fps: int,
        width: int,
        height: int
    ) -> bool:
        """Encode frames to video with audio."""
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-framerate', str(fps),
                '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                '-i', audio_file,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_file
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return True
            
        except Exception as e:
            print(f"Video encoding failed: {e}")
            return False
    
    def _cleanup_temp_files(self, temp_audio: str, temp_frames_dir: str):
        """Clean up temporary files."""
        try:
            if temp_audio and os.path.exists(temp_audio):
                os.unlink(temp_audio)
        except:
            pass
        
        try:
            if temp_frames_dir and os.path.exists(temp_frames_dir):
                import shutil
                shutil.rmtree(temp_frames_dir)
        except:
            pass

