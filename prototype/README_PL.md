# Aetherian — prototyp 0.1

**Eksperymentalne pliki moda do Lionheart: Legacy of the Crusader.**
Kontrole statyczne i testy odwracalnego instalatora nie oznaczają, że rozgrywka
została sprawdzona. Aktualny stan testów silnika opisuje `RUNTIME_PL.md`.

## Zawartość

- Nowa definicja rasy **Aetherian**, bez podmieniania istniejących ras.
- Model człowieka płci żeńskiej jako zastępstwo. W kreatorze wybierz **Female / Kobieta**.
  Oba wpisy modelu wskazują kobietę, ale silnik nadal pozwala wybrać płeć męską;
  wpływa ona na dialogi, więc nie wybieraj jej w tym prototypie.
- Początkowo: ST 4, PE 6, EN 4, CH 6, IN 5, AG 6, LK 4; 6 punktów do rozdania.
  Trzy umiejętności specjalizowane, bez osobnego wyboru cechy rasowej.
- **Energia:** pojemność 100, regeneracja 3 na sekundę dla tej rasy.
  To wykorzystanie istniejącego zasobu many: pasek i część interfejsu nadal mówią
  „Mana”, nie ma drugiego niezależnego paska. Pojemność jest w prototypie stała.
- 61 oryginalnych definicji zaklęć otrzymuje dodatkowe ograniczenie wykluczające
  Aetherian zarówno przy wyświetlaniu, jak i sprawdzaniu możliwości rzucenia.
  Dotyczy to także części efektów różdżek. Inne rasy zachowują swoje warunki.
- Polskie nazwy i opisy dopisane do istniejącego `Local.txt` w UTF-16LE.

| Zdolność | Koszt energii | Odnowienie | Działanie zapisane w danych |
|---|---:|---:|---|
| Rzut Czakramem | 12 | 1,2 s | 7–11 obrażeń ciętych, z premiami drugiej ręki i Boskiego Ognia |
| Boski Ogień | 20 | 12 s | Przez 12 s: +2–4 obrażeń od ognia czakramem i jego rzutem |
| Skrzydła Brzasku | 25 | 20 s | Przez 6 s: +15% ruchu i +5 klasy pancerza; bez latania |

**Czakram Świtu:** 2–5 obrażeń ciętych, +10% szybkości animacji ataku odziedziczone
po szabli. Tymczasowo model szabli, ikona złotego pierścienia.

**Czakram Brzasku:** wyposażenie drugiej ręki, +1 klasy pancerza i +1–3 obrażeń
ciętych głównym czakramem i jego rzutem. Tymczasowo model małej tarczy.
To mechaniczny prototyp pary broni: dodatkowe obrażenia są składnikiem jednego
ataku, a nie drugim niezależnym trafieniem. Nie zmieniamy globalnej liczby slotów.

Rzut korzysta z istniejącego efektu świetlistego lodowego pierścienia, ale zadaje
obrażenia cięte. Nie ma animacji powrotu, rykoszetów ani zużywania amunicji.
Na tym etapie można użyć tej zdolności także bez założonego głównego czakramu.

## Instalacja na Windows

Wymagany **Python 3.8 lub nowszy**. Zamknij grę. Użyj osobnej kopii instalacji
i nowej rozgrywki testowej — nowe zasoby zapisane w sejwie nie znikną automatycznie
po odinstalowaniu moda.

Otwórz terminal w katalogu tej paczki. Podaj katalog zawierający `Lionheart.exe`:

```powershell
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --check
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --install
```

`--check` nie zapisuje niczego w katalogu gry. Instalator sprawdza całą paczkę
i oryginalne pliki przed pierwszą zmianą. Ta wersja jest przygotowana dla plików
z przekazanego archiwum; przy różnicy sum kontrolnych zatrzyma się z komunikatem.
Nie stosuj opcji wymuszania ani nie kopiuj części plików ręcznie po takim błędzie.

