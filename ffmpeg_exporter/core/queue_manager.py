"""
Export Queue Manager
Manages batch export jobs with sequential processing.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable
from enum import Enum

from core.media_manager import MediaConfig
from core.ffmpeg_builder import ExportSettings


class JobStatus(Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportJob:
    """Single export job in queue."""
    id: str
    name: str
    media_config: MediaConfig
    export_settings: ExportSettings
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0-100
    created_time: str = ""
    started_time: Optional[str] = None
    finished_time: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert job to dict for JSON serialization."""
        def serialize_value(obj):
            """Recursively serialize objects, converting Enum to value."""
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_value(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return serialize_value(asdict(obj))
            else:
                return obj
        
        return {
            'id': self.id,
            'name': self.name,
            'media_config': serialize_value(asdict(self.media_config)),
            'export_settings': serialize_value(asdict(self.export_settings)),
            'status': self.status.value,
            'progress': self.progress,
            'created_time': self.created_time,
            'started_time': self.started_time,
            'finished_time': self.finished_time,
            'error_message': self.error_message
        }
    
    @staticmethod
    def from_dict(data: dict) -> Optional['ExportJob']:
        """Create job from dict, reconstructing Enum fields. Returns None if corrupt."""
        try:
            from core.media_manager import (
                MediaMode, LoopMode, AudioSource, OverlayPosition, 
                VisualizerType, BlendMode, LogoOverlay, TextOverlay,
                NowPlayingConfig, VisualizerConfig
            )
            from core.ffmpeg_builder import VideoCodec, AudioCodec, RateControl, EncodingMethod
            
            # Reconstruct media_config with Enum conversion
            mc_data = data['media_config']
            
            # Convert logo_overlay if present
            logo_overlay = None
            if mc_data.get('logo_overlay'):
                logo_data = mc_data['logo_overlay']
                logo_overlay = LogoOverlay(
                    enabled=logo_data.get('enabled', False),
                    filepath=logo_data.get('filepath', ''),
                    size_percent=logo_data.get('size_percent', 15),
                    position=OverlayPosition(logo_data.get('position', 'top_right')),
                    x_offset=logo_data.get('x_offset', 20),
                    y_offset=logo_data.get('y_offset', 20)
                )
            
            # Convert text_overlay if present
            text_overlay = None
            if mc_data.get('text_overlay'):
                text_data = mc_data['text_overlay']
                text_overlay = TextOverlay(
                    enabled=text_data.get('enabled', False),
                    text=text_data.get('text', ''),
                    font_file=text_data.get('font_file', ''),
                    font_size=text_data.get('font_size', 40),
                    font_color=text_data.get('font_color', 'white'),
                    position=OverlayPosition(text_data.get('position', 'bottom_center')),
                    x_offset=text_data.get('x_offset', 0),
                    y_offset=text_data.get('y_offset', 50)
                )
            
            # Convert now_playing_config if present
            now_playing_config = None
            if mc_data.get('now_playing_config'):
                np_data = mc_data['now_playing_config']
                now_playing_config = NowPlayingConfig(
                    enabled=np_data.get('enabled', False),
                    font_file=np_data.get('font_file', ''),
                    font_size=np_data.get('font_size', 36),
                    font_color=np_data.get('font_color', 'white'),
                    position=OverlayPosition(np_data.get('position', 'bottom_center')),
                    x_offset=np_data.get('x_offset', 0),
                    y_offset=np_data.get('y_offset', 40),
                    start_offset_seconds=float(np_data.get('start_offset_seconds', 0))
                )
            
            # Convert visualizer_config if present
            visualizer_config = None
            if mc_data.get('visualizer_config'):
                viz_data = mc_data['visualizer_config']
                visualizer_config = VisualizerConfig(
                    enabled=viz_data.get('enabled', False),
                    video_path=viz_data.get('video_path', ''),
                    size_percent=viz_data.get('size_percent', 20),
                    position=OverlayPosition(viz_data.get('position', 'center')),
                    x_offset=viz_data.get('x_offset', 0),
                    y_offset=viz_data.get('y_offset', 0),
                    loop_mode=LoopMode(viz_data.get('loop_mode', 'match_audio')),
                    blend_mode=BlendMode(viz_data.get('blend_mode', 'normal')),
                    chroma_key_enabled=viz_data.get('chroma_key_enabled', False),
                    chroma_key_color=viz_data.get('chroma_key_color', '#000000'),
                    chroma_similarity=viz_data.get('chroma_similarity', 0.3),
                    chroma_blend=viz_data.get('chroma_blend', 0.1)
                )
            
            media_config = MediaConfig(
                mode=MediaMode(mc_data.get('mode', 'video_directory')),
                video_files=mc_data.get('video_files', []),
                static_image=mc_data.get('static_image', ''),
                cover_video=mc_data.get('cover_video', ''),
                audio_files=mc_data.get('audio_files', []),
                audio_source=AudioSource(mc_data.get('audio_source', 'audio_directory')),
                audio_mix_video_volume=mc_data.get('audio_mix_video_volume', 1.0),
                audio_mix_music_volume=mc_data.get('audio_mix_music_volume', 1.0),
                loop_mode=LoopMode(mc_data.get('loop_mode', 'match_audio')),
                custom_duration=mc_data.get('custom_duration', 0.0),
                audio_multiplier=mc_data.get('audio_multiplier', 1),
                video_scale_enabled=mc_data.get('video_scale_enabled', False),
                video_scale_percent=mc_data.get('video_scale_percent', 150),
                transition_enabled=mc_data.get('transition_enabled', False),
                transition_duration=mc_data.get('transition_duration', 1.0),
                transition_type=mc_data.get('transition_type', 'fade'),
                logo_overlay=logo_overlay or LogoOverlay(),
                text_overlay=text_overlay or TextOverlay(),
                now_playing_config=now_playing_config or NowPlayingConfig(),
                visualizer=visualizer_config or VisualizerConfig(),
                overlays=mc_data.get('overlays', [])
            )
            
            # Reconstruct export_settings with Enum conversion
            es_data = data['export_settings']
            export_settings = ExportSettings(
                width=es_data.get('width', 1920),
                height=es_data.get('height', 1080),
                fps=es_data.get('fps', 30),
                encoding_method=EncodingMethod(es_data.get('encoding_method', 'nvenc_hq')),
                video_codec=VideoCodec(es_data.get('video_codec', 'h264')),
                rate_control=RateControl(es_data.get('rate_control', 'crf')),
                crf_value=es_data.get('crf_value', 23),
                bitrate_kbps=es_data.get('bitrate_kbps', 4000),
                audio_codec=AudioCodec(es_data.get('audio_codec', 'aac')),
                audio_bitrate_kbps=es_data.get('audio_bitrate_kbps', 192),
                output_filename=es_data.get('output_filename', 'output.mp4'),
                output_directory=es_data.get('output_directory', '')
            )
            
            # Create job object
            job = ExportJob(
                id=data['id'],
                name=data['name'],
                media_config=media_config,
                export_settings=export_settings,
                status=JobStatus(data['status']),
                progress=data.get('progress', 0.0),
                created_time=data.get('created_time', ''),
                started_time=data.get('started_time'),
                finished_time=data.get('finished_time'),
                error_message=data.get('error_message')
            )
            
            # CRITICAL: Validate reconstructed object before returning
            # Test if object is accessible without recursion
            _ = job.status.value  # Force evaluate
            _ = job.name  # Force evaluate
            _ = job.id  # Force evaluate
            
            return job
            
        except Exception as e:
            # Any error = corrupt job, return None to skip it
            print(f"[QUEUE] Failed to deserialize job: {e}")
            return None


class QueueManager:
    """
    Manages export queue with sequential processing.
    Singleton pattern to ensure one queue manager per app.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._jobs: List[ExportJob] = []
        self._is_processing = False
        self._current_job: Optional[ExportJob] = None
        self._queue_file = Path("config/export_queue.json")
        
        # Callbacks
        self._on_job_started: Optional[Callable] = None
        self._on_job_progress: Optional[Callable] = None
        self._on_job_completed: Optional[Callable] = None
        self._on_job_failed: Optional[Callable] = None
        self._on_queue_finished: Optional[Callable] = None
        self._on_queue_changed: Optional[Callable] = None
        
        # Load saved queue
        self.load_queue()
    
    def add_job(self, media_config: MediaConfig, export_settings: ExportSettings, name: Optional[str] = None) -> ExportJob:
        """
        Add new job to queue.
        
        Args:
            media_config: Media configuration
            export_settings: Export settings
            name: Optional job name (auto-generated if None)
            
        Returns:
            Created ExportJob
        """
        # Auto-generate name if not provided
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"Export_{timestamp}"
        
        job = ExportJob(
            id=str(uuid.uuid4()),
            name=name,
            media_config=media_config,
            export_settings=export_settings,
            created_time=datetime.now().isoformat()
        )
        
        self._jobs.append(job)
        self._notify_queue_changed()
        self.save_queue()
        
        return job
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove job from queue.
        Cannot remove job that is currently processing.
        
        Args:
            job_id: Job ID to remove
            
        Returns:
            True if removed, False if not found or currently processing
        """
        # Don't remove current processing job
        if self._current_job and self._current_job.id == job_id:
            return False
        
        for i, job in enumerate(self._jobs):
            if job.id == job_id:
                self._jobs.pop(i)
                self._notify_queue_changed()
                self.save_queue()
                return True
        
        return False
    
    def move_job(self, job_id: str, new_index: int) -> bool:
        """
        Reorder job in queue.
        
        Args:
            job_id: Job ID to move
            new_index: New position (0-based)
            
        Returns:
            True if moved successfully
        """
        # Find current index
        current_index = None
        for i, job in enumerate(self._jobs):
            if job.id == job_id:
                current_index = i
                break
        
        if current_index is None:
            return False
        
        # Don't move processing job
        if self._current_job and self._current_job.id == job_id:
            return False
        
        # Move job
        job = self._jobs.pop(current_index)
        self._jobs.insert(new_index, job)
        
        self._notify_queue_changed()
        self.save_queue()
        return True
    
    def get_jobs(self) -> List[ExportJob]:
        """Get all jobs in queue."""
        return self._jobs.copy()
    
    def get_job(self, job_id: str) -> Optional[ExportJob]:
        """Get specific job by ID."""
        for job in self._jobs:
            if job.id == job_id:
                return job
        return None
    
    def clear_completed(self):
        """Remove all completed/failed jobs from queue."""
        self._jobs = [
            job for job in self._jobs 
            if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        self._notify_queue_changed()
        self.save_queue()
    
    def is_processing(self) -> bool:
        """Check if queue is currently processing."""
        return self._is_processing
    
    def get_current_job(self) -> Optional[ExportJob]:
        """Get currently processing job."""
        return self._current_job
    
    def get_pending_count(self) -> int:
        """Get number of pending jobs."""
        return sum(1 for job in self._jobs if job.status == JobStatus.PENDING)
    
    def update_job_progress(self, job_id: str, progress: float):
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
        """
        job = self.get_job(job_id)
        if job:
            job.progress = progress
            if self._on_job_progress:
                self._on_job_progress(job)
    
    def mark_job_started(self, job_id: str):
        """Mark job as started/processing."""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.PROCESSING
            job.started_time = datetime.now().isoformat()
            if self._on_job_started:
                self._on_job_started(job)
            self.save_queue()
    
    def mark_job_completed(self, job_id: str):
        """Mark job as completed."""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.finished_time = datetime.now().isoformat()
            if self._on_job_completed:
                self._on_job_completed(job)
            self.save_queue()
    
    def mark_job_failed(self, job_id: str, error_message: str):
        """Mark job as failed."""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.finished_time = datetime.now().isoformat()
            if self._on_job_failed:
                self._on_job_failed(job)
            self.save_queue()
    
    def save_queue(self):
        """Save queue to JSON file."""
        try:
            self._queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'jobs': [job.to_dict() for job in self._jobs],
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self._queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save queue: {e}")
    
    def load_queue(self):
        """Load queue from JSON file."""
        try:
            if not self._queue_file.exists():
                return
            
            with open(self._queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize and FILTER OUT corrupt jobs (from_dict returns None for corrupt)
            loaded_jobs = []
            for job_data in data.get('jobs', []):
                job = ExportJob.from_dict(job_data)
                if job is not None:  # Skip corrupt jobs
                    loaded_jobs.append(job)
            
            self._jobs = loaded_jobs
            
            # Reset any processing jobs to pending (in case app crashed)
            for job in self._jobs:
                try:
                    if job.status == JobStatus.PROCESSING:
                        job.status = JobStatus.PENDING
                except:
                    # If we can't access status, skip this job
                    pass
            
            # DON'T call _notify_queue_changed() here!
            # It will be called by QueuePanel after UI is ready
            
        except Exception as e:
            print(f"Failed to load queue: {e}")
            import traceback
            traceback.print_exc()
            self._jobs = []
            # Delete corrupt queue file
            if self._queue_file.exists():
                self._queue_file.unlink()
    
    # Callback setters
    def set_on_job_started(self, callback: Callable):
        """Set callback for when job starts."""
        self._on_job_started = callback
    
    def set_on_job_progress(self, callback: Callable):
        """Set callback for job progress updates."""
        self._on_job_progress = callback
    
    def set_on_job_completed(self, callback: Callable):
        """Set callback for when job completes."""
        self._on_job_completed = callback
    
    def set_on_job_failed(self, callback: Callable):
        """Set callback for when job fails."""
        self._on_job_failed = callback
    
    def set_on_queue_finished(self, callback: Callable):
        """Set callback for when entire queue finishes."""
        self._on_queue_finished = callback
    
    def set_on_queue_changed(self, callback: Callable):
        """Set callback for when queue changes (add/remove/reorder)."""
        self._on_queue_changed = callback
    
    def _notify_queue_changed(self):
        """Notify that queue has changed."""
        if self._on_queue_changed:
            self._on_queue_changed()
    
    # Processing control (to be implemented by queue processor)
    def start_processing(self):
        """Flag to start processing queue."""
        self._is_processing = True
    
    def stop_processing(self):
        """Flag to stop processing queue."""
        self._is_processing = False
    
    def set_current_job(self, job: Optional[ExportJob]):
        """Set current processing job."""
        self._current_job = job
        if job:
            job.status = JobStatus.PROCESSING
            job.started_time = datetime.now().isoformat()
            if self._on_job_started:
                self._on_job_started(job)
