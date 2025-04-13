# Dokument wymagań produktu (PRD) - FashionDetector

## 1. Przegląd produktu

FashionDetector to aplikacja webowa umożliwiająca użytkownikom wyszukiwanie ubrań online na podstawie zdjęć. Głównym celem produktu jest uproszczenie i przyspieszenie procesu odnajdywania konkretnych części garderoby w sklepach internetowych.

Aplikacja wykorzystuje zaawansowane modele AI (LLM) do analizy zdjęć odzieży, generowania ich opisów tekstowych, a następnie automatycznego przeszukiwania popularnych sklepów internetowych w celu znalezienia identycznych lub podobnych produktów.

W fazie MVP, aplikacja skupia się wyłącznie na górnych częściach garderoby (koszulki, bluzy, kurtki, itp.) i przeszukuje sklepy takie jak Zalando, Modivo i ASOS. Wyniki wyszukiwania są prezentowane w formie listy linków (maksymalnie 5 pozycji).

## 2. Problem użytkownika

Manualne przeglądanie stron internetowych w poszukiwaniu konkretnych ubrań jest czasochłonne i frustrujące. Użytkownicy często:

- Tracą znaczną ilość czasu na przeglądanie wielu stron sklepów
- Rezygnują z zakupu ubrań podobnych do tych, które im się podobają, ze względu na trudności w ich znalezieniu
- Nie mają skutecznego narzędzia do identyfikacji produktów widzianych np. na zdjęciach w mediach społecznościowych
- Muszą samodzielnie formułować zapytania tekstowe, które często nie prowadzą do znalezienia pożądanego produktu

FashionDetector rozwiązuje te problemy, umożliwiając użytkownikom przesłanie zdjęcia ubrania i automatyczne wyszukanie tego samego lub podobnego produktu w wielu sklepach jednocześnie.

## 3. Wymagania funkcjonalne

1. Przesyłanie zdjęć:
   - System musi umożliwiać użytkownikom przesyłanie zdjęć górnych części garderoby
   - Obsługiwane będą powszechnie używane formaty plików graficznych (JPEG, PNG)

2. Analiza obrazu:
   - System wykorzystuje model LLM do analizy przesłanego zdjęcia
   - Model rozpoznaje typ odzieży, kolor, wzory, nadruki i inne istotne cechy
   - Wynikiem analizy jest szczegółowy opis tekstowy ubrania

3. Wyszukiwanie produktów:
   - System automatycznie przeszukuje sklepy internetowe (Zalando, Modivo, ASOS) używając web scrapingu
   - Wyszukiwanie uwzględnia wszystkie rozpoznane cechy ubrania
   - System szuka produktów o minimalnym progu podobieństwa 85%

4. Prezentacja wyników:
   - System wyświetla maksymalnie 5 najlepiej dopasowanych produktów
   - Produkty dokładnie dopasowane (≥85% podobieństwa) są priorytetyzowane i pokazywane na początku listy
   - Jeśli produkt w identycznym kolorze nie jest dostępny, system pokazuje alternatywne kolory
   - Wyniki są prezentowane w formie listy linków do stron produktów

5. Obsługa czasu wykonania:
   - Czas wyszukiwania nie powinien przekraczać 10 sekund
   - System powiadamia użytkownika, gdy czas wyszukiwania przekracza 10 sekund
   - W przypadku braku wyników, system informuje o tym użytkownika

## 4. Granice produktu

Poniższe funkcjonalności i cechy NIE wchodzą w zakres MVP:

1. Zaawansowany interfejs użytkownika
   - MVP skupia się na funkcjonalności, a nie na atrakcyjności UI

2. Rozpoznawanie dolnych części garderoby i dodatków
   - MVP koncentruje się wyłącznie na górnych częściach garderoby

3. Funkcja zapisywania/oznaczania ulubionych przedmiotów
   - Ta funkcjonalność będzie rozważona w późniejszych wersjach produktu

4. Filtrowanie wyników (np. wg ceny, rozmiaru)
   - Filtrowanie nie jest częścią MVP

5. Integracja z API sklepów
   - MVP korzysta z web scrapingu zamiast API sklepów

6. Mechanizm raportowania nieprawidłowych wyników
   - Zostanie dodany w późniejszych wersjach

7. Możliwość edycji/kadrowania zdjęć przed przesłaniem do analizy
   - Zostanie dodana w późniejszych wersjach

8. Aplikacje mobilne (iOS, Android)
   - MVP będzie dostępny wyłącznie jako aplikacja webowa

9. Sortowanie wyników
   - Zostanie dodane w późniejszych wersjach

## 5. Historyjki użytkowników

### US-001
**Tytuł**: Przesyłanie zdjęcia ubrania

**Opis**: Jako użytkownik, chcę przesłać zdjęcie górnej części garderoby, aby znaleźć identyczny lub podobny produkt online.

**Kryteria akceptacji**:
- Interfejs umożliwia przesłanie zdjęcia z urządzenia użytkownika
- Obsługiwane są formaty JPEG i PNG
- System weryfikuje, czy przesłany plik jest obrazem
- Po przesłaniu zdjęcia, system automatycznie rozpoczyna proces analizy

