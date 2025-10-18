# Media Handling with External URLs

## Overview
The system now supports both uploaded media files and external URLs (e.g., from CDNs, Unsplash, etc.).

## PostMedia Model Features

### Fields
- **`file`**: Uploaded media file (optional)
- **`external_url`**: External URL for media hosted elsewhere (optional)
- **`media_type`**: Type of media (image, video, audio, file)
- **`thumbnail`**: Thumbnail image (auto-generated for videos)
- **`description`**: Optional caption/alt text
- **`order`**: Display order for multiple attachments

### Validation Rules
- Must have **either** `file` OR `external_url` (not both, not neither)
- For videos: auto-generates thumbnail at 1 second if file is uploaded

### Properties
- **`media_url`**: Returns the appropriate URL (external_url if set, otherwise file.url)

## Video Thumbnail Generation

### Requirements
- FFmpeg installed (now included in Docker image)
- Pillow (PIL) for image processing

### Automatic Generation
When a video file is uploaded:
1. Signal triggers `generate_video_thumbnail()` method
2. Extracts frame at 1 second using ffmpeg
3. Resizes to 400x300 (maintains aspect ratio)
4. Saves as JPEG thumbnail

### Manual Generation
```python
post_media = PostMedia.objects.get(id=some_id)
success = post_media.generate_video_thumbnail(at_second=5)  # Extract at 5 seconds
```

## API Usage

### Creating PostMedia with External URL
```python
PostMedia.objects.create(
    post=post,
    media_type='image',
    external_url='https://images.unsplash.com/photo-123...',
    description='Sunset over the lake',
    order=0
)
```

### Creating PostMedia with Uploaded File
```python
PostMedia.objects.create(
    post=post,
    media_type='video',
    file=uploaded_file,
    description='Product demo video',
    order=0
)
# Thumbnail auto-generated via signal
```

### Serializer Response
```json
{
    "id": "uuid",
    "media_type": "image",
    "file": null,
    "external_url": "https://images.unsplash.com/...",
    "thumbnail": null,
    "description": "Sunset over the lake",
    "order": 0,
    "media_url": "https://images.unsplash.com/..."
}
```

## Import Script Usage

The Sherbrooke posts import script now creates PostMedia objects with external URLs:

```bash
docker compose exec backend python scripts/import_sherbrooke_posts.py
```

This will:
- Create posts with proper community links
- Add PostMedia objects using Unsplash URLs
- Set descriptions and order for attachments

## Future Enhancements

### CDN Integration
Consider using a CDN for uploaded media:
1. Upload to CDN on file save
2. Store CDN URL in `external_url`
3. Delete local file to save space

### Thumbnail Customization
- Allow custom thumbnail upload for videos
- Support different thumbnail sizes
- Extract multiple frames for preview

### External URL Validation
- Add URL health checks
- Cache external media locally
- Handle broken links gracefully
