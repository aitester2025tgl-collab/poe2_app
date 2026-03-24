# PERFORMANCE_IMPROVEMENTS.md

## Performance Optimization Recommendations

### 1. **Caching Layer**

#### Current Issue:
- Every bot/web request reads from JSON files
- LLM calls are slow and not cached
- Repeated parsing of same data

#### Solution: Implement Redis/In-Memory Cache

```python
# utils/cache.py
from functools import lru_cache
import json
from typing import Dict, Any

class BuildCache:
    def __init__(self):
        self._cache = {}
        self._timestamp = None
    
    @lru_cache(maxsize=128)
    def get_builds_for_class(self, class_name: str) -> list:
        """Cached build retrieval"""
        return self._load_builds().get(class_name, [])
    
    def _load_builds(self) -> Dict[str, Any]:
        """Load builds with timestamp check"""
        # Implement file modification check
        # Only reload if file changed
        pass
```

**Impact**: 90% reduction in I/O operations

---

### 2. **Database Migration**

#### Current Issue:
- JSON files don't scale well
- No indexing or querying capabilities
- Concurrent access issues

#### Solution: SQLite/PostgreSQL

```python
# models.py
from sqlalchemy import Column, Integer, String, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Build(Base):
    __tablename__ = 'builds'
    
    id = Column(Integer, primary_key=True)
    build_name = Column(String(255), index=True)
    class_name = Column(String(50), index=True)
    version = Column(String(20))
    reputation = Column(Integer, index=True)
    confidence = Column(Float, index=True)
    recommendation_score = Column(Float, index=True)
    skill_tree_data = Column(JSON)
    url = Column(String(500), unique=True)
```

**Benefits**:
- Fast queries with indexes
- Atomic transactions
- Concurrent access
- Easy filtering and sorting

---

### 3. **Async Processing**

#### Current Issue:
- Synchronous LLM calls block execution
- Batch processing is sequential
- Web scraping waits for each page

#### Solution: Use asyncio

```python
import asyncio
import aiohttp

async def fetch_multiple_builds(urls: list):
    """Fetch builds concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_build_async(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Result: 5-10x faster batch processing
```

---

### 4. **LLM Response Caching**

#### Current Issue:
- Same article processed multiple times
- LLM calls are expensive (time-wise)

#### Solution: Cache LLM Responses

```python
import hashlib

def get_cached_llm_response(article_text: str):
    """Cache LLM extractions by content hash"""
    content_hash = hashlib.sha256(article_text.encode()).hexdigest()
    
    cache_file = f"cache/llm_{content_hash}.json"
    if os.path.exists(cache_file):
        return json.load(open(cache_file))
    
    # Call LLM only if not cached
    response = extract_with_llm(article_text)
    json.dump(response, open(cache_file, 'w'))
    return response
```

**Impact**: Avoid 80%+ of redundant LLM calls

---

### 5. **Lazy Loading**

#### Current Issue:
- All builds loaded into memory at once
- Telegram bot loads entire dataset

#### Solution: Pagination & Lazy Loading

```python
def get_builds_paginated(class_name: str, page: int = 0, size: int = 5):
    """Load only requested page"""
    with open('poe2_builds.json') as f:
        f.seek(0)  # Stream parse
        # Use ijson for streaming
        builds = ijson.items(f, f'{class_name}.item')
        # Return only current page
        return list(itertools.islice(builds, page*size, (page+1)*size))
```

---

### 6. **Indexing & Search Optimization**

#### Current Implementation:
```python
# O(n) linear search through all builds
for build in builds:
    if is_build_valid(build):
        valid_builds.append(build)
```

#### Optimized Version:
```python
# Pre-compute validation results
BUILD_INDEX = {
    'Warrior': {
        'valid': [...],
        'by_score': sorted_builds,
        'by_reputation': sorted_builds
    }
}

# O(1) lookup
def get_valid_builds(class_name):
    return BUILD_INDEX[class_name]['valid']
```

---

### 7. **Reduce JSON File Size**

#### Current Issue:
- Repeated field names in every entry
- Uncompressed storage

#### Solution:
```python
# Compress JSON files
import gzip

def save_compressed(data, filename):
    with gzip.open(f'{filename}.gz', 'wt', encoding='utf-8') as f:
        json.dump(data, f)

def load_compressed(filename):
    with gzip.open(f'{filename}.gz', 'rt', encoding='utf-8') as f:
        return json.load(f)

# Typical compression: 70-80% size reduction
```

---

### 8. **API Rate Limiting**

#### Current Issue:
- No rate limiting on external APIs
- Can hit quotas quickly

#### Solution:
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls per minute
def call_google_api(query):
    # Your API call here
    pass
```

---

### 9. **Parallel Validation**

#### Current Issue:
```python
# Sequential validation
for build in builds:
    validate(build)
```

#### Optimized:
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    results = executor.map(validate_build, builds)

# 4x faster on 4-core CPU
```

---

### 10. **Monitoring & Profiling**

Add performance monitoring:

```python
import time
from functools import wraps

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@timeit
def fetch_builds():
    # Your code here
```

---

## Priority Implementation Order

1. **High Priority** (Immediate gains):
   - LLM response caching (#4)
   - JSON caching (#1)
   - Lazy loading (#5)

2. **Medium Priority** (Moderate effort):
   - Async processing (#3)
   - JSON compression (#7)
   - Indexing (#6)

3. **Low Priority** (Long-term):
   - Database migration (#2)
   - Monitoring (#10)

---

## Expected Performance Gains

| Optimization | Speed Improvement | Complexity |
|--------------|-------------------|------------|
| LLM Caching  | 10-50x           | Low        |
| Async I/O    | 5-10x            | Medium     |
| Database     | 2-5x             | High       |
| Indexing     | 3-10x            | Low        |
| Compression  | N/A (size)       | Low        |

---

## Memory Usage Optimization

```python
# Use generators instead of lists
def iter_builds():
    """Yield builds one at a time"""
    with open('poe2_builds.json') as f:
        data = json.load(f)
        for class_name, builds in data.items():
            for build in builds:
                yield build

# Instead of:
# all_builds = list(...)  # Loads everything

# Use:
# for build in iter_builds():  # Processes one at a time
```
