# System Architecture

## Diagram

```text
Student (Browser)
       │
       ▼
Vanilla HTML / CSS / JS (index.html, script.js, style.css)
       │ (REST APIs)
       ▼
Flask Backend (app.py)
       │
 ┌─────┼────────────────┬─────────────────┐
 │     │                │                 │
 ▼     ▼                ▼                 ▼
SQLAlchemy (ORM)   Gemini API       JobSpy (Web Scraper)    Photon API
(SQLite / Postgres) (gemini-3.6-flash) (LinkedIn, Indeed)     (Geocoding)
```

## Layers
1. **Frontend**: Pure Vanilla HTML/CSS/JS. No heavy frameworks. Uses MapLibre GL JS for rendering the map tiles from OpenFreeMap.
2. **Backend**: Python Flask. Acts as the orchestrator.
3. **Database**: SQLAlchemy ORM handling local SQLite databases for lightweight persistence, and PostgreSQL for production environments like Render.
4. **External APIs**:
   - **Gemini**: Core AI engine.
   - **Photon**: Open-source geocoding API to convert city names to Lat/Lon.
   - **JobSpy**: Scrapes job boards.
