# FashionDetector

A web application that helps users find clothing items online by simply uploading images.

## Table of Contents
- [Project Description](#project-description)
- [Tech Stack](#tech-stack)

## Project Description

FashionDetector is a web application that simplifies and accelerates the process of finding specific clothing items online. Users can upload images of garments they like, and the application will automatically search popular online stores to find identical or similar products.

**Key Features:**
- Image upload for upper garments (shirts, sweaters, jackets, etc.)
- AI-powered image analysis using Large Language Models
- Automatic searching across major clothing stores
- Presentation of results as a list of direct links to products
- Finding both exact matches and similar alternatives

## Tech Stack

### Core Technologies
- **Backend Language**: Python 3.10+
- **AI/ML**: 
  - HuggingFace (model access)
  - GPT-4 Vision API (garment recognition)
- **CI/CD**: GitHub Actions

### Additional Components
- **Web Framework**: FastAPI
- **Web Scraping**: Scrapy
- **Database**: PostgreSQL
- **Cloud Infrastructure**: AWS Lambda + S3
- **Security Tools**: Bandit (Python static code analysis)

### Prerequisites
- Python 3.10 or higher
- PostgreSQL
- AWS account (for Lambda and S3)
- API keys for GPT-4 Vision

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FashionDetector.git
cd FashionDetector
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with your API keys and configuration
touch .env
```

6. Configure AWS credentials:
```bash
# Add your AWS credentials to the .env file
echo "AWS_ACCESS_KEY_ID=your_access_key" >> .env
echo "AWS_SECRET_ACCESS_KEY=your_secret_key" >> .env
echo "AWS_REGION=your_region" >> .env
```

7. Start the application:
```bash
uvicorn app.main:app --reload
```

## Project Scope

### MVP Includes:
- Image upload functionality for upper garments only
- AI-powered image analysis with LLM
- Web scraping of major clothing retailers (Zalando, Modivo, ASOS)
- Results display as a list of links (maximum 5 results)
- Processing of patterns and prints
- Alternative color suggestions when original is unavailable
- Response time target of 10 seconds

### MVP Excludes:
- Advanced user interface
- Recognition of bottom garments and accessories
- Favorite/bookmarking functionality
- Result filtering capabilities
- Store API integrations (using web scraping instead)
- Error reporting mechanisms
- Image editing/cropping before analysis
- Mobile applications (iOS, Android)
- Result sorting options

### Future Plans
After successful MVP implementation, the project will expand to include:
- Recognition of other garment types
- Enhanced user interface
- Filtering and sorting capabilities
- Mobile applications
- Direct API integrations with retailers

## Project Status

Current status: **Planning/Initial Development**

### Success Metrics
The project aims to achieve:
- Search effectiveness: 70% of searches resulting in exact matches
- Speed: Average response time under 8 seconds, maximum 10 seconds
- Recognition accuracy: 85% of garment features correctly identified
- Result usefulness: 60% of searches leading to at least one link click

## License

*License information to be defined.*

---

© 2025 FashionDetector Team 