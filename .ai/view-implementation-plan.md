# API Endpoint Implementation Plan: POST /api/searches

## 1. Przegląd punktu końcowego

Endpoint do inicjowania wyszukiwania ubrań na podstawie przesłanego zdjęcia. Umożliwia użytkownikowi przesłanie obrazu przedstawiającego ubranie, które chce znaleźć w sklepach internetowych. System analizuje obraz przy użyciu modeli AI, identyfikuje kluczowe cechy odzieży i inicjuje równoległe wyszukiwanie w określonych sklepach online.

## 2. Szczegóły żądania

- **Metoda HTTP**: POST
- **Struktura URL**: `/api/searches`
- **Content-Type**: `multipart/form-data`
- **Parametry**:
  - **Wymagane**:
    - `image` (plik binowy) - Zdjęcie ubrania w formacie JPEG lub PNG
  - **Opcjonalne**:
    - `stores` (tablica stringów) - Lista sklepów do przeszukania, np. ["zalando", "modivo", "asos"]

- **Limity i walidacja**:
  - Akceptowane formaty obrazu: JPEG/PNG
  - Maksymalny rozmiar obrazu: 10 MB
  - Nazwy sklepów muszą znajdować się na liście obsługiwanych sklepów

## 3. Wykorzystywane typy

### Pydantic Models

```python
from pydantic import BaseModel, Field, conlist
from typing import List, Optional
from enum import Enum
from fastapi import UploadFile, File

class StoreEnum(str, Enum):
    ZALANDO = "zalando"
    MODIVO = "modivo"
    ASOS = "asos"
    # dodaj więcej obsługiwanych sklepów

class SearchRequest(BaseModel):
    stores: Optional[List[StoreEnum]] = None

class SearchResponse(BaseModel):
    search_id: str
    status: str = "processing"
    estimated_time_seconds: int = 10
    timestamp: str
```

## 4. Szczegóły odpowiedzi

- **Kod statusu**: 202 Accepted
- **Format odpowiedzi**: JSON
- **Struktura**:
  ```json
  {
    "search_id": "string",
    "status": "processing",
    "estimated_time_seconds": 10,
    "timestamp": "2023-04-14T19:22:37Z"
  }
  ```
- **Możliwe kody błędów**:
  - 400: Nieprawidłowy format obrazu (akceptowane tylko JPEG/PNG)
  - 413: Obraz zbyt duży
  - 429: Przekroczono limit zapytań
  - 500: Błąd serwera

## 5. Przepływ danych

1. **Walidacja wejścia**:
   - Sprawdzenie czy plik jest obrazem w formacie JPEG/PNG
   - Sprawdzenie czy rozmiar nie przekracza 10 MB
   - Walidacja opcjonalnej listy sklepów

2. **Przetwarzanie**:
   - Generowanie unikalnego identyfikatora wyszukiwania
   - Zapisanie obrazu w tymczasowym magazynie (S3)
   - Inicjowanie zadania w tle dla analizy obrazu i wyszukiwania

3. **Operacje na danych**:
   - Początkowe rekordy zostaną utworzone w tabelach `search_metrics` i `store_searches` po zakończeniu analizy
   - Rozpoznane atrybuty będą zapisywane w tabeli `attribute_recognitions`
   - Dane metryk wydajności będą aktualizowane po zakończeniu wszystkich operacji

4. **Interakcje zewnętrzne**:
   - API GPT-4 Vision dla analizy obrazu
   - Moduł Scrapy do przeszukiwania sklepów internetowych
   - AWS S3 do przechowywania obrazów

## 6. Względy bezpieczeństwa

1. **Walidacja plików**:
   - Sprawdzanie MIME type pliku
   - Ostrożne przetwarzanie binarnych danych obrazu
   - Skanowanie obrazów pod kątem złośliwego kodu

2. **Limity szybkości**:
   - Implementacja ograniczenia zapytań do 10/godz. dla użytkowników anonimowych
   - Implementacja ograniczenia zapytań do 100/godz. dla uwierzytelnionych użytkowników

3. **Uwierzytelnianie**:
   - Endpoint dostępny publicznie, opcjonalne uwierzytelnianie przez Supabase JWT

4. **Sanityzacja danych**:
   - Bezpieczne przetwarzanie przesłanych plików
   - Walidacja nazw sklepów przed użyciem w zapytaniach

## 7. Obsługa błędów

| Scenariusz | Kod HTTP | Komunikat | Akcja |
|------------|----------|-----------|-------|
| Nieprawidłowy format pliku | 400 | "Invalid image format. Only JPEG/PNG accepted." | Logowanie błędu, informowanie użytkownika |
| Przekroczenie rozmiaru pliku | 413 | "Image too large. Maximum size is 10 MB." | Logowanie błędu, informowanie użytkownika |
| Nieprawidłowa nazwa sklepu | 400 | "Invalid store name provided. Supported stores: zalando, modivo, asos." | Logowanie błędu, informowanie użytkownika |
| Przekroczony limit zapytań | 429 | "Rate limit exceeded. Try again later." | Logowanie zdarzenia, zwrócenie czasu pozostałego do resetowania limitu |
| Błąd wewnętrzny | 500 | "Internal server error. Please try again later." | Szczegółowe logowanie błędu, powiadomienie administratora |

