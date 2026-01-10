# Quick Start Guide for TALANTA AI Backend

## ⚡ Quick Setup (5 Minutes)

### Option 1: Using Docker (Recommended)

```powershell
# 1. Navigate to project directory
cd "C:\Users\ELITEBOOK 810\Desktop\TALANTA"

# 2. Copy environment file
Copy-Item backend\.env.example backend\.env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 5. Run database migrations
docker-compose exec app alembic upgrade head

# 6. Initialize Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p talanta_graph_pass_2024 -f /var/lib/neo4j/import/init.cypher

# 7. Seed sample data
docker-compose exec app python scripts/seed_data.py

# 8. Test the API
# Open http://localhost:8000/docs in your browser
```

### Option 2: Local Development (Without Docker)

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15
- Neo4j 5
- Redis 7
- (Optional) Ollama with Llama 3

```powershell
# 1. Install Python dependencies
cd backend
pip install -r requirements.txt

# 2. Set up .env file
Copy-Item .env.example .env
# Edit .env with your local database URLs

# 3. Run migrations
alembic upgrade head

# 4. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. In separate terminals, start:
# - Celery worker: celery -A app.tasks.celery_app worker --loglevel=info
# - Celery beat: celery -A app.tasks.celery_app beat --loglevel=info
```

---

## 🧪 Testing the System

### 1. Test Authentication

Open http://localhost:8000/docs

**Step 1: Login**
```
POST /auth/login
Body:
{
  "phone_number": "+254712345678"
}
```
**Result:** Check terminal logs for OTP (e.g., "🔐 OTP for +254712345678: 123456")

**Step 2: Verify OTP**
```
POST /auth/verify
Body:
{
  "phone_number": "+254712345678",
  "otp": "123456",
  "session_id": "<session_id_from_login>"
}
```
**Result:** Copy the `access_token`

**Step 3: Authorize**
Click the "Authorize" button (🔒 icon) and paste: `Bearer <your_access_token>`

### 2. Test Conversational Profiling

```
POST /chat/message
Body:
{
  "text": "I am a certified electrician from Nairobi with 7 years experience"
}
```

**Expected:**
- Intent: PROFILE_UPDATE
- Entities extracted: skills, location, experience
- Neo4j graph updated automatically

### 3. Test Market Intelligence

```
GET /market/gap-analysis
```

**Expected:** List of missing skills based on job market

```
GET /market/training-centers?skill=Solar&lat=-1.286&long=36.817&radius_km=50
```

**Expected:** Nearby training centers sorted by distance

### 4. Test Document Verification

```
POST /verify/upload
Form Data:
- file: (select an image file)
- document_type: CERTIFICATE
- skill_name: Electrical Wiring
```

**Expected:** 
- Verification ID returned
- Celery task queued for OCR processing

```
GET /verify/status/{verification_id}
```

**Expected:** Status updates (PENDING → PROCESSING → VERIFIED)

### 5. Test Admin Dashboard

**Login as admin first:**
```
POST /auth/login
Body: {"phone_number": "+254700000000"}

POST /auth/verify
Body: {"phone_number": "+254700000000", "otp": "<otp_from_logs>", "session_id": "..."}
```

Then access:
```
GET /admin/metrics/overview
GET /admin/metrics/skill-distribution
GET /admin/metrics/verification-queue
```

---

## 🔍 Verification Steps

### Check Services are Running

```powershell
# Check all containers
docker-compose ps

# Should show 7 services running:
# - postgres (healthy)
# - neo4j (healthy)
# - redis (healthy)
# - minio (healthy)
# - app (healthy)
# - celery_worker (running)
# - celery_beat (running)
```

### Check Logs

```powershell
# API logs
docker-compose logs -f app

# Celery worker logs
docker-compose logs -f celery_worker

# PostgreSQL logs
docker-compose logs postgres

# Neo4j logs
docker-compose logs neo4j
```

### Access Management UIs

- **FastAPI Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: talanta_graph_pass_2024)
- **MinIO Console**: http://localhost:9001 (user: talanta_minio_admin, pass: talanta_minio_secure_pass_2024)

---

## 🐛 Troubleshooting

### Issue: Docker containers won't start

```powershell
# Clean up and restart
docker-compose down -v
docker-compose up -d --build
```

### Issue: "Connection refused" errors

```powershell
# Check if services are healthy
docker-compose ps

# Wait for health checks (may take 30-60 seconds)
# If still failing, check specific service logs
docker-compose logs <service_name>
```

### Issue: Ollama not found (LLM errors)

**Option 1:** Install Ollama
```powershell
# Download from https://ollama.ai
# After install:
ollama pull llama3:instruct
```

**Option 2:** Use OpenAI instead
Edit `backend\.env`:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key
```

**Option 3:** Use fallback mode (keyword-based)
The system will automatically fall back to keyword matching if LLM is unavailable.

### Issue: Neo4j initialization failed

```powershell
# Manually initialize
docker-compose exec neo4j cypher-shell -u neo4j -p talanta_graph_pass_2024

# Then run:
:source /var/lib/neo4j/import/init.cypher
```

### Issue: OCR not working

The system uses PaddleOCR which downloads models on first run. If it fails:
```powershell
# Check Celery worker logs
docker-compose logs celery_worker

# OCR will use mock mode if PaddleOCR unavailable
```

---

## 📊 Sample Test Data

After running `seed_data.py`, you have:

**Users:**
- Admin: +254700000000 (role: ADMIN)

**Training Centers:**
- Nairobi Technical Training Institute
- Mombasa Youth Polytechnic
- Kisumu National Polytechnic

**Jobs:**
- 5 sample jobs (Plumber, Electrician, Solar Installer, etc.)

**Skills in Neo4j:**
- 10+ skills with categories
- Prerequisite relationships

---

## 🚀 Next Steps

1. **Customize Configuration**
   - Edit `backend\.env` for your environment
   - Update database passwords
   - Configure LLM provider

2. **Add Real Data**
   - Connect to KNQA API
   - Integrate job scraping
   - Add actual training centers

3. **Security Hardening**
   - Change all default passwords
   - Enable TLS/SSL
   - Configure firewall rules

4. **Deploy to Production**
   - Use docker-compose.prod.yml
   - Set up reverse proxy (Nginx)
   - Configure monitoring (Prometheus/Grafana)

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs <service>`
2. Review README.md for detailed documentation
3. Check walkthrough.md for implementation details

---

**System Status After Setup:**
✅ API Server: http://localhost:8000  
✅ API Docs: http://localhost:8000/docs  
✅ Neo4j Browser: http://localhost:7474  
✅ MinIO Console: http://localhost:9001  

**You're ready to build Kenya's sovereign workforce infrastructure! 🇰🇪**
