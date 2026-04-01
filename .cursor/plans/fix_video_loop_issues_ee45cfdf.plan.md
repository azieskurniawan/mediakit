---
name: Fix Video Loop Issues
overview: "Fix video looping behavior across different scenarios (with/without transitions, with/without overlays). Current issues: videos not looping properly, only last video loops, or videos freeze after first cycle."
todos:
  - id: fix-concat-looping
    content: Fix traditional concat mode - videos not looping properly (only last video loops)
    status: completed
  - id: fix-concat-overlay-error
    content: Fix traditional concat mode - video_duration undefined error when overlays present
    status: completed
  - id: fix-xfade-stops
    content: Fix xfade mode - videos stop after first cycle instead of looping
    status: completed
  - id: fix-xfade-image-overlay
    content: Fix xfade mode - image overlay causes video to not play at all
    status: pending
  - id: add-debug-logging
    content: Add comprehensive debug logging to diagnose video looping issues
    status: pending
---

# Fix Video Looping in All Scenarios

## Problem Analysis

Based on user testing, there are 5 broken scenarios:

### Scenario 1: No transition, no overlay

- **Issue**: Only video 2 loops (1,2,2,2,2...)
- **Root cause**: `_create_concat_file()` not properly looping all videos
- **Location**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) line 401

### Scenario 2: With transition (xfade), no overlay

- **Issue**: Video stops after video 2, audio continues
- **Root cause**: Pre-repeat logic calculates wrong, or xfade chain stops early
- **Location**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) line 1273-1320

### Scenario 3: With transition, video overlay

- **Issue**: Video stops after video 2, overlay also stops
- **Root cause**: Same as scenario 2 + overlay uses `shortest=1` which stops when base video stops
- **Location**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) line 1600+

### Scenario 4: With transition, image overlay

- **Issue**: Video doesn't play at all, only audio plays, but image overlay shows
- **Root cause**: Possibly filter_complex error with image overlay in xfade mode
- **Location**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) line 1600+

### Scenario 5: No transition, video overlay

- **Issue**: Error at line 694 - `trim=duration=` has incomplete value
- **Root cause**: `video_duration` variable is undefined in traditional concat mode
- **Location**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) line 694

## Root Cause Summary

There are **2 separate video building modes** with different bugs:

### Mode 1: Traditional Concat (no transitions)

- Uses `-f concat` input with concat file
- Video looping handled by `_create_concat_file()`
- **Bug 1**: Concat file generation doesn't properly loop all videos
- **Bug 2**: `video_duration` not passed to `_build_filter_complex()`, causing error when overlays are present

### Mode 2: Xfade Transitions

- Uses individual video inputs with xfade filter chain
- Video looping handled by pre-repeating video list
- **Bug 3**: Pre-repeat calculation may be wrong
- **Bug 4**: Xfade chain may not be building correctly for many videos
- **Bug 5**: Image overlay breaks xfade mode entirely

## Solution Strategy

Fix each mode separately with proper variable passing:

### Fix 1: Traditional Concat Mode

1. Fix `_create_concat_file()` to properly loop all videos (not just last one)
2. Pass `target_duration` to `_build_filter_complex()` so overlay trim filter works

### Fix 2: Xfade Mode

1. Verify pre-repeat calculation is correct
2. Add debug logging to show xfade chain being built
3. Fix image overlay handling in xfade mode (currently breaks completely)
4. Ensure overlays work with long xfade chains

## Implementation Plan

### Task 1: Fix Traditional Concat - Video Looping

**File**: [`ffmpeg_exporter/core/media_manager.py`](ffmpeg_exporter/core/media_manager.py)

Inspect `_create_concat_file()` method:

- Current behavior: Likely only repeating last video
- Expected: Should repeat entire sequence (A,B,A,B,A,B...)

### Task 2: Fix Traditional Concat - Overlay Error

**File**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py)

Line 530: `_build_video_traditional_concat()` calls `_build_filter_complex()`:

```python
filter_complex = self._build_filter_complex(
    # Missing: target_duration parameter!
)
```

Line 694: `_build_filter_complex()` tries to use `video_duration`:

```python
filters.append(f"[{input_idx}:v]trim=duration={video_duration}:start=0,...")
# video_duration is undefined!
```

**Fix**: Pass `target_duration` as parameter to `_build_filter_complex()`.

### Task 3: Fix Xfade Mode - Video Stops After First Cycle

**File**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py)

Line 1295-1310: Pre-repeat logic:

```python
single_cycle_duration = sum(original_video_durations) - (transition_duration * (len(original_videos) - 1))
num_repeats = int(audio_duration / single_cycle_duration) + 2
```

**Investigate**:

- Is `single_cycle_duration` calculation correct?
- Is xfade chain being built for all repeated videos?
- Add logging to debug xfade chain construction

### Task 4: Fix Xfade Mode - Image Overlay Breaks Video

**File**: [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py)

Line 1600+: Overlay application in xfade mode.

**Issue**: When image overlay is present, video doesn't play at all.

**Investigate**:

- How are overlays applied in xfade mode?
- Is there a difference between video overlays and image overlays?
- May need to loop image overlay differently in xfade mode

### Task 5: Add Comprehensive Debug Logging

Add logging throughout to help diagnose:

```python
print(f"[MODE] Traditional Concat / Xfade Transition")
print(f"[VIDEOS] Count: {len(videos)}, Durations: {video_durations}")
print(f"[AUDIO] Duration: {audio_duration}s")
print(f"[TARGET] Duration: {target_duration}s")
print(f"[CONCAT FILE] Contents: ...")  # For traditional mode
print(f"[XFADE] Pre-repeat: {num_repeats}x, Total videos: {len(videos)}")  # For xfade mode
print(f"[OVERLAYS] Count: {len(overlays)}, Types: [video/image]")
```

## Files to Modify

1. [`ffmpeg_exporter/core/media_manager.py`](ffmpeg_exporter/core/media_manager.py) - Fix `_create_concat_file()`
2. [`ffmpeg_exporter/core/ffmpeg_builder.py`](ffmpeg_exporter/core/ffmpeg_builder.py) - Fix both modes:

   - `_build_video_traditional_concat()` - pass target_duration
   - `_build_filter_complex()` - accept target_duration param
   - `_build_video_with_transitions()` - fix pre-repeat and image overlay

## Testing Matrix

After fixes, test all 5 scenarios:

| Scenario | Transition | Overlay | Expected Result |

|----------|-----------|---------|-----------------|

| 1 | No | No | Videos loop: A,B,A,B,A,B... for full audio |

| 2 | Yes (fade) | No | Videos loop with transitions for full audio |

| 3 | Yes (fade) | Video | Base videos + overlay loop for full audio |

| 4 | Yes (fade) | Image | Base videos loop + image repeats for full audio |

| 5 | No | Video | Videos + overlay loop for full audio |

## Questions for User

Before implementing, I need to understand the concat file behavior:

1. **Concat file contents**: When you export with traditional mode (no transitions), what does the generated concat file look like? (Should be in temp folder like `tmpXXXX.txt`)

2. **Expected looping behavior**: For 2 videos (A=5s, B=5s) with 3min audio, do you want:

   - Option A: Repeat entire sequence (A,B,A,B,A,B... for 3min)
   - Option B: Something else?

3. **Xfade pre-repeat**: Current code repeats videos BEFORE xfade (A,B,A,B... → 44 inputs → chain xfade). Is this correct or should we use a different approach?