# Architektura UI dla FashionDetector

## 1. Przegląd struktury UI

Architektura UI dla FashionDetector składa się z czterech głównych widoków tworzących liniowy przepływ użytkownika, który rozpoczyna się od uwierzytelnienia, poprzez przesłanie zdjęcia, proces analizy, aż do prezentacji wyników. Aplikacja jest implementowana przy użyciu Dash - frameworka Pythonowego, który integruje się z backendem FastAPI. Struktura nawigacji jest prosta i intuicyjna, wspierająca główny cel aplikacji - wyszukiwanie ubrań na podstawie zdjęcia.

Cała aplikacja wykorzystuje pastelową paletę kolorów i jest zbudowana z wykorzystaniem komponentów Dash Bootstrap dla zapewnienia responsywności. Podstawowy przepływ użytkownika jest prosty: logowanie → przesłanie zdjęcia → oczekiwanie na przetwarzanie → przeglądanie wyników → ponowne wyszukiwanie.

## 2. Lista widoków

### Widok Logowania
- **Ścieżka**: `/login`
- **Główny cel**: Uwierzytelnienie użytkownika w systemie
- **Kluczowe informacje**: Pola logowania, komunikaty o błędach
- **Kluczowe komponenty**:
  - Formularz logowania (dbc.Form)
  - Pola wprowadzania loginu i hasła (dbc.Input)
  - Przycisk logowania (dbc.Button)
  - Obsługa błędów (dbc.Alert)
  - Logo aplikacji (html.Img)

### Widok Przesyłania Zdjęcia (Home)
- **Ścieżka**: `/`
- **Główny cel**: Umożliwienie użytkownikowi przesłania zdjęcia ubrania do analizy
- **Kluczowe informacje**: Wskazówki dotyczące przesyłania, obsługiwane formaty, limity rozmiaru
- **Kluczowe komponenty**:
  - Obszar drag & drop (dcc.Upload)
  - Wskazówki wizualne dotyczące przesyłania (dbc.Card z instrukcjami)
  - Przycisk inicjujący wyszukiwanie (dbc.Button)
  - Walidacja pliku (formaty JPG/PNG, max 5MB)
  - Header z nazwą aplikacji i opcją wylogowania
  - Komponent przechowujący stan (dcc.Store)

### Widok Przetwarzania
- **Ścieżka**: `/processing/{search_id}`
- **Główny cel**: Informowanie użytkownika o postępie przetwarzania
- **Kluczowe informacje**: Status przetwarzania, szacowany czas
- **Kluczowe komponenty**:
  - Wskaźnik ładowania "kręcące się kółko" (dcc.Loading z type="circle")
  - Informacja o szacowanym czasie (dbc.Alert dla czasu >10s)
  - Przechowywanie ID wyszukiwania (dcc.Store)
  - Mechanizm odpytywania API o status (Interval)
  - Obsługa błędów (dbc.Alert)

### Widok Wyników Wyszukiwania
- **Ścieżka**: `/results/{search_id}`
- **Główny cel**: Prezentacja znalezionych produktów
- **Kluczowe informacje**: Lista produktów, linki do sklepów, alternatywne kolory
- **Kluczowe komponenty**:
  - Lista wyników (html.Ul, html.Li)
  - Linki do produktów (dcc.Link lub html.A)
  - Sekcje alternatywnych kolorów jako lista zagnieżdżona
  - Przycisk "Nowe wyszukiwanie" (dbc.Button)
  - Komunikat o braku wyników (dbc.Alert, gdy lista jest pusta)
  - Miniatura przesłanego zdjęcia (html.Img)

## 3. Mapa podróży użytkownika

1. **Uwierzytelnienie**
   - Użytkownik wchodzi na stronę i jest przekierowany do widoku logowania
   - Wprowadza login i hasło
   - Po pomyślnym uwierzytelnieniu jest przekierowany do widoku głównego (Home)

