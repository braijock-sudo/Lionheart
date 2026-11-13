# Diagnostyka awarii przed kreatorem

Pełny prototyp 0.1 spowodował awarię u użytkownika po wybraniu „Rozpocznij grę”.
Przyczyna nie została ustalona. Testy instalatora nie sprawdzają działania silnika.

`race_only.py` używa pliku rasy **z już rozpakowanej paczki moda**. Nie zawiera
zasobów gry ani ich nie pobiera. Instaluje tylko istniejący w paczce plik
`Data/Resources/Races/Aetherian.Race`. Nie instaluje zmian umiejętności, many,
zaklęć, dialogów ani lokalizacji. To test diagnostyczny, a nie poprawiona pełna wersja.

## Najpierw przywróć grę bez moda

Zamknij grę. W folderze pełnego moda, obok `install.py`, uruchom:

```powershell
py -3 install.py --game "E:\SteamLibrary\steamapps\common\Lionheart Legacy of the Crusader" --uninstall
```

Uruchom grę bez moda i sprawdź otwieranie kreatora. Jeśli nadal występuje awaria,
nie instaluj testu. Zgłoś wynik oraz komunikat odinstalowania.

## Test samej rasy

Jeżeli kreator bez moda działa, zamknij grę. W tym samym folderze rozpakowanego
moda pobierz sam skrypt diagnostyczny:

```powershell
Invoke-WebRequest "https://raw.githubusercontent.com/braijock-sudo/Lionheart/main/diagnostics/race_only.py" -OutFile "race_only.py"
```

Sprawdź, a potem zainstaluj test:

```powershell
py -3 race_only.py --game "E:\SteamLibrary\steamapps\common\Lionheart Legacy of the Crusader" --check
py -3 race_only.py --game "E:\SteamLibrary\steamapps\common\Lionheart Legacy of the Crusader" --install
```

Uruchamiaj te polecenia osobno. Wynik kontroli powinien zawierać **1 planned changes**.
Nie przechodź do instalacji po błędzie. Skrypt sprawdza również zgodność oryginalnej
paczki i przywróconych plików, ale zapisuje wyłącznie jedną definicję rasy.

Sprawdź, czy otwiera się kreator i czy widać rasę Aetherian. Nie używaj testu
do właściwej rozgrywki. Komunikat o wybraniu rasy po instalacji pochodzi z bazowego
instalatora; ten test nie zawiera umiejętności ani czakramów.

## Usunięcie testu

Zamknij grę i użyj **race_only.py**, nie install.py:

```powershell
py -3 race_only.py --game "E:\SteamLibrary\steamapps\common\Lionheart Legacy of the Crusader" --uninstall
```

Test ma osobny katalog stanu `.aetherian-race-test`. Nie nakładaj na niego pełnego
moda. Zgłoś, czy kreator działa bez moda i czy działa z samą rasą.

Zweryfikowano wybór dokładnie jednego pliku, brak zmian pozostałych plików,
odinstalowanie oraz blokadę instalacji przy obecnym pełnym prototypie.
Nie potwierdzono działania tej wersji w grze. Wymagany Python 3.8 lub nowszy.
