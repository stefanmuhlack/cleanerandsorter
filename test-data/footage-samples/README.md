# Footage and Media Test Data

This directory contains sample media files for testing the Footage Management Service.

## Directory Structure

```
footage-samples/
├── client1/
│   ├── branding/
│   │   ├── raw/
│   │   │   ├── logo_original.png
│   │   │   └── banner_original.jpg
│   │   ├── processed/
│   │   │   ├── logo_final.png
│   │   │   └── banner_final.jpg
│   │   └── designs/
│   │       ├── logo_design.psd
│   │       └── brand_guidelines.pdf
│   └── marketing/
│       ├── videos/
│       │   ├── product_demo.mp4
│       │   └── company_intro.mp4
│       └── images/
│           ├── product_photos/
│           └── social_media/
├── client2/
│   ├── web-design/
│   │   ├── mockups/
│   │   ├── wireframes/
│   │   └── assets/
│   └── print-materials/
│       ├── brochures/
│       ├── flyers/
│       └── business_cards/
└── client3/
    ├── video-production/
    │   ├── raw_footage/
    │   ├── edited/
    │   └── final_delivery/
    └── photography/
        ├── portraits/
        ├── events/
        └── products/
```

## File Types

### Images
- **Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP, SVG
- **Sizes**: 1KB - 10MB
- **Use Cases**: Logos, banners, product photos, social media content

### Videos
- **Formats**: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V
- **Sizes**: 1MB - 100MB
- **Use Cases**: Product demos, company introductions, tutorials

### Design Files
- **Formats**: PSD, AI, EPS, SVG, PDF, INDD, Sketch, Fig
- **Sizes**: 1MB - 10MB
- **Use Cases**: Logo designs, brand guidelines, mockups

### Documents
- **Formats**: DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, RTF
- **Sizes**: 1KB - 1MB
- **Use Cases**: Project briefs, specifications, reports

## Metadata Examples

### Image Metadata
```json
{
  "width": 1920,
  "height": 1080,
  "format": "PNG",
  "color_space": "sRGB",
  "dpi": 300,
  "exif": {
    "DateTime": "2024:01:15 10:30:00",
    "Make": "Canon",
    "Model": "EOS R5",
    "ISO": 100,
    "FNumber": "f/2.8",
    "ExposureTime": "1/125"
  }
}
```

### Video Metadata
```json
{
  "width": 1920,
  "height": 1080,
  "duration": 120.5,
  "fps": 30,
  "codec": "H.264",
  "bitrate": 5000000,
  "audio": true,
  "audio_codec": "AAC",
  "audio_channels": 2
}
```

### Design Metadata
```json
{
  "layers": 15,
  "resolution": 300,
  "color_mode": "RGB",
  "file_size": 52428800,
  "created_date": "2024-01-15T10:00:00Z",
  "modified_date": "2024-01-15T15:30:00Z"
}
```

## Testing Scenarios

### 1. File Upload
- Upload different file types and sizes
- Test thumbnail generation
- Verify metadata extraction
- Check automatic classification

### 2. Search and Filter
- Search by customer, project, category
- Filter by file type, date range, size
- Test tag-based search
- Verify search results accuracy

### 3. Organization
- Test automatic folder structure creation
- Verify file categorization
- Check tag assignment
- Test duplicate detection

### 4. Performance
- Upload large files (100MB+)
- Test concurrent uploads
- Verify thumbnail generation speed
- Check search performance with many files

## Sample Files to Create

### Images
- `client1/branding/raw/logo_original.png` (2MB, 1920x1080)
- `client1/branding/processed/logo_final.png` (1MB, 800x600)
- `client2/web-design/assets/hero_image.jpg` (3MB, 1920x1080)
- `client3/photography/portraits/team_photo.jpg` (5MB, 4000x3000)

### Videos
- `client1/marketing/videos/product_demo.mp4` (50MB, 1920x1080, 60s)
- `client2/web-design/videos/website_preview.mp4` (25MB, 1280x720, 30s)
- `client3/video-production/raw_footage/interview_raw.mp4` (100MB, 1920x1080, 120s)

### Design Files
- `client1/branding/designs/logo_design.psd` (15MB, multi-layer)
- `client2/web-design/mockups/homepage_mockup.psd` (25MB, complex design)
- `client3/print-materials/brochures/company_brochure.indd` (8MB, print-ready)

### Documents
- `client1/branding/documents/brand_guidelines.pdf` (2MB, comprehensive guide)
- `client2/web-design/documents/project_brief.docx` (500KB, project specifications)
- `client3/video-production/documents/script_final.docx` (1MB, video script)

## Usage Instructions

1. **Upload Test Files**: Use the Footage Management interface to upload sample files
2. **Verify Processing**: Check that thumbnails are generated and metadata is extracted
3. **Test Search**: Use various search criteria to find uploaded files
4. **Check Organization**: Verify files are organized correctly by customer/project
5. **Test Classification**: Confirm automatic categorization and tagging works
6. **Performance Test**: Upload multiple files simultaneously to test performance

## Notes

- All sample files should be properly licensed for testing
- File sizes should be realistic for production use
- Metadata should be comprehensive and accurate
- Folder structure should follow the defined organization rules
- Test files should cover all supported file types and formats 