## 8. Rozważania dotyczące wydajności

1. **Asynchroniczne przetwarzanie**:
   - Wykorzystanie zadań w tle FastAPI do długotrwałych operacji
   - Implementacja asynchronicznego przetwarzania dla równoległego wyszukiwania w wielu sklepach

2. **Limity zasobów**:
   - Ograniczenie równoczesnych zadań analizy obrazów
   - Dynamiczne zarządzanie zasobami dla procesów scrapowania

3. **Optymalizacja obrazów**:
   - Zmniejszenie rozdzielczości obrazów przed analizą AI
   - Przechowywanie zoptymalizowanych wersji obrazów

4. **Monitorowanie wydajności**:
   - Śledzenie czasów odpowiedzi dla różnych części procesu
   - Analiza metryk dla optymalizacji wąskich gardeł

## 9. Etapy wdrożenia

1. **Przygotowanie struktury projektu**:
   - Utworzenie modułu `searches` w strukturze API
   - Przygotowanie schematów Pydantic dla walidacji danych wejściowych

2. **Implementacja kontrolera API**:
   - Utworzenie endpointu POST w FastAPI
   - Implementacja walidacji obrazu
   - Konfiguracja response modeli

3. **Implementacja usługi wyszukiwania**:
   - Utworzenie klasy `SearchService` obsługującej logikę biznesową
   - Implementacja funkcji generowania ID wyszukiwania
   - Integracja z usługą analizy obrazów

4. **Integracja z zewnętrznymi API**:
   - Połączenie z API GPT-4 Vision do analizy obrazów
   - Implementacja klientów dla komunikacji ze sklepami

5. **Konfiguracja zadań w tle**:
   - Implementacja mechanizmu kolejkowania zadań
   - Konfiguracja zarządzania stanami zadań

6. **Implementacja warstwy danych**:
   - Utworzenie repozytoriów dla interakcji z tabelami bazy danych
   - Implementacja zapisu metryk i statystyk

7. **Testy jednostkowe i integracyjne**:
   - Testy jednostkowe dla logiki biznesowej
   - Testy integracyjne dla całego flow API

8. **Konfiguracja limitów szybkości**:
   - Implementacja middleware dla ograniczania zapytań
   - Konfiguracja nagłówków rate-limiting

9. **Dokumentacja**:
   - Aktualizacja dokumentacji OpenAPI
   - Przygotowanie przykładów użycia dla deweloperów

10. **Wdrożenie**:
    - Konfiguracja CI/CD z GitHub Actions
    - Wdrożenie na środowisko AWS Lambda
    - Monitorowanie wydajności po wdrożeniu

## 10. Przykład implementacji

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import time
import uuid
from datetime import datetime, timezone

# Definicje typów
class StoreEnum(str, Enum):
    ZALANDO = "zalando"
    MODIVO = "modivo"
    ASOS = "asos"

class SearchResponse(BaseModel):
    search_id: str
    status: str = "processing"
    estimated_time_seconds: int = 10
    timestamp: str

# Inicjalizacja routera
router = APIRouter(tags=["searches"])

# Usługa wyszukiwania
class SearchService:
    async def validate_image(self, image: UploadFile) -> bool:
        # Walidacja typu MIME
        content_type = image.content_type
        valid_types = ["image/jpeg", "image/png"]
        
        if content_type not in valid_types:
            return False
            
        # Sprawdzenie rozmiaru
        await image.seek(0)
        content = await image.read()
        size_in_mb = len(content) / (1024 * 1024)
        
        await image.seek(0)  # Reset pozycji do ponownego użycia
        
        return size_in_mb <= 10

    async def process_search(self, image: UploadFile, stores: List[StoreEnum]) -> None:
        # Implementacja logiki przetwarzania w tle
        # - Zapisanie obrazu
        # - Analiza obrazu przez AI
        # - Inicjacja wyszukiwania w sklepach
        # - Zapis metryk do bazy danych
        pass

# Endpoint API
@router.post("/searches", response_model=SearchResponse, status_code=202)
async def create_search(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    stores: Optional[List[StoreEnum]] = Form(None),
    search_service: SearchService = Depends()
):
    # Walidacja obrazu
    is_valid = await search_service.validate_image(image)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Only JPEG/PNG accepted with max size 10MB."
        )
    
    # Generowanie ID wyszukiwania
    search_id = str(uuid.uuid4())
    
    # Określenie domyślnych sklepów jeśli nie podano
    if not stores:
        stores = [store for store in StoreEnum]
    
    # Dodanie zadania w tle
    background_tasks.add_task(
        search_service.process_search,
        image,
        stores
    )
    
    # Przygotowanie odpowiedzi
    timestamp = datetime.now(timezone.utc).isoformat()
    
    return SearchResponse(
        search_id=search_id,
        status="processing",
        estimated_time_seconds=10,
        timestamp=timestamp
    ) 