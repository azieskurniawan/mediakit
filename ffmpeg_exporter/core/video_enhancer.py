"""
Video Enhancement Engine.
Supports AI upscaling (Real-ESRGAN) and fast enhancement (FFmpeg).
"""
import os
import subprocess
import tempfile
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path
import urllib.request
import shutil


class EnhanceMethod(Enum):
    """Enhancement method."""
    FFMPEG_FAST = "ffmpeg_fast"
    FFMPEG_QUALITY = "ffmpeg_quality"
    REALESRGAN_2X = "realesrgan_2x"
    REALESRGAN_4X = "realesrgan_4x"


class EnhancePreset(Enum):
    """Enhancement preset."""
    SUBTLE = "subtle"
    NORMAL = "normal"
    STRONG = "strong"
    MAXIMUM = "maximum"


@dataclass
class EnhanceSettings:
    """Video enhancement settings."""
    method: EnhanceMethod = EnhanceMethod.FFMPEG_QUALITY
    preset: EnhancePreset = EnhancePreset.NORMAL
    sharpen: bool = True
    denoise: bool = True
    enhance_colors: bool = True
    upscale_factor: int = 1  # 1 = keep original, 2 = 2x, 4 = 4x
    output_directory: str = ""
    use_gpu: bool = True  # Use GPU if available (for Real-ESRGAN)
    bitrate_mode: int = 0  # 0=Auto, 1=High, 2=Maximum, 3=Custom
    custom_bitrate: Optional[int] = None  # kbps, used when bitrate_mode=3
    
    @property
    def requires_gpu(self) -> bool:
        """Check if method requires GPU."""
        return self.method in [EnhanceMethod.REALESRGAN_2X, EnhanceMethod.REALESRGAN_4X]