### US-002
**Tytuł**: Analiza przesłanego zdjęcia

**Opis**: Jako system, chcę analizować przesłane zdjęcie za pomocą modelu LLM, aby generować dokładny opis tekstowy przedstawionego ubrania.

**Kryteria akceptacji**:
- System prawidłowo identyfikuje górną część garderoby na zdjęciu
- System rozpoznaje kolor ubrania
- System identyfikuje wzory i nadruki na ubraniu
- System generuje szczegółowy opis tekstowy ubrania
- Analiza jest przeprowadzana w czasie nieprzekraczającym 5 sekund

### US-003
**Tytuł**: Wyszukiwanie produktów w sklepach online

**Opis**: Jako system, chcę wykorzystać wygenerowany opis ubrania do przeszukania popularnych sklepów internetowych, aby znaleźć identyczne lub podobne produkty.

**Kryteria akceptacji**:
- System przeszukuje sklepy Zalando, Modivo i ASOS
- System prawidłowo identyfikuje produkty z podobieństwem ≥85% jako dokładne dopasowania
- System znajduje również produkty podobne, ale niespełniające progu 85% podobieństwa
- System prawidłowo obsługuje wzory i nadruki podczas wyszukiwania
- System znajduje alternatywne kolory produktu, jeśli oryginalny kolor nie jest dostępny
- Wyszukiwanie jest przeprowadzane w czasie nieprzekraczającym 10 sekund

### US-004
**Tytuł**: Wyświetlanie wyników wyszukiwania

**Opis**: Jako użytkownik, chcę zobaczyć listę znalezionych produktów, aby móc wybrać i zakupić interesujący mnie przedmiot.

**Kryteria akceptacji**:
- System wyświetla maksymalnie 5 najlepiej dopasowanych produktów
- Dokładne dopasowania (≥85% podobieństwa) są pokazywane na początku listy
- Każdy wynik zawiera link do strony produktu w sklepie
- Kliknięcie w link przenosi użytkownika bezpośrednio do strony produktu
- System pokazuje alternatywne kolory produktu, gdy oryginalny kolor nie jest dostępny

### US-005
**Tytuł**: Informacja o czasie wyszukiwania

**Opis**: Jako użytkownik, chcę otrzymać powiadomienie, gdy czas wyszukiwania przekracza 10 sekund, aby wiedzieć, że system nadal pracuje.

**Kryteria akceptacji**:
- System monitoruje czas wyszukiwania
- Po przekroczeniu 10 sekund, system wyświetla powiadomienie dla użytkownika
- Powiadomienie informuje, że wyszukiwanie trwa dłużej niż oczekiwano, ale nadal jest przetwarzane
- System kontynuuje wyszukiwanie mimo przekroczenia czasu

### US-006
**Tytuł**: Informacja o braku wyników

**Opis**: Jako użytkownik, chcę otrzymać informację, gdy system nie znajdzie żadnych pasujących produktów, aby wiedzieć, że moje wyszukiwanie zostało zakończone.

**Kryteria akceptacji**:
- System sprawdza liczbę znalezionych wyników
- Gdy liczba wyników wynosi 0, system wyświetla odpowiedni komunikat
- Komunikat informuje, że nie znaleziono żadnych pasujących produktów
- System sugeruje ponowne przesłanie innego zdjęcia lub zmiany w parametrach wyszukiwania

### US-007
**Tytuł**: Prezentacja produktów niedostępnych w sprzedaży

**Opis**: Jako użytkownik, chcę widzieć również produkty, które nie są już dostępne w sprzedaży, aby mieć pełną informację o znalezionych dopasowaniach.

**Kryteria akceptacji**:
- System dołącza do wyników również produkty niedostępne w sprzedaży
- Produkty niedostępne są odpowiednio oznaczone
- Produkty niedostępne nie są uwzględniane w limicie 5 wyników, jeśli dostępne są inne pasujące produkty
- System dołącza link do produktu, mimo jego niedostępności

## 6. Metryki sukcesu

Sukces produktu będzie mierzony przy użyciu następujących metryk:

1. Skuteczność wyszukiwania:
   - Procent wyszukiwań, które skutkują znalezieniem dokładnego dopasowania (≥85% podobieństwa)
   - Docelowa wartość: minimum 70% wyszukiwań powinno znajdować dokładne dopasowanie

2. Szybkość działania:
   - Średni czas od przesłania zdjęcia do prezentacji wyników
   - Docelowa wartość: średnio poniżej 8 sekund, maksymalnie 10 sekund

3. Dokładność rozpoznawania:
   - Procent prawidłowo rozpoznanych cech ubrania (typ, kolor, wzory, nadruki)
   - Docelowa wartość: minimum 85% prawidłowo rozpoznanych cech

4. Użyteczność wyników:
   - Procent przypadków, gdy użytkownik klika w co najmniej jeden z zaproponowanych linków
   - Docelowa wartość: minimum 60% wyszukiwań powinno skutkować kliknięciem w link

Te metryki będą monitorowane po wdrożeniu MVP i posłużą jako podstawa do planowania kolejnych iteracji produktu. 