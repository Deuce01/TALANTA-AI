# TALANTA AI Deployment Guide

## Free Resources (MVP/Development)

### Hosting & Infrastructure
- **Frontend**: Streamlit Community Cloud (free)
- **Database**: PostgreSQL on Railway (free tier: 500MB)
- **File Storage**: GitHub (code) + local CSV files
- **Domain**: Free subdomain from hosting provider

### AI & APIs
- **LLM**: Google Gemini API (free tier: 15 requests/minute)
- **NLP**: spaCy with free models
- **Job Data**: Manual scraping from public sites

### Development Tools
- **Version Control**: GitHub (free)
- **Environment**: Local development
- **Monitoring**: Basic Streamlit logs

### Cost: $0/month

## Production Setup

### Hosting & Infrastructure
- **Frontend**: AWS EC2 or DigitalOcean ($10-20/month)
- **Database**: AWS RDS PostgreSQL ($15-30/month)
- **File Storage**: AWS S3 ($5-10/month)
- **CDN**: CloudFlare (free tier)
- **Domain**: Custom domain ($10-15/year)

### AI & APIs
- **LLM**: Google Gemini Pro API ($0.50-2.00 per 1M tokens)
- **NLP**: Cloud-based NLP services or self-hosted
- **Job Data**: Automated scraping + job board APIs

### Production Tools
- **Monitoring**: AWS CloudWatch ($5-15/month)
- **CI/CD**: GitHub Actions (free)
- **Security**: SSL certificates (free via Let's Encrypt)
- **Backup**: Automated database backups ($5-10/month)

### Estimated Cost: $50-100/month

## Feature-by-Feature Resource Requirements

### Feature 1: Career Advisor ✅
**Free**: Streamlit + Gemini API + GitHub
**Production**: Same + monitoring + custom domain

### Feature 2: Skills Demand Analyzer
**Free**: 
- Manual job data collection
- Local CSV storage
- Basic spaCy NLP

**Production**:
- Automated web scraping
- PostgreSQL database
- Advanced NLP models

### Feature 3: Skills Gap Analysis
**Free**:
- Sample CV datasets
- Local processing
- Basic matching algorithms

**Production**:
- Real CV processing
- Advanced ML models
- Scalable processing

### Feature 4: Workforce Dashboard
**Free**:
- Plotly charts
- Static data
- Basic exports

**Production**:
- Real-time data
- Interactive dashboards
- Advanced analytics

## Migration Path

1. **Start Free**: Build and test all features
2. **Hybrid**: Move database to cloud, keep free hosting
3. **Scale Up**: Migrate to production infrastructure
4. **Optimize**: Add monitoring, caching, CDN

## Quick Start Commands

```bash
# Free deployment to Streamlit Cloud
git push origin main
# Connect GitHub repo to Streamlit Cloud

# Production deployment (example)
docker build -t talanta-ai .
docker run -p 8501:8501 talanta-ai
```