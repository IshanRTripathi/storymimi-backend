# Public Stories Endpoint Implementation - FastAPI Backend

## 🎯 **OVERVIEW**

This document provides the complete implementation for the public stories endpoint that will serve freely available stories to all users, independent of user authentication.

---

## 📊 **DATABASE SCHEMA**

### **Public Stories Table**
```sql
-- Create public_stories table
CREATE TABLE public_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_url VARCHAR(500),
    tags JSON DEFAULT '[]',
    duration VARCHAR(50) DEFAULT '3 minutes',
    featured BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    age_rating VARCHAR(20) DEFAULT 'ALL',
    language VARCHAR(10) DEFAULT 'en',
    category VARCHAR(100) DEFAULT 'adventure',
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published BOOLEAN DEFAULT TRUE,
    scenes JSON NOT NULL -- Complete story content
);

-- Create indexes for performance
CREATE INDEX idx_public_stories_featured ON public_stories(featured) WHERE featured = TRUE;
CREATE INDEX idx_public_stories_category ON public_stories(category);
CREATE INDEX idx_public_stories_tags ON public_stories USING GIN(tags);
CREATE INDEX idx_public_stories_published ON public_stories(published) WHERE published = TRUE;
CREATE INDEX idx_public_stories_created_at ON public_stories(created_at DESC);
```

### **Sample Data Population**
```sql
-- Insert sample public stories
INSERT INTO public_stories (
    title, description, cover_image_url, tags, duration, featured, 
    category, age_rating, scenes
) VALUES 
(
    'The Magical Forest Adventure',
    'Join Luna as she discovers a enchanted forest filled with talking animals and magical creatures.',
    'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=600&fit=crop',
    '["fantasy", "adventure", "children", "magic", "animals"]',
    '4 minutes',
    TRUE,
    'fantasy',
    'ALL',
    '[
        {
            "sequence": 0,
            "text": "Once upon a time, a curious girl named Luna discovered a hidden path behind her grandmother''s cottage. The path shimmered with golden light and seemed to beckon her forward.",
            "image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/magical-forest-1.mp3"
        },
        {
            "sequence": 1,
            "text": "As Luna stepped into the magical forest, she met a wise old owl who wore tiny spectacles. ''Welcome, young adventurer,'' hooted the owl. ''I''ve been waiting for someone brave like you.''",
            "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/magical-forest-2.mp3"
        },
        {
            "sequence": 2,
            "text": "The owl led Luna to a clearing where all the forest animals had gathered. They needed her help to save their magical spring from losing its power. Luna knew this would be her greatest adventure yet.",
            "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/magical-forest-3.mp3"
        }
    ]'
),
(
    'Space Explorer Zara',
    'Follow Captain Zara on her mission to discover new planets and make friends with alien creatures.',
    'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=600&fit=crop',
    '["science-fiction", "space", "adventure", "friendship", "exploration"]',
    '5 minutes',
    TRUE,
    'science-fiction',
    'ALL',
    '[
        {
            "sequence": 0,
            "text": "Captain Zara checked her star map one more time before launching her sleek silver spaceship into the vast cosmos. Today, she would explore the mysterious Planet Zephyr.",
            "image_url": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/space-explorer-1.mp3"
        },
        {
            "sequence": 1,
            "text": "On Planet Zephyr, Zara discovered crystal caves that sang beautiful melodies. She also met the Zephyrians - friendly purple creatures with multiple eyes who communicated through musical tones.",
            "image_url": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/space-explorer-2.mp3"
        },
        {
            "sequence": 2,
            "text": "The Zephyrians taught Zara their musical language, and in return, she shared stories of Earth. Together, they created a beautiful symphony that echoed across the galaxy, celebrating their new friendship.",
            "image_url": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/space-explorer-3.mp3"
        }
    ]'
),
(
    'The Brave Little Mouse',
    'Pip the mouse proves that being small doesn''t mean you can''t do big things when he saves his village.',
    'https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=400&h=600&fit=crop',
    '["animals", "courage", "friendship", "village", "heroism"]',
    '3 minutes',
    FALSE,
    'adventure',
    'ALL',
    '[
        {
            "sequence": 0,
            "text": "In the cozy village of Whiskertown lived Pip, the smallest mouse anyone had ever seen. While other mice laughed at his size, Pip dreamed of doing something truly heroic.",
            "image_url": "https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/brave-mouse-1.mp3"
        },
        {
            "sequence": 1,
            "text": "When a fierce storm blocked the village''s food storage with fallen trees, only Pip was small enough to squeeze through the tiny gaps and reach the supplies.",
            "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/brave-mouse-2.mp3"
        },
        {
            "sequence": 2,
            "text": "Pip worked tirelessly, carrying food bit by bit to feed all the village mice. From that day forward, everyone knew that heroes come in all sizes, and Pip was the bravest of them all.",
            "image_url": "https://images.unsplash.com/photo-1548681528-6a5c45b66b42?w=800&h=600&fit=crop",
            "audio_url": "https://example.com/audio/brave-mouse-3.mp3"
        }
    ]'
);
```

