"""
Pipeline Status Models

Tracks document processing pipeline stages for debugging and monitoring.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Document processing pipeline stages."""

    UPLOADED = "uploaded"  # File received and saved to disk
    PARSING = "parsing"  # Extracting content from file
    PARSED = "parsed"  # Content successfully extracted
    INDEXING = "indexing"  # Creating vector embeddings
    INDEXED = "indexed"  # Embeddings stored in Chroma
    EXTRACTING_METADATA = "extracting_metadata"  # LLM metadata extraction
    METADATA_EXTRACTED = "metadata_extracted"  # Metadata extraction complete
    UPDATING_WIKI = "updating_wiki"  # Generating categories/relationships
    WIKI_UPDATED = "wiki_updated"  # Wiki generation complete
    COMPLETE = "complete"  # All processing finished
    FAILED = "failed"  # Processing failed at some stage


class PipelineStatus(str, Enum):
    """Status of current pipeline stage."""

    PENDING = "pending"  # Stage not started
    IN_PROGRESS = "in_progress"  # Stage currently executing
    SUCCESS = "success"  # Stage completed successfully
    FAILED = "failed"  # Stage failed with error
    SKIPPED = "skipped"  # Stage skipped (e.g., metadata extraction disabled)


class PipelineStageInfo(BaseModel):
    """Information about a single pipeline stage."""

    stage: PipelineStage = Field(..., description="Pipeline stage name")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="Current status")
    started_at: datetime | None = Field(None, description="When stage started")
    completed_at: datetime | None = Field(None, description="When stage completed")
    duration_seconds: float | None = Field(None, description="Time taken in seconds")
    error_message: str | None = Field(None, description="Error message if failed")
    details: dict | None = Field(default_factory=dict, description="Stage-specific details")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DocumentPipeline(BaseModel):
    """Complete pipeline status for a document."""

    doc_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    current_stage: PipelineStage = Field(default=PipelineStage.UPLOADED, description="Current pipeline stage")
    overall_status: PipelineStatus = Field(default=PipelineStatus.IN_PROGRESS, description="Overall pipeline status")

    # Stage tracking
    stages: list[PipelineStageInfo] = Field(default_factory=list, description="All pipeline stages")

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Pipeline start time")
    completed_at: datetime | None = Field(None, description="Pipeline completion time")
    total_duration_seconds: float | None = Field(None, description="Total time taken")

    # Configuration
    auto_index: bool = Field(default=True, description="Auto-indexing enabled")
    extract_metadata: bool = Field(default=True, description="Metadata extraction enabled")
    update_wiki: bool = Field(default=False, description="Wiki update enabled")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def get_stage_info(self, stage: PipelineStage) -> PipelineStageInfo | None:
        """Get information for a specific stage."""
        for stage_info in self.stages:
            if stage_info.stage == stage:
                return stage_info
        return None

    def update_stage(
        self,
        stage: PipelineStage,
        status: PipelineStatus,
        error_message: str | None = None,
        details: dict | None = None
    ):
        """Update or create a pipeline stage."""
        stage_info = self.get_stage_info(stage)

        if stage_info is None:
            # Create new stage
            stage_info = PipelineStageInfo(
                stage=stage,
                status=status,
                started_at=datetime.utcnow() if status == PipelineStatus.IN_PROGRESS else None,
                error_message=error_message,
                details=details or {}
            )
            self.stages.append(stage_info)
        else:
            # Update existing stage
            stage_info.status = status
            if status == PipelineStatus.IN_PROGRESS and stage_info.started_at is None:
                stage_info.started_at = datetime.utcnow()
            elif status in [PipelineStatus.SUCCESS, PipelineStatus.FAILED, PipelineStatus.SKIPPED]:
                stage_info.completed_at = datetime.utcnow()
                if stage_info.started_at:
                    stage_info.duration_seconds = (stage_info.completed_at - stage_info.started_at).total_seconds()
            stage_info.error_message = error_message
            if details:
                stage_info.details.update(details)

        # Update current stage
        if status == PipelineStatus.IN_PROGRESS:
            self.current_stage = stage

        # Update overall status
        if status == PipelineStatus.FAILED:
            self.overall_status = PipelineStatus.FAILED
            if self.completed_at is None:
                self.completed_at = datetime.utcnow()
                if self.started_at:
                    self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def mark_complete(self):
        """Mark pipeline as complete."""
        self.current_stage = PipelineStage.COMPLETE
        self.overall_status = PipelineStatus.SUCCESS
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage (0-100)."""
        total_stages = len(self.stages)
        if total_stages == 0:
            return 0.0

        completed_stages = sum(
            1 for s in self.stages
            if s.status in [PipelineStatus.SUCCESS, PipelineStatus.SKIPPED]
        )

        return (completed_stages / total_stages) * 100.0

    def to_summary(self) -> dict:
        """Generate a summary for display."""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "current_stage": self.current_stage.value,
            "overall_status": self.overall_status.value,
            "progress_percentage": self.get_progress_percentage(),
            "total_duration_seconds": self.total_duration_seconds,
            "stages_summary": [
                {
                    "stage": s.stage.value,
                    "status": s.status.value,
                    "duration": s.duration_seconds,
                    "error": s.error_message
                }
                for s in self.stages
            ]
        }