class VideoEnhancer:
    """Video enhancement engine."""
    
    # Real-ESRGAN model URLs
    MODEL_URLS = {
        'RealESRGAN_x2plus': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth',
        'RealESRGAN_x4plus': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
    }
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize video enhancer.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable.
        """
        self.ffmpeg_path = ffmpeg_path
        self._realesrgan_available = self._check_realesrgan()
        self._weights_dir = Path('weights')
        self._weights_dir.mkdir(exist_ok=True)
    
    def _check_realesrgan(self) -> bool:
        """Check if Real-ESRGAN is available."""
        try:
            import torch
            import realesrgan
            # Check if CUDA is available (optional, but good to know)
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                print(f"✅ Real-ESRGAN available with GPU: {torch.cuda.get_device_name(0)}")
            else:
                print(f"✅ Real-ESRGAN available (CPU only)")
            return True
        except Exception as e:
            print(f"❌ Real-ESRGAN not available: {e}")
            return False
    
    def is_realesrgan_available(self) -> bool:
        """Check if Real-ESRGAN is installed."""
        return self._realesrgan_available
    
    def _download_model_weights(self, model_name: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Download Real-ESRGAN model weights if not exists.
        
        Args:
            model_name: Model name (e.g., 'RealESRGAN_x2plus').
            progress_callback: Callback for download progress.
            
        Returns:
            True if successful or already exists, False otherwise.
        """
        model_path = self._weights_dir / f'{model_name}.pth'
        
        # Check if already exists
        if model_path.exists():
            print(f"✅ Model weights found: {model_path}")
            return True
        
        # Get download URL
        if model_name not in self.MODEL_URLS:
            print(f"❌ Unknown model: {model_name}")
            return False
        
        url = self.MODEL_URLS[model_name]
        print(f"\n📥 Downloading {model_name} model weights...")
        print(f"   Source: {url}")
        print(f"   Target: {model_path}")
        print(f"   Size: ~65 MB (this may take 1-2 minutes)\n")
        
        try:
            # Download with progress
            def reporthook(count, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = count * block_size
                    percent = min(int(downloaded * 100 / total_size), 100)
                    if count % 50 == 0:  # Print every 50 blocks
                        print(f"   Progress: {percent}% ({downloaded // 1024 // 1024} MB / {total_size // 1024 // 1024} MB)")
            
            # Download to temporary file first
            temp_path = model_path.with_suffix('.tmp')
            urllib.request.urlretrieve(url, temp_path, reporthook)
            
            # Move to final location
            shutil.move(str(temp_path), str(model_path))
            
            print(f"✅ Download complete: {model_path}\n")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def enhance_video_ffmpeg(
        self,
        input_path: str,
        output_path: str,
        settings: EnhanceSettings,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Enhance video using FFmpeg filters.
        
        Args:
            input_path: Input video path.
            output_path: Output video path.
            settings: Enhancement settings.
            progress_callback: Callback for progress (current_frame, total_frames).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Build filter chain
            filters = []
            
            # Denoise filter
            if settings.denoise:
                denoise_strength = self._get_denoise_strength(settings.preset)
                filters.append(f"hqdn3d={denoise_strength}")
            
            # Color enhancement
            if settings.enhance_colors:
                color_params = self._get_color_params(settings.preset)
                filters.append(color_params)
            
            # Sharpening
            if settings.sharpen:
                sharpen_params = self._get_sharpen_params(settings.preset)
                filters.append(sharpen_params)
            
            # Upscaling
            if settings.upscale_factor > 1:
                # Get input dimensions
                width, height = self._get_video_dimensions(input_path)
                new_width = width * settings.upscale_factor
                new_height = height * settings.upscale_factor
                filters.append(f"scale={new_width}:{new_height}:flags=lanczos")
            
            # Build FFmpeg command
            filter_str = ",".join(filters) if filters else "null"
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', filter_str,
                '-c:v', 'libx264',
                '-preset', 'slow' if settings.method == EnhanceMethod.FFMPEG_QUALITY else 'medium',
                '-crf', '18',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            print(f"\n{'='*60}")
            print("FFmpeg Enhancement Command:")
            print(' '.join(cmd))
            print(f"{'='*60}\n")
            
            # Execute
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Track progress
            total_frames = self._get_video_frame_count(input_path)
            current_frame = 0
            
            for line in process.stdout:
                print(line.rstrip())
                
                # Parse frame progress
                if 'frame=' in line:
                    try:
                        frame_str = line.split('frame=')[1].split()[0]
                        current_frame = int(frame_str)
                        if progress_callback and total_frames > 0:
                            progress_callback(current_frame, total_frames)
                    except:
                        pass
            
            process.wait()
            return process.returncode == 0
            
        except Exception as e:
            print(f"FFmpeg enhancement error: {e}")
            return False
    
    def enhance_video_realesrgan(
        self,
        input_path: str,
        output_path: str,
        settings: EnhanceSettings,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Enhance video using Real-ESRGAN AI upscaling.
        
        Args:
            input_path: Input video path.
            output_path: Output video path.
            settings: Enhancement settings.
            progress_callback: Callback for progress (current_frame, total_frames).
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.is_realesrgan_available():
            print("Real-ESRGAN not available!")
            return False
        
        try:
            import cv2
            import torch
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            
            print(f"\n{'='*60}")
            print("Real-ESRGAN AI Enhancement")
            print(f"Input: {input_path}")
            print(f"Scale: {settings.upscale_factor}x")
            print(f"{'='*60}\n")
            
            # Determine model
            if settings.method == EnhanceMethod.REALESRGAN_2X:
                model_name = 'RealESRGAN_x2plus'
                scale = 2
            else:
                model_name = 'RealESRGAN_x4plus'
                scale = 4
            
            # Download model weights if needed
            if not self._download_model_weights(model_name, progress_callback):
                print(f"❌ Failed to download model weights: {model_name}")
                return False
            
            # Create model
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=scale)
            
            # Model path
            model_path = str(self._weights_dir / f'{model_name}.pth')
            
            # Determine device (GPU or CPU based on settings and availability)
            use_gpu = settings.use_gpu and torch.cuda.is_available()
            
            if use_gpu:
                print(f"🎮 Using GPU: {torch.cuda.get_device_name(0)}")
                print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                if settings.use_gpu and not torch.cuda.is_available():
                    print("⚠️ GPU requested but not available, falling back to CPU")
                else:
                    print("💻 Using CPU (this will be MUCH slower)")
            
            # Create upsampler
            upsampler = RealESRGANer(
                scale=scale,
                model_path=model_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=True if use_gpu else False,
                gpu_id=0 if use_gpu else None
            )
            
            # Open video
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                print("Cannot get frame count")
                return False
            
            # Get output dimensions from first frame
            ret, frame = cap.read()
            if not ret:
                print("Cannot read first frame")
                return False
            
            output, _ = upsampler.enhance(frame, outscale=scale)
            h, w = output.shape[:2]
            
            print(f"Output resolution: {w}x{h}")
            
            # Calculate appropriate bitrate based on resolution and mode
            pixels = w * h
            
            # Base bitrate (Auto mode)
            if pixels <= 1920*1080:  # 1080p
                base_bitrate = 12000  # 12 Mbps
            elif pixels <= 2560*1440:  # 1440p
                base_bitrate = 18000  # 18 Mbps
            elif pixels <= 3840*2160:  # 4K
                base_bitrate = 35000  # 35 Mbps
            else:  # 8K+
                base_bitrate = 100000  # 100 Mbps
            
            # Apply bitrate mode
            if settings.bitrate_mode == 0:  # Auto
                target_bitrate = base_bitrate
                mode_name = "Auto"
            elif settings.bitrate_mode == 1:  # High (1.5x)
                target_bitrate = int(base_bitrate * 1.5)
                mode_name = "High (1.5x)"
            elif settings.bitrate_mode == 2:  # Maximum (4K-level for all, like Topaz!)
                target_bitrate = 35000  # Always 35 Mbps
                mode_name = "Maximum (Topaz-style)"
            elif settings.bitrate_mode == 3:  # Custom
                target_bitrate = settings.custom_bitrate if settings.custom_bitrate else base_bitrate
                mode_name = "Custom"
            else:
                target_bitrate = base_bitrate
                mode_name = "Auto"
            
            print(f"Bitrate mode: {mode_name}")
            print(f"Target bitrate: {target_bitrate/1000:.1f} Mbps")
            
            # Create temporary raw output (uncompressed)
            import tempfile
            temp_raw = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
            temp_raw_path = temp_raw.name
            temp_raw.close()
            
            # Use lossless codec for temporary file (MJPEG for compatibility)
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(temp_raw_path, fourcc, fps, (w, h))
            
            if not out.isOpened():
                print("❌ Failed to create temporary video writer")
                return False
            
            # Reset to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # Process each frame
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Enhance frame
                output, _ = upsampler.enhance(frame, outscale=scale)
                
                # Write to output
                out.write(output)
                
                # Progress
                frame_idx += 1
                if progress_callback:
                    progress_callback(frame_idx, total_frames)
                
                if frame_idx % 30 == 0:
                    print(f"Processed {frame_idx}/{total_frames} frames ({frame_idx*100//total_frames}%)")
            
            # Cleanup
            cap.release()
            out.release()
            
            print(f"\n✅ AI Enhancement complete! Re-encoding with high bitrate...")
            
            # Re-encode with FFmpeg for proper H.264 encoding with high bitrate
            ffmpeg_command = [
                self.ffmpeg_path,
                '-i', temp_raw_path,
                '-c:v', 'libx264',
                '-preset', 'slow',  # Slow = best quality
                '-crf', '18',  # CRF 18 = very high quality (lower = better)
                '-b:v', f'{target_bitrate}k',
                '-maxrate', f'{target_bitrate}k',
                '-bufsize', f'{target_bitrate*2}k',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-y',
                output_path
            ]
            
            print(f"FFmpeg command: {' '.join(ffmpeg_command)}")
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True
            )
            
            # Remove temporary file
            import os
            try:
                os.remove(temp_raw_path)
            except:
                pass
            
            if result.returncode != 0:
                print(f"❌ FFmpeg encoding failed: {result.stderr}")
                return False
            
            print(f"\n✅ Enhancement complete!")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            import traceback
            print(f"Real-ESRGAN enhancement error: {e}")
            print(traceback.format_exc())
            return False
    
    def enhance_video(
        self,
        input_path: str,
        output_path: str,
        settings: EnhanceSettings,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Enhance video using selected method.
        
        Args:
            input_path: Input video path.
            output_path: Output video path.
            settings: Enhancement settings.
            progress_callback: Callback for progress.
            
        Returns:
            True if successful, False otherwise.
        """
        # Use appropriate method
        if settings.method in [EnhanceMethod.REALESRGAN_2X, EnhanceMethod.REALESRGAN_4X]:
            return self.enhance_video_realesrgan(input_path, output_path, settings, progress_callback)
        else:
            return self.enhance_video_ffmpeg(input_path, output_path, settings, progress_callback)
    
    def _get_denoise_strength(self, preset: EnhancePreset) -> str:
        """Get denoise filter parameters based on preset."""
        params = {
            EnhancePreset.SUBTLE: "1.5:1.5:6:6",
            EnhancePreset.NORMAL: "2:2:8:8",
            EnhancePreset.STRONG: "3:3:10:10",
            EnhancePreset.MAXIMUM: "4:4:12:12"
        }
        return params.get(preset, params[EnhancePreset.NORMAL])
    
    def _get_color_params(self, preset: EnhancePreset) -> str:
        """Get color enhancement parameters based on preset."""
        params = {
            EnhancePreset.SUBTLE: "eq=contrast=1.03:brightness=0.01:saturation=1.03",
            EnhancePreset.NORMAL: "eq=contrast=1.05:brightness=0.02:saturation=1.05",
            EnhancePreset.STRONG: "eq=contrast=1.08:brightness=0.03:saturation=1.08",
            EnhancePreset.MAXIMUM: "eq=contrast=1.1:brightness=0.04:saturation=1.1"
        }
        return params.get(preset, params[EnhancePreset.NORMAL])
    
    def _get_sharpen_params(self, preset: EnhancePreset) -> str:
        """Get sharpening parameters based on preset."""
        params = {
            EnhancePreset.SUBTLE: "unsharp=5:5:0.5:5:5:0.0",
            EnhancePreset.NORMAL: "unsharp=5:5:1.0:5:5:0.0",
            EnhancePreset.STRONG: "unsharp=7:7:1.3:5:5:0.0",
            EnhancePreset.MAXIMUM: "unsharp=7:7:1.5:5:5:0.0"
        }
        return params.get(preset, params[EnhancePreset.NORMAL])
    
    def _get_video_dimensions(self, video_path: str) -> tuple:
        """Get video dimensions (width, height)."""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-f', 'null',
                '-'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = result.stderr
            
            # Parse dimensions from output
            import re
            match = re.search(r'(\d{3,5})x(\d{3,5})', output)
            if match:
                return int(match.group(1)), int(match.group(2))
            
            return 1920, 1080  # Default
        except:
            return 1920, 1080
    
    def _get_video_frame_count(self, video_path: str) -> int:
        """Get total frame count of video."""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-map', '0:v:0',
                '-c', 'copy',
                '-f', 'null',
                '-'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stderr
            
            # Parse frame count
            import re
            match = re.search(r'frame=\s*(\d+)', output)
            if match:
                return int(match.group(1))
            
            return 0
        except:
            return 0