---

## 🐍 **PYDANTIC MODELS**

### **Response Models**
```python
# app/models/public_story_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AgeRating(str, Enum):
    ALL = "ALL"
    AGES_3_PLUS = "3+"
    AGES_6_PLUS = "6+"
    AGES_9_PLUS = "9+"
    AGES_12_PLUS = "12+"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class StoryCategory(str, Enum):
    FANTASY = "fantasy"
    SCIENCE_FICTION = "science-fiction"
    ADVENTURE = "adventure"
    FRIENDSHIP = "friendship"
    ANIMALS = "animals"
    MYSTERY = "mystery"
    EDUCATIONAL = "educational"

class PublicStoryScene(BaseModel):
    sequence: int = Field(..., description="Scene order number")
    text: str = Field(..., description="Scene narrative text")
    image_url: Optional[str] = Field(None, description="Scene image URL")
    audio_url: Optional[str] = Field(None, description="Scene audio URL")

class PublicStorySummary(BaseModel):
    """Summary model for story lists and cards"""
    id: str = Field(..., description="Story unique identifier")
    title: str = Field(..., description="Story title")
    description: Optional[str] = Field(None, description="Short story description")
    cover_image_url: Optional[str] = Field(None, description="Story cover image URL")
    tags: List[str] = Field(default_factory=list, description="Story tags")
    duration: str = Field(..., description="Estimated reading/listening time")
    featured: bool = Field(False, description="Whether story is featured")
    view_count: int = Field(0, description="Number of views")
    age_rating: AgeRating = Field(AgeRating.ALL, description="Age appropriateness")
    category: StoryCategory = Field(..., description="Story category")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Reading difficulty")
    created_at: datetime = Field(..., description="Creation timestamp")

class PublicStoryDetail(PublicStorySummary):
    """Complete story model with scenes"""
    scenes: List[PublicStoryScene] = Field(..., description="Story scenes")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class CategorizedPublicStories(BaseModel):
    """Categorized stories for home screen"""
    featured: List[PublicStorySummary] = Field(default_factory=list)
    popular: List[PublicStorySummary] = Field(default_factory=list)
    latest: List[PublicStorySummary] = Field(default_factory=list)
    by_category: Dict[str, List[PublicStorySummary]] = Field(default_factory=dict)
    by_age_rating: Dict[str, List[PublicStorySummary]] = Field(default_factory=dict)
```

---

## 🔄 **DATABASE MODELS**

### **SQLAlchemy Model**
```python
# app/models/database_models.py

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class PublicStory(Base):
    __tablename__ = "public_stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    cover_image_url = Column(String(500))
    tags = Column(JSON, default=list)
    duration = Column(String(50), default="3 minutes")
    featured = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0)
    age_rating = Column(String(20), default="ALL")
    language = Column(String(10), default="en")
    category = Column(String(100), default="adventure", index=True)
    difficulty_level = Column(String(20), default="beginner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published = Column(Boolean, default=True, index=True)
    scenes = Column(JSON, nullable=False)  # Complete story content

    def to_summary_dict(self) -> dict:
        """Convert to PublicStorySummary format"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "tags": self.tags or [],
            "duration": self.duration,
            "featured": self.featured,
            "view_count": self.view_count,
            "age_rating": self.age_rating,
            "category": self.category,
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at,
        }

    def to_detail_dict(self) -> dict:
        """Convert to PublicStoryDetail format"""
        summary = self.to_summary_dict()
        summary.update({
            "scenes": self.scenes or [],
            "updated_at": self.updated_at,
        })
        return summary
```

---

## 🚀 **API ENDPOINTS**

