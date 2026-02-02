# PII Anonymizer

A document anonymization tool that detects and replaces personally identifiable information (PII) with placeholders, allowing safe use of documents with AI platforms.

## What it does

Upload documents containing sensitive information. The system identifies PII (names, emails, phone numbers, SSNs, credit cards, addresses) and replaces each instance with a consistent placeholder like [PERSON_1] or [EMAIL_1]. Copy the anonymized text to any AI tool. Original values are encrypted and can be restored later.

## Requirements

- Docker and Docker Compose
- 4GB RAM minimum

## Deployment

1. Clone the repository

2. Create environment file:
```
cp .env.example .env
```

3. Edit .env and set:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@db:5432/pii_anonymizer
```

4. Build and run:
```
docker-compose up --build -d
```

5. Access the application at http://localhost:3000

## Usage

1. Register an account
2. Upload a document (PDF, DOCX, or TXT)
3. Review detected PII and anonymized output
4. Export anonymized document or copy text
5. Use Decrypt tab to view original values when needed

## Project Structure

```
PII-Anonymizer/
  backend/         Python FastAPI server
  frontend/        React web application
  docker-compose.yml
```
