# Aetherian — prototyp moda do Lionheart

Eksperymentalny prototyp 0.1 dla Lionheart: Legacy of the Crusader.

## Pobieranie

Paczka ZIP jest przygotowana. Link do pobrania pojawi się po potwierdzeniu jej publicznej publikacji przez właściciela repozytorium.

Paczka zawiera instalator, pliki moda, instrukcję po polsku i robocze modele Blender/GLB. Wymaga własnej instalacji gry zgodnej z wersją wskazaną przez instalator oraz Python 3.10 lub nowszego.

## Stan prototypu

- Definicja nowej rasy Aetherian.
- Dwa czakramy: główna broń i wyposażenie drugiej ręki z premią do obrażeń.
- Rzut Czakramem, Boski Ogień i Skrzydła Brzasku.
- Energia wykorzystująca mechanizm many: pojemność 100 i regeneracja 3/s.
- Polskie opisy i odwracalny instalator z kopiami oryginałów.

**Działanie w grze nie zostało potwierdzone.** Przeszły kontrole plików oraz testy instalacji i odinstalowania. Próby uruchomienia gry w środowisku Wine zakończyły się przed ekranem gry; nie uruchamiały się również kontrolne programy 32-bitowe.

Grafika w grze nadal korzysta z modeli zastępczych. Model z aureolą, małymi skrzydłami, sandałami i świetlistymi obręczami jest osobnym roboczym źródłem, bez eksportu GR2. Drugi czakram nie ma niezależnej animacji ataku. To nie jest gotowa, przetestowana wersja moda.

## Instalacja

Rozpakuj ZIP i przeczytaj `Aetherian-0.1/README_PL.md` oraz `RUNTIME_PL.md`. Zamknij grę i użyj osobnej kopii instalacji oraz nowej rozgrywki testowej.

```powershell
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --check
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --install
```

Odinstalowanie:

```powershell
py -3 install.py --game "C:\Gry\Lionheart Legacy of the Crusader" --uninstall
```

Repozytorium zawiera pliki prototypu, bez pełnej gry i jej pliku wykonywalnego.