### **Main Endpoints Implementation**
```python
# app/api/public_stories.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict
from app.database import get_db
from app.models.database_models import PublicStory
from app.models.public_story_models import (
    PublicStorySummary, 
    PublicStoryDetail, 
    CategorizedPublicStories,
    StoryCategory,
    AgeRating,
    DifficultyLevel
)

router = APIRouter(prefix="/stories", tags=["public-stories"])

@router.get("/public", response_model=List[PublicStorySummary])
async def get_public_stories(
    category: Optional[StoryCategory] = None,
    age_rating: Optional[AgeRating] = None,
    difficulty_level: Optional[DifficultyLevel] = None,
    featured_only: bool = False,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get public stories with optional filtering
    """
    query = db.query(PublicStory).filter(PublicStory.published == True)
    
    # Apply filters
    if category:
        query = query.filter(PublicStory.category == category.value)
    
    if age_rating:
        query = query.filter(PublicStory.age_rating == age_rating.value)
    
    if difficulty_level:
        query = query.filter(PublicStory.difficulty_level == difficulty_level.value)
    
    if featured_only:
        query = query.filter(PublicStory.featured == True)
    
    # Order by creation date (newest first)
    query = query.order_by(desc(PublicStory.created_at))
    
    # Apply pagination
    stories = query.offset(offset).limit(limit).all()
    
    return [PublicStorySummary(**story.to_summary_dict()) for story in stories]

@router.get("/public/categorized", response_model=CategorizedPublicStories)
async def get_categorized_public_stories(
    db: Session = Depends(get_db)
):
    """
    Get public stories organized by categories for home screen
    """
    # Get all published stories
    stories = db.query(PublicStory).filter(PublicStory.published == True).all()
    
    # Convert to summary format
    story_summaries = [PublicStorySummary(**story.to_summary_dict()) for story in stories]
    
    # Categorize stories
    featured = [s for s in story_summaries if s.featured][:3]
    popular = sorted(story_summaries, key=lambda x: x.view_count, reverse=True)[:10]
    latest = sorted(story_summaries, key=lambda x: x.created_at, reverse=True)[:10]
    
    # Group by category
    by_category = {}
    for story in story_summaries:
        if story.category not in by_category:
            by_category[story.category] = []
        by_category[story.category].append(story)
    
    # Group by age rating
    by_age_rating = {}
    for story in story_summaries:
        if story.age_rating not in by_age_rating:
            by_age_rating[story.age_rating] = []
        by_age_rating[story.age_rating].append(story)
    
    return CategorizedPublicStories(
        featured=featured,
        popular=popular,
        latest=latest,
        by_category=by_category,
        by_age_rating=by_age_rating
    )

@router.get("/public/{story_id}", response_model=PublicStoryDetail)
async def get_public_story_detail(
    story_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete public story with all scenes
    """
    story = db.query(PublicStory).filter(
        and_(
            PublicStory.id == story_id,
            PublicStory.published == True
        )
    ).first()
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Increment view count
    story.view_count += 1
    db.commit()
    
    return PublicStoryDetail(**story.to_detail_dict())

@router.get("/public/featured", response_model=List[PublicStorySummary])
async def get_featured_stories(
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db)
):
    """
    Get featured public stories for home screen
    """
    stories = db.query(PublicStory).filter(
        and_(
            PublicStory.published == True,
            PublicStory.featured == True
        )
    ).order_by(desc(PublicStory.created_at)).limit(limit).all()
    
    return [PublicStorySummary(**story.to_summary_dict()) for story in stories]

@router.get("/public/popular", response_model=List[PublicStorySummary])
async def get_popular_stories(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get popular public stories based on view count
    """
    stories = db.query(PublicStory).filter(
        PublicStory.published == True
    ).order_by(desc(PublicStory.view_count)).limit(limit).all()
    
    return [PublicStorySummary(**story.to_summary_dict()) for story in stories]
```

---

## 📝 **API USAGE EXAMPLES**

### **Get Categorized Stories for Home Screen**
```bash
curl -X GET "http://localhost:8080/stories/public/categorized"
```

**Response:**
```json
{
  "featured": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "The Magical Forest Adventure",
      "description": "Join Luna as she discovers a enchanted forest...",
      "cover_image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=600&fit=crop",
      "tags": ["fantasy", "adventure", "children", "magic", "animals"],
      "duration": "4 minutes",
      "featured": true,
      "view_count": 1250,
      "age_rating": "ALL",
      "category": "fantasy",
      "difficulty_level": "beginner",
      "created_at": "2023-12-07T10:30:00Z"
    }
  ],
  "popular": [...],
  "latest": [...],
  "by_category": {
    "fantasy": [...],
    "science-fiction": [...],
    "adventure": [...]
  },
  "by_age_rating": {
    "ALL": [...],
    "3+": [...],
    "6+": [...]
  }
}
```

### **Get All Public Stories with Filters**
```bash
curl -X GET "http://localhost:8080/stories/public?category=fantasy&limit=10"
```

### **Get Featured Stories**
```bash
curl -X GET "http://localhost:8080/stories/public/featured?limit=3"
```

### **Get Complete Story with Scenes**
```bash
curl -X GET "http://localhost:8080/stories/public/123e4567-e89b-12d3-a456-426614174000"
```

---

## 🎯 **FLUTTER INTEGRATION READY**

Your Flutter app can now use this endpoint! Update the `_getPublicStories()` method:

```dart
Future<List<StoryCardData>> _getPublicStories() async {
  try {
    final response = await _dio.get('/stories/public/categorized');
    final categorizedResponse = CategorizedPublicStories.fromJson(response.data);
    
    // Convert and combine all categories
    List<StoryCardData> allStories = [];
    allStories.addAll(categorizedResponse.featured.map(_toStoryCardData));
    allStories.addAll(categorizedResponse.popular.map(_toStoryCardData));
    allStories.addAll(categorizedResponse.latest.map(_toStoryCardData));
    
    return allStories;
  } catch (e) {
    _logger.e('Error loading public stories: $e');
    return [];
  }
}
```

---

## 🚀 **DEPLOYMENT CHECKLIST**

- [ ] Create `public_stories` table with provided SQL
- [ ] Insert sample data using the provided SQL
- [ ] Add the new API endpoints to your FastAPI app
- [ ] Test endpoints with curl/Postman
- [ ] Update Flutter app to use real endpoint
- [ ] Verify categorized stories display correctly

**Your app will immediately have rich, categorized public content! 🎉** 