2. **Przesłanie zdjęcia**
   - Użytkownik znajduje się na stronie głównej
   - Przeciąga i upuszcza zdjęcie ubrania lub klika obszar, aby wybrać plik
   - System waliduje plik (format, rozmiar)
   - Użytkownik klika "Szukaj"
   - System przekierowuje do widoku przetwarzania

3. **Przetwarzanie**
   - Aplikacja wysyła zdjęcie do API
   - Użytkownik widzi wskaźnik ładowania (kręcące się kółko)
   - Jeśli czas przetwarzania przekracza 10 sekund, pokazuje się komunikat
   - System odpytuje API o status wyszukiwania
   - Po zakończeniu przetwarzania, użytkownik jest przekierowany do widoku wyników

4. **Przeglądanie wyników**
   - Użytkownik widzi listę znalezionych produktów (lub komunikat o braku wyników)
   - Każdy produkt ma link do sklepu
   - Pod każdym produktem znajduje się informacja o alternatywnych kolorach z linkami
   - Użytkownik może kliknąć "Nowe wyszukiwanie", aby powrócić do widoku głównego

5. **Obsługa błędów**
   - W przypadku błędu przetwarzania, użytkownik widzi komunikat
   - Może powrócić do widoku głównego i spróbować ponownie

## 4. Układ i struktura nawigacji

Nawigacja w aplikacji FashionDetector jest prosta i liniowa, prowadząca użytkownika przez cały proces wyszukiwania:

```
Login → Home → Processing → Results → Home (dla nowego wyszukiwania)
```

- **Header**: Obecny na wszystkich stronach po zalogowaniu, zawiera logo aplikacji i przycisk wylogowania
- **Nawigacja kontekstowa**: Na widoku wyników znajduje się przycisk "Nowe wyszukiwanie"
- **Przekierowania automatyczne**:
  - Z logowania do Home po pomyślnym uwierzytelnieniu
  - Z przetwarzania do wyników po zakończeniu analizy
  - Do logowania, gdy sesja wygasła lub użytkownik się wylogował
- **Nawigacja poprzez URL**: Aplikacja wykorzystuje parametry URL (np. ID wyszukiwania) do identyfikacji stanu

## 5. Kluczowe komponenty

### 1. AuthManager
- **Opis**: Komponent zarządzający uwierzytelnianiem (integracja flask-login z Dash)
- **Funkcjonalności**: Logowanie, wylogowanie, weryfikacja sesji, przekierowania
- **Wykorzystanie**: Ochrona dostępu do widoków dla zalogowanych użytkowników

### 2. ImageUploader
- **Opis**: Komponent obsługujący przesyłanie zdjęć poprzez drag & drop
- **Funkcjonalności**: Walidacja plików, podgląd zdjęcia, przesyłanie do serwera
- **Wykorzystanie**: Główny element widoku Home

### 3. ProcessingIndicator
- **Opis**: Komponent pokazujący status przetwarzania
- **Funkcjonalności**: Wskaźnik ładowania, odpytywanie API o status, obsługa długiego przetwarzania
- **Wykorzystanie**: Główny element widoku Processing

### 4. ResultsList
- **Opis**: Komponent wyświetlający wyniki wyszukiwania
- **Funkcjonalności**: Lista produktów, alternatywne kolory, linki do sklepów
- **Wykorzystanie**: Główny element widoku Results

### 5. ErrorHandler
- **Opis**: Komponent do obsługi i prezentacji błędów
- **Funkcjonalności**: Przechwytywanie błędów, formatowanie komunikatów
- **Wykorzystanie**: We wszystkich widokach, gdzie mogą wystąpić błędy

### 6. APIClient
- **Opis**: Klasa pomocnicza do komunikacji z API
- **Funkcjonalności**: Metody do przesyłania zdjęć, sprawdzania statusu, pobierania wyników
- **Wykorzystanie**: We wszystkich komponentach, które komunikują się z API

### 7. StateManager
- **Opis**: Komponent do zarządzania stanem aplikacji
- **Funkcjonalności**: Przechowywanie ID wyszukiwania, statusu, komunikatów
- **Wykorzystanie**: We wszystkich widokach do zachowania spójności stanu aplikacji 