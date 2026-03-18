"""Memory tracking utilities for AITabletop agents.

Security Note:
    This module provides memory usage tracking. If memory tracking is unavailable,
    warnings are logged to alert users that memory limit enforcement may be bypassed.
"""

from __future__ import annotations

import logging
import warnings

# Cross-platform memory tracking
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

# Try to import psutil as fallback for Windows
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)

# Track if we've already warned about missing memory tracking
_memory_tracking_warning_shown = False


class MemoryTracker:
    """Track memory usage of the current process.

    Security Note:
        Memory tracking is used to enforce memory limits during agent execution.
        If memory tracking is unavailable, agents may exceed memory limits
        without detection. Warnings are issued when tracking is unavailable.
    """

    def __init__(self) -> None:
        """Initialize the memory tracker.

        Raises a warning if no memory tracking backend is available.
        """
        self.peak_memory_bytes = 0
        self._warning_issued = False

        # Check if any memory tracking backend is available
        if not HAS_RESOURCE and not HAS_PSUTIL:
            self._issue_tracking_warning()

    def _issue_tracking_warning(self) -> None:
        """Issue a warning about missing memory tracking backends."""
        global _memory_tracking_warning_shown

        if not _memory_tracking_warning_shown:
            _memory_tracking_warning_shown = True
            warning_msg = (
                "SECURITY WARNING: No memory tracking backend available. "
                "Install 'psutil' (pip install psutil) or ensure 'resource' module "
                "is available for proper memory limit enforcement. "
                "Without memory tracking, agents may exceed memory limits undetected."
            )
            logger.warning(warning_msg)
            warnings.warn(warning_msg, UserWarning, stacklevel=2)

    def get_memory_bytes(self) -> int:
        """Get current process memory usage estimate in bytes.

        Uses platform-specific methods to estimate memory usage.
        Updates ``peak_memory_bytes`` if current usage exceeds the tracked peak.

        Returns:
            Current memory usage in bytes, or 0 if tracking is unavailable.

        Note:
            If this returns 0 and no memory tracking backend is available,
            a warning is issued on first call.
        """
        current_bytes = self._get_process_memory()

        # Issue warning if we're getting 0 from tracking
        if current_bytes == 0 and not self._warning_issued:
            self._warning_issued = True
            if not HAS_RESOURCE and not HAS_PSUTIL:
                logger.warning(
                    "Memory tracking returned 0 - no backend available. "
                    "Memory limit enforcement may be bypassed."
                )

        if current_bytes > self.peak_memory_bytes:
            self.peak_memory_bytes = current_bytes

        return current_bytes

    def _get_process_memory(self) -> int:
        """Get memory usage using available platform-specific method.

        Returns:
            Memory usage in bytes, or 0 if no backend is available.
        """
        if HAS_RESOURCE:
            # Unix/Linux/macOS
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # Linux reports ru_maxrss in kilobytes, macOS in bytes.
                # Heuristic: if value > 10M, assume bytes (macOS)
                if usage.ru_maxrss > 10_000_000:
                    return int(usage.ru_maxrss)
                else:
                    return int(usage.ru_maxrss * 1024)
            except Exception as e:
                logger.warning(f"Error getting resource usage: {e}")
                return 0
        elif HAS_PSUTIL:
            # Windows with psutil
            try:
                process = psutil.Process()
                return process.memory_info().rss
            except Exception as e:
                logger.warning(f"Error getting psutil memory info: {e}")
                return 0
        else:
            # No memory tracking available
            return 0

    def get_peak_memory_bytes(self) -> int:
        """Get peak memory usage since tracker creation.

        Returns:
            Peak memory usage in bytes.
        """
        return self.peak_memory_bytes

    def reset_peak(self) -> None:
        """Reset peak memory tracking."""
        self.peak_memory_bytes = 0

    def is_tracking_available(self) -> bool:
        """Check if memory tracking is available.

        Returns:
            True if at least one memory tracking backend is available.
        """
        return HAS_RESOURCE or HAS_PSUTIL