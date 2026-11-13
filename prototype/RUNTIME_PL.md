# Stan testów silnika — 13 listopada 2026

**Nie potwierdzono działania prototypu w uruchomionej grze.**

Przygotowano odrębną kopię zasobów z dostarczonego archiwum oraz przenośne
Wine 11.21 amd64 WoW64 i ekran Xorg z wirtualnym sterownikiem obrazu.
Pierwsza próba rozpakowania biblioteką libarchive nie obsłużyła części archiwum
RAR5; pełne rozpakowanie zasobów narzędziem 7-Zip 25.01 zakończyło się komunikatem
„Everything is Ok”. Pominięto duży `dataZZZ.dat`, pozostawiając zasoby luźne.

64-bitowy program kontrolny `wine cmd /c echo Wine-working` wykonał się poprawnie.
Uruchomienie `Lionheart.exe` zakończyło się przed ekranem gry komunikatem Wine:

```text
Application could not be started, or no application associated with the specified file.
ShellExecuteEx failed
```

Taki sam błąd wystąpił przy niezależnym kontrolnym programie 32-bitowym z paczki
Wine (Notepad i CMD), także przy próbie poza podstawową piaskownicą poleceń.
Przyczyna problemu środowiska 32-bitowego pozostaje nierozstrzygnięta.
Nie jest to dowód niezgodności samej gry ani błąd działania nowych zasobów.

Próby wykonywano przed zainstalowaniem prototypu w pełnej kopii gry.
Nie sprawdzono kreatora, nowej rasy, działania umiejętności, obrażeń,
regeneracji ani zapisywania rozgrywki. Plik wykonywalny nie był modyfikowany.

Kontrole opisane w `validation.json` dotyczą parsowania zasobów,
istnienia odwołań, warunków zapisanych w danych i poprawności odwracalnego
instalatora. Nie zastępują testu na działającej instalacji Windows.

Model 3D wyeksportowano do GLB i otwarto jako scenę Blender; sprawdzono obecność
siatek i szkieletu, a podgląd wyrenderowano. Nie ma eksportu GR2 ani animacji
zgodnych z Lionheartem.