Instalator dodaje 11 zasobów i modyfikuje 68 plików: dwie formuły zasobu,
cztery drzewa dialogowe, 61 definicji zaklęć i plik lokalizacji. Kopie zmienianych
plików trafiają do `.aetherian-0.1/backup` w katalogu gry. Plik wykonywalny,
archiwum DAT i istniejące zapisy nie są modyfikowane.

Rozpocznij nową grę, wybierz Aetherian i kobietę. W rozmowie z wybranym duchem
w początkowej celi, gdy dostępne są już pytania o ucieczkę, wybierz:

> [Aetherian] Przywołuję moje czakramy światła.

Opcja daje obie bronie jednorazowo. Potem wróć do zwykłej rozmowy o ucieczce.
Taka sama zapasowa opcja jest dodana u kowala Eduardo w Barcelonie.
Załóż Czakram Świtu w slocie broni i Czakram Brzasku w miejscu małej tarczy.
Nowych zdolności szukaj w gałęzi walki, w „Aetherian — dyscypliny światła”.
Sposób prezentacji nowej gałęzi wymaga sprawdzenia w działającym silniku.

Jeśli rasy lub gałęzi nie ma na liście, zakończ test i zachowaj informację o tym
ekranie. Nie wybieraj istniejącej rasy, licząc na automatyczną konwersję.

## Odinstalowanie

Zamknij grę i uruchom:

```powershell
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --uninstall
```

Instalator przywraca oryginały i usuwa dodane zasoby. Gdy plik został później
zmieniony, zatrzyma się przed przywracaniem, zamiast nadpisywać dodatkowe mody.
Wróć do zapisu utworzonego przed instalacją lub zacznij nową grę bez moda.

## Model roboczy

W `art/` znajdują się `.blend`, `.glb` i podgląd PNG: jasna dorosła kobieca postać,
aureola, małe piórzaste skrzydła, sandały i dwie świetliste obręcze.

**To uproszczona bryła projektowa z referencyjnym szkieletem, nie gotowy model gry.**
Wymaga dopracowania sylwetki, retopologii, skinningu, animacji i eksportu GR2.
Nazwy części kości nawiązują do konwencji Bip01, ale zgodność z dokładnym
szkieletem Lionhearta nie została potwierdzona. Instalator nie kopiuje tych
plików do gry. Render nie jest zrzutem ekranu z Lionhearta.

## Co sprawdzić w rozgrywce

1. Czy rasa pojawia się w kreatorze; czy działa wybór kobiety i przejście do gry.
2. Czy początkowa rozmowa i ucieczka przebiegają normalnie.
3. Czy opcja czakramów działa tylko raz, także po zapisaniu i wczytaniu.
4. Czy można założyć obie bronie i czy odłożenie drugiej usuwa jej premie.
5. Czy widać trzy zdolności; czy zwykłe zaklęcia są dla tej rasy zablokowane.
6. Czy rzut pobiera 12 energii, a zasób wraca o 3 na sekundę.
7. Czy Boski Ogień kończy się po 12 s i nie kumuluje po ponownym użyciu.
8. Czy premia Skrzydeł Brzasku znika po 6 s.
9. Czy inna rasa zachowuje dotychczasową pojemność many, regenerację i zaklęcia.

Niepotwierdzone pozostają m.in. obsługa nowej rasy przez scenariusz, działanie
nowych pozycji list zasobów i kolejność ładowania zasobów luźnych względem DAT.
Nie usuwaj całego cache ani archiwum gry w celu wymuszania działania.

## Źródła i testy

`dev/` zawiera generator zasobów, parser formatu, testy i skrypt Blender.
Narzędzia deweloperskie wymagają Pythona 3.10 lub nowszego; instalator działa od 3.8.
Generator odnosi się do ścieżek roboczych autora; przy samodzielnym budowaniu
ustaw `BASE` i `OUT` oraz lokalizację spisu archiwum w skrypcie testowym.
Do instalacji gotowej paczki te skrypty nie są potrzebne.

`validation.json` opisuje kontrole składni, odwołań do zasobów, ograniczeń rasy,
zgodności instalacji, odinstalowania i wycofania zmian po symulowanym błędzie.
Te kontrole nie symulują wykonywania zdolności przez silnik.
