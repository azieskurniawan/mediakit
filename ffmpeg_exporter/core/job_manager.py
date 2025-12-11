"""
Job Manager - Manages multiple export and livestream jobs.
"""
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from PySide6.QtCore import QObject, Signal


class JobType(Enum):
    """Type of job."""
    EXPORT = "export"
    LIVESTREAM = "livestream"


class JobStatus(Enum):
    """Status of a job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Represents a processing job (export or livestream)."""
    id: str
    type: JobType
    name: str
    command: List[str]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    process: Optional[subprocess.Popen] = None
    temp_files: List[str] = field(default_factory=list)
    
    # For livestream jobs
    stream_duration_minutes: Optional[int] = None  # Auto-stop after N minutes
    
    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.started_at:
            end_time = self.finished_at or datetime.now()
            return (end_time - self.started_at).total_seconds()
        return None
    
    def get_status_display(self) -> str:
        """Get display-friendly status."""
        if self.status == JobStatus.RUNNING:
            duration = self.get_duration()
            if duration:
                mins, secs = divmod(int(duration), 60)
                return f"Running ({mins}m {secs}s)"
        return self.status.value.title()


class JobManager(QObject):
    """Manages multiple concurrent jobs."""
    
    # Signals
    job_added = Signal(str)  # job_id
    job_started = Signal(str)  # job_id
    job_progress = Signal(str, str)  # job_id, log_line
    job_completed = Signal(str)  # job_id
    job_failed = Signal(str, str)  # job_id, error_message
    job_cancelled = Signal(str)  # job_id
    
    def __init__(self):
        super().__init__()
        self._jobs: Dict[str, Job] = {}
        self._job_counter = 0
        self._lock = threading.Lock()
    
    def create_job(
        self,
        job_type: JobType,
        name: str,
        command: List[str],
        temp_files: Optional[List[str]] = None,
        stream_duration_minutes: Optional[int] = None
    ) -> str:
        """
        Create a new job.
        
        Args:
            job_type: Type of job (export or livestream).
            name: Human-readable job name.
            command: FFmpeg command to execute.
            temp_files: Temporary files to cleanup after job.
            stream_duration_minutes: For livestream, auto-stop duration.
            
        Returns:
            Job ID.
        """
        with self._lock:
            self._job_counter += 1
            job_id = f"{job_type.value}_{self._job_counter}"
            
            job = Job(
                id=job_id,
                type=job_type,
                name=name,
                command=command,
                temp_files=temp_files or [],
                stream_duration_minutes=stream_duration_minutes
            )
            
            self._jobs[job_id] = job
            self.job_added.emit(job_id)
            
            return job_id
    
    def start_job(self, job_id: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Start executing a job.
        
        Args:
            job_id: ID of job to start.
            log_callback: Optional callback for log lines.
            
        Returns:
            True if started successfully.
        """
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.PENDING:
            return False
        
        # Start job in background thread
        thread = threading.Thread(
            target=self._run_job,
            args=(job_id, log_callback),
            daemon=True
        )
        thread.start()
        
        return True
    
    def _run_job(self, job_id: str, log_callback: Optional[Callable[[str], None]] = None) -> None:
        """Run a job (called in background thread)."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        # Update status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self.job_started.emit(job_id)
        
        try:
            # Start process
            process = subprocess.Popen(
                job.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            job.process = process
            
            # For livestream with duration limit, set up auto-stop timer
            stop_timer = None
            if job.type == JobType.LIVESTREAM and job.stream_duration_minutes:
                stop_timer = threading.Timer(
                    job.stream_duration_minutes * 60,
                    lambda: self.cancel_job(job_id)
                )
                stop_timer.daemon = True
                stop_timer.start()
            
            # Read output line by line
            for line in process.stdout:
                if line:
                    self.job_progress.emit(job_id, line.rstrip())
                    if log_callback:
                        log_callback(line.rstrip())
            
            # Wait for completion
            return_code = process.wait()
            
            # Cancel auto-stop timer if it exists
            if stop_timer:
                stop_timer.cancel()
            
            # Update status based on return code
            if return_code == 0:
                job.status = JobStatus.COMPLETED
                job.finished_at = datetime.now()
                self.job_completed.emit(job_id)
            else:
                job.status = JobStatus.FAILED
                job.finished_at = datetime.now()
                job.error_message = f"Process exited with code {return_code}"
                self.job_failed.emit(job_id, job.error_message)
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.finished_at = datetime.now()
            job.error_message = str(e)
            self.job_failed.emit(job_id, job.error_message)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: ID of job to cancel.
            
        Returns:
            True if cancelled successfully.
        """
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.RUNNING:
            return False
        
        # Terminate process
        if job.process:
            try:
                job.process.terminate()
                job.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                job.process.kill()
            except Exception:
                pass
        
        # Update status
        job.status = JobStatus.CANCELLED
        job.finished_at = datetime.now()
        self.job_cancelled.emit(job_id)
        
        return True
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs."""
        return list(self._jobs.values())
    
    def get_active_jobs(self) -> List[Job]:
        """Get jobs that are currently running."""
        return [job for job in self._jobs.values() if job.status == JobStatus.RUNNING]
    
    def cleanup_job(self, job_id: str) -> None:
        """
        Cleanup temporary files for a job.
        
        Args:
            job_id: ID of job to cleanup.
        """
        job = self._jobs.get(job_id)
        if not job:
            return
        
        import os
        for temp_file in job.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass
        
        job.temp_files = []
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from history.
        
        Args:
            job_id: ID of job to remove.
            
        Returns:
            True if removed successfully.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        # Can only remove completed/failed/cancelled jobs
        if job.status == JobStatus.RUNNING:
            return False
        
        # Cleanup temp files
        self.cleanup_job(job_id)
        
        # Remove from dictionary
        del self._jobs[job_id]
        
        return True

