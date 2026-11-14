# Repozytorium przewodnika OOOZ

Najnowszy build przewodnika można znaleźć na [naszej stronie internetowej](https://oooz.edu.pl/przewodnik/) i na kanale `#przewodnik` na [naszym serwerze Discord](https://discord.gg/AMGxG4TvDS).

Znalezione błędy prosimy zgłaszać tutaj w zakładce "Issues" lub na Discordzie.

## Buildowanie

1. Zainstaluj programy Git LFS (jeśli chcesz pracować z gitem), Graphviz, Python 3 oraz [Typst](https://typst.app/open-source/#download).
2. Stwórz wirtualne środowisko za pomocą `python3 -m venv ./venv/`. (Pyphen w Debianie nie ma języka polskiego.)
3. Zainstaluj potrzebne pakiety w Pythonie za pomocą `./venv/bin/pip3 install -r requirements.txt`.
4. Uruchom `./build.py --watch`. Od teraz przewodnik będzie buildowany po każdej zmianie w plikach źródłowych. Jeśli chcesz tylko jednorazowo zbuildować przewodnik, to usuń opcję `--watch`.

Produkty tego procesu to:
- `build/discord.xml` - Przewodnik w formie dla Discorda. Ten plik jest konsumowany przez komendę: `./deploy-discord.py --token TOKEN_BOTA --guild ID_SERWERA --channel ID_KANAŁU --purge`
- `build/download.pdf` - Przewodnik w formie PDF-a.
- `build/webpage/` - Przewodnik w formie strony internetowej. Zdeployowana strona musi otrzymać URL taki jak w atrybucie `url` w korzeniu `source.xml`.

## Praca z treścią

> [!WARNING]
> Z każdym nowym rokiem szkolnym trzeba zaktualizować daty i linki w "Jakie korzyści przynosi sukces w...", "Jak wystartować w…" i "Jak wygląda drugi i trzeci etap…".

> [!NOTE]
> Informacje w "Jakie są kursy/obozy przygotowujące do Olimpiady?", "Które zajęcia OKI wybrać?", "Ile wynosi próg do finału…" i "Jakie konkursy istnieją poza Olimpiadą?" mogą się nagle zdezaktualnić.

Cała treść przewodnika mieści się w pliku `source.xml`. XML to taki HTML, ale mniej odjechany i taki, w którym można definiować własne znaczniki. Strukturę gramatyczną `source.xml` opisuje plik `source.rnc` - schemat w języku RELAX NG Compact Syntax ([dokumentacja](https://relaxng.org/compact-tutorial-20030326.html)). Najważniejsze, co należy z niej wyciągnąć, to idea, że każdy znacznik może występować inline (czyli wewnątrz paragrafu) lub jako blok (czyli zajmując całą szerokość strony, wizualnie tworząc blok). Poniżej jest lista interesujących znaczników i ich znaczenie.

### `<answer>`

Odpowiedź na pytanie umieszczone w atrybucie `question`. Musi mieć unikalny na cały dokument atrybut `id`. Opcjonalnie można oznaczyć odpowiedź jako wartą uwagi w kontekście całego przewodnika ustawiając atrybut `important` na `yes`.

### `<code>`, blok/inline

Po prostu kod. Może występować zarówno inline jak i jako blok. W tym drugim przypadku trzeba oddzielić go od paragrafów otaczających go co najmniej jedną pustą linią. Przyjmuje opcjonalny atrybut `lang`. Dostępne języki to `bash`, `cpp` i `python`. Można łatwo dodać więcej, ale trzeba przy tym dokonać odpowiednich zmian w całym codebase'ie.

### `<contributor>`

Opisuje osobę, która miała "istotny wkład" do powstania obecnej wersji przewodnika. Zawartość znacznika to opis tego wkładu.

Atrybuty:
- `name` - `Imię "Pseudonim" Nazwisko` lub `Imię Nazwisko`.
- `discord-id` - ID użytkownika na Discordzie.
- `website` (opcjonalny) - Link do osobistej strony internetowej lub innego profilu internetowego (np. GitHub).

Trudno zdefiniować, jak bardzo wkład musi być istotny, aby był "istotny". Na pewno sama recenzja czy znajdywanie błędów nie jest "istotnym wkładem" - tak uważa też prawo autorskie. Najbezpieczniej będzie powiedzieć, że to po prostu lista osób, które posiadają prawa autorskie osobiste do tego utworu. Gdyby ktoś w przyszłości udzielił hosting, to pewnie też wypadałoby o tej osobie wspomnieć.

### `<emphasis>`, inline

Słowo lub krótka fraza z wymawianym naciskiem, czyli takim, który możnaby usłyszeć, gdyby autor czytał ten tekst.

### `<graph>`, blok

Graf w języku DOT ([dokumentacja](https://graphviz.org/documentation/)). Przyjmuje atrybut `description`, który ma opisywać graf w taki sposób, że osoba, która nie widzi obrazka, będzie w stanie zrozumieć, co na tym obrazku jest. [Bardziej szczegółowe wyjaśnienie, jak takie opisy pisać.](https://typst.app/docs/guides/accessibility/#textual-representations)

Kolory elementów grafu są automatycznie zmieniane przez `render_graph` w `build.py`, aby był widoczny na i czarnym i na białym tle. Obecny kod nie został napisany z myślą, że ktoś będzie w `<graph>` ustawiać jakieś kolory, więc jak tak zrobisz i nie wyjdzie, to nie martw się, że coś zrobiłeś źle. Błąd jest najpewniej w `build.py`.

### `<important>`, inline

Ważna informacja, którą czytelnik *musi* zobaczyć, gdyby tylko przeglądał tekst pobieżnie. Najlepsze użycie tego znacznika jest w pytaniu "Jaka jest najlepsza strategia na drugim etapie...".

### `<link>`, inline

Link do URL-a, który jest w atrybucie `url`. Znacznik musi zawierać jakiś tekst.

### `<list>`, blok

Lista `<item>`-ów, które z kolei zawierają po prostu zwykłe znaczniki blokowe. Czyli po prostu zwykła lista, jaką byś ujrzał w druku.

Atrybuty:
- `ordered` (domyślnie `no`) - `yes` jeśli lista jest ponumerowana. `no` jeśli jest wypunktowana.
- `compact` (domyślnie `yes`) - `yes` jeśli kolejne elementy listy nie powinny być oddzielone odstępem blokowym. `no` jeśli powinny być.

### `<math>`, inline

Wyrażenie matematyczne. Zawartość to taki mini-język. Kolejne "tokeny" (symbole, liczby, operatory itd.) muszą być oddzielone spacjami (z wyjątkiem nawiasów okrągłych). Przykład: `(1 + 2) * 3`. Dostępne symbole są zdefiniowane w `math_symbols` na początku `build.py`; nie jest to lista zamknięta na nowe dodatki. Do każdego tokenu można dodać indeks dolny lub górny poprzez dopisanie odpowiednio `_` lub `^` oraz ciągu znaków bez spacji. Przykład: `x_i+1 + 2^n`. [Zestaw dostępnych znaków w indeksach](https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts) jest bardzo ograniczony przez standard Unicode.

### `<note>`, blok

Informacja dla czytelnika, która niekoniecznie jest *ważna*, ale którą warto zapamiętać.

### `<placeholer>`, inline

W trakcie renderowania zastępywany przez automatycznie wygenerowany tekst. Klucz jest w atrybucie `for` i na razie jedyny zdefiniowana wartość to `contributors` - lista wszystkich wkładodawców.

### `<problem>`, inline

Odniesienie do zadania z OI lub OIJ z kolorem odpowiadającym etapowi. Przyjmuje atrybut `id`, który dla zadań z OI ma format `oi{EDYCJA}-{TRZYLITEROWY KOD ZADANIA}`, a dla zadań z OIJ - `oij{EDYCJA}-{ETAP JAKO LICZBA}-{TRZYLITEROWY KOD ZADANIA}`. Przykłady: `oi10-mal`, `oij15-3-cie`.

### `<ref>`, inline

Link do innego miejsca w dokumencie - na razie tylko do znaczników `<answer>`. Miejsce docelowe jest w atrybucie `id`.

### `<subanswer>`

Pododpowiedź na podpytanie w atrybucie `subanswer`.

### `<todo>`, blok

Notatka autorów dokumentu dla nich samych, co trzeba dopisać, zmienić, poprawić...

### `<warning>`, blok

Ostrzeżenie dla czytelnika.

**Komentarz:** Ze względu na to, iż przewodnik jest wydawany w trzech zupełnie niepodobnych formach prezentacji (Discordowy Markdown, HTML/CSS i Typst), zastosowany został bardzo wyraźny podział na warstwę semantyczną i warstwę prezentacji dokumentu. Znaczniki, które tłumaczą się na pogrubiony tekst lub kursywę, nie przyjmują nazwy od ich wyglądu (np. "bold" czy "italic"), tylko od funkcji, jaką one pełnią w tekście (np. "important" lub "emphasis"). Takie rozwiązanie przy okazji wymusza jednolity wygląd dokumentu poprzez ograniczenie dostępu do komend stylizujących docelowego systemu prezentacji.

## Komentarze do treści

Przewodnik ma przede wszystkim charakter informacyjny - ma przekazać najważniejsze informacje. Nie chcemy zanudzać czytelnika długimi wywodami, które też są obciążeniem dla nas, gdyż trzeba dbać o ich aktualność.

Znaczna część wiedzy olimpijskiej, którą posiadają uczniowie ze szkół olimpijskich, przekazywana jest im od starszych kolegów lub studentów, którzy prowadzą zajęcia w ich szkołach. Chodzi tu konkretnie o tę wiedzę *nietechniczną*, czyli np. strategie na zawody, syllabus itp. Uczniowie spoza takich wielkich ośrodków są z tego powodu już na start w gorszym położeniu tylko i wyłącznie ze względu na szkołę, do której uczęszczają, gdyż nawet jeśli takie informacje siedzą gdzieś w internecie, to i tak są one fragmentaryczne lub nawet sprzeczne ze sobą i zebranie całej treści, która znajduje się w tym przewodniku, byłoby bardzo trudne i czasochłonne - o wiele bardziej niż by to było opłacalne. Zebranie wszystkich tajników programowania sportowego w jedno miejsce pozwoli *wszystkim* zainteresowanym szybciej wdrażać się w jego świat.

Aby lepiej dotrzeć do czytelnika, staramy się pisać zadania w taki sposób, aby bezpośrednio zwracały się do niego. To, jakie emocje i myśli wzbudzimy w nim, jest o wiele ważniejsze niż gramatyka czy składnia. Wstęp oraz pierwsze trzy pytania muszą być szczególnie kontrolowane pod względem skuteczności przekazu (użytych słów, ich nacechowania, spójności zdań itd.) - bo są najważniejsze. Drugą rzeczą, która polepsza przekaz, są *przykłady*. Dobrze jest skupić się na konkretach, które pozwolą czytelnikowi zobaczyć coś na własne oczy, zamiast na abstrakcyjnych opisach.

Poniżej znajdują się komentarzę do poszczególnych pytań.

### "Na czym polega Olimpiada?"

Przykładowe zadanie zostało wybrane ze względu na następujące kryteria:
- **Pokazuje, jak wielkie oszczędności obliczeniowe można uzyskać dzięki algorytmice.** To jest właśnie jej kwintesencja. Wykładnicza a wielomianowa złożność to wielka przepaść, co zostało naświetlone w odpowiedzi na pytanie.
- Powyższy punkt oznacza też, że wybrane zadanie jest faktycznie zadaniem algorytmicznym, a nie matematycznym tak, jak się czasami zdarza na Olimpiadzie.
- Trudnością zadania nie jest samo wymyślenie jakiegokolwiek rozwiązania, a przyśpiesenie go. Algorytmy zachłanne często nie spełniają tego warunku. W wybranym zadaniu rozwiązanie brutalne jest bardzo łatwe do zrozumienia i samodzielnego wymyślenia: W każdym punkcie albo przykładamy wałek albo nie, co modelujemy za pomocą jednowymiarowej tablicy zer i jedynek.
- Rozwiązanie wzorcowe jest nieoczywiste, a mimo to proste do zrozumienia. Nie ma takich koncepcyjnych przeskoków, jakie by były, gdybyśmy mieli tłumaczyć np. drzewa przedziałowe. A pewne niewygodne szczegóły (algorytm na silnie spójne składowe) jesteśmy w stanie przemilczeć nieprzeszkadzając na zrozumieniu rozwiązania wzorcowego.
- Całość można zwięźle wytłumaczyć. Nie ma żadnej przypadkologii i nie ma długich rozważań.
- Nawiązuje do bardzo znanego problemu P=NP, co nie jest wymagane, ale jest mile widziane.

Najważniejszą częścią opisu tak naprawdę nie jest rozwiązanie wzorcowe, tylko treść zadania i rozwiązanie brutalne. Jeśli chcemy zainteresować czytelnika tą algorytmiką, to musi najpierw bardzo dobrze zrozumieć, jaki problem ona rozwiązuje.

W całym tekście musimy powstrzymywać się od używania znanego nam żargonu algorytmicznego i innych abstrakcyjnych sformułowań. O wiele bliższą codzienności i pobudzającą wyobraźnię zwykłego człowieka frazą jest "sieć połączeń" aniżeli "graf skierowany". Takie techniczne sformułowania zostawiamy na koniec bardziej jako dopisek na marginesie. Tak samo nie wprowadzamy abstrakcji tam, gdzie nie trzeba, i na literały formuły CNF mówimy po prostu "równania", bo akurat możemy.

Jeśli nazwiemy jakieś pojęcie lub obiekt konkretną nazwą, to musimy używać tylko i wyłącznie tej nazwy przez całe omówienie, żeby nie mieszać czytelnikowi w głowie. Ubogość języka w naszym przypadku tylko zwiększa jego ekspresywność.

### "Czy umiejętności algorytmiczne przydają się później w życiu?"

Przykłady użycia algorytmiki w pytaniu o przydatności umiejętności algorytmicznych powinny być rzeczami, z których czytelnik korzysta na co dzień. Powinny linkować do dokładnych wytłumaczeń tych algorytmów, nie tylko dla celów dydaktycznych, ale też żeby czytelnik zobaczył na własne oczy te algorytmy, których istnienie próbujemy mu sprzedać.

### "Jak wygląda drugi etap i finał…"

Opis tego, jak wygląda drugi i trzeci etap Olimpiady, nie ma charakteru informacyjnego, a bardziej przypomina opowieść kolegi. Chcemy w nim dokładnie zobrazować czytelnikowi, jak wyglądają dalsze etapy Olimpiady z perspektywy prawdziwego uczestnika. To jest też element "wprowadzania go w świat Olimpiady".

### "Jakie algorytmy i techniki muszę znać na…"

Lista wymaganych algorytmów i technik jest prawdopodobnie najbardziej kontrowersyjną i niedopracowaną częścią tego przewodnika. Każda lista tego typu wymaga podjęcia jakiś decyzji projektowych. Najbardziej kluczowe naszej listy są zawarte już w samym sformułowaniu pytania i w krótkim paragrafie znajdującym się pod nim. Choć tak, jak one są napisane w tekście, nie wyjaśnia za bardzo, *dlaczego* są takie, a nie inne. Czytelnikowi zostały przedstawione bardziej techniczne decyzje projektowe samej listy - coś w stylu specyfikacji, która pozwoli przyszłym odkrywcom listy ocenić, czym ta lista w ogóle i dlaczego mieliby jej zaufać, że wiarygodnie odpowiada na stawione pytanie i nie jest przysłowiowo wyciągnieta z czapy.

Przykładowo ograniczenie się tylko do *oficjalnych* omówień zapewnia, że lista nie jest subiektywnym wymysłem autora. Każdy bardzo dobrze wie, że istnieją zadania, które można rozwiązać albo standardowymi metodami, które jednak mogą wymagać od zawodnika trochę zastanowienia się, albo bezmyślnie jakimś niszowym chińskim trikiem z bloga na Codeforces. Pierwsza opcja nas zupełnie satysfakcjonuje, gdyż jest to lista *wymaganych* algorytmów, a nie *fajnych/przydatnych* algorytmów.

Ponadto oficjalne omówienia dają nam wgląd w to, co siedzi autorom zadań w głowach. Jeśli układając zadanie pomyśleli o tym, żeby to było zadanie na algorytm XYZ, to bardzo możliwe jest, że w przyszłości znowu wymyślą zadanie na algorytm XYZ. Może nawet już takie wymyślili i teraz czeka ono w shortliście.

Poniżej prezentujemy i tłumaczymy trzy największe wady naszej listy:

1. Wybór przedstawionych pojęć nie jest w 100% obiektywny. W liście OIJ świadomie pominęliśmy pojęcia poznanawane podczas nauki podstaw zwykłego programowania w C++, a w liście OI dodatkowo dobrze znane struktury z STLa i dobrze znaną matematykę ze szkoły średniej. W miejscach, gdzie mogliśmy, to decydowaliśmy się zapisać *problem*, który omówienie wymaga od nas, żebyśmy umieli rozwiązać, niż konkretny *algorytm*, który ten problem rozwiązuje. Przykład: "Najkrótsze ścieżki z jednego źródła" zamiast "Dijkstra". Uzasadnienie myślę, że jest akurat dość oczywiste; nie ma znaczenia czy do znalezienia wszystkich liczb pierwszych użyjesz sita Eratostenesa czy sita Eulera. Przykładem sytuacji, gdzie nie mogliśmy, jest zadanie *Kolekcjoner bajtemonów 2*, w którym analiza złożoności czasowej ściśle zależy od szczegołów algorytmu Euklidesa. Dokładną oczekiwaną złożoność algorytmu rozwiązującego dany problem ukryliśmy w zalinkowanym faktycznym algorytmie.

2. Podczas czytania wszystkich omówień niewątpliwie coś mogło umsknąć naszej uwadze. Niektóre algorytmy jak na przykład DFS są na tyle fundamentalne, że omówienia często nie dość, że nie wspominają o nich, to w miejscach, gdzie oczekuje się ich użycia, piszą o nich nie w sposób imperatywny: "Przeszukujemy drzewo…", a jedynie w sposób deklaratywny: "…korzystając z głebokości wierzchołków…".

3. Kolejny aspekt, który wymagał pewnego stopnia subiektywnej opinii było stwierdzenie, czy dane omówienie zakłada użycie pewnego algorytmu. W przypadkach, gdy omówienie przedstawiało wiele rozwiązań wzorcowych, staraliśmy oprzeć się na tym, które jest prostsze - to znaczy wymaga mniej sztuczek albo wymaga algorytmów, które są bardziej elementarne. Przykładowo z omówienia zadania *Ciąg binarny* wybraliśmy rozwiązanie oparte na trwałym drzewie przedziałowym i odrzuciliśmy te oparte na Wavelet Tree, gdyż… no cóż - Wavelet Tree to nisza, a ogólna technika utrwalania przydaje się - jeśli nie "wszędzie" - to "wszędziej" niż Wavelet Tree. Czasami omówienia opisują istniejący algorytm udając, że jest to coś nowego. Przykład: DFT w zadaniu *Wielomian*. Czasami w ten sposób opisują coś, co w czasie ich powstania jeszcze nie miało nazwy. Przykład: drzewa wirtualne w zadaniu *Kolacje*.

Szczególnie kontrowersyjnym elementem listy okazał się podział czy też posortowanie algorytmów według "przydatności" - a raczej jego brak. Powód takiej decyzji jest zgodny z ogólną filozofią, jaką przyjęliśmy w tworzeniu tej listy - **czyli ograniczeniem czysto subiektownych decyzji**. "Przydatność" algorytmu jest *bardzo* subiektywną metryką:

Pierwszą lepszą definicją "przydatności" algorytmu jest liczba zadań, w których się pojawił. No i tuż już od razu dochodzimy do rozdroża, bo co z zadaniami z finałów? Czy je też powinniśmy wliczać do tej metryki? Na finałach w ostatnich latach zwykle pojawia się znacznie więcej algorytmów niż na drugim etapie. Dla kogoś, kto celuje tylko w przejście drugiego etapu, takie algorytmy z finału są zupełnie nieprzydatne. A dla kogoś, kto celuje w wygranie OI, znajomość takich algorytmów może być kluczowa. Nieważne, którą opcję byś wybrał, i tak jedna z tych dwóch osób by tylko straciła na twojej decyzji.

Kolejnym pytaniem, na które musielibyśmy odpowiedzieć w definicji "przydatności", jest to, czy odsuwamy na bok algorytmy, które nie pojawiły się w ostatnich kilku latach - bo bardziej spostrzegawczy zawodnicy wiedzą, że w tych ostatnich kilku latach (mniej więcej od czasów pandemii koronawirusa) zadania OI zaczęły się robić bardziej ad-hocowe z mniejszym naciskiem na wiedzę algorytmiczną. To oczywiście oznacza, że ta wiedza jest mniej przydatna na Olimpiadzie.

A czemu na przykład wyraźnym przeskokiem w "przydatności" algorytmu nie miałoby być to, czy pojawił się co najnmiej dwa razy, czy tylko raz? Przecież raz to mógł być przypadek, a dwa razy - świadoma decyzja, i wtedy uczestnik mógłby podczas nauki odrzucać takie nieprzydatne jednorazowe algorytmy i uczyć się wszystkich co najmniej dwurazowych.

**Zamiast podejmować te wszystkie decyzje za czytelnika, wolimy przedstawić mu nasze rady i dostarczyć mu jak najwięcej informacji, aby sam mógł podjąć odpowiednią dla siebie decyzję.**

Jako notatkę dla przyszłych analizujących omówienia zostawiamy poniższą listę pojęć, na które warto uważać czytając omówienia: [Scalanie do podwyniku z największego poddrzewa](https://usaco.guide/adv/comb-sub?lang=cpp), Arytmetyka modularna (bardziej dla OIJ), Dziel i zwyciężaj, Funkcja low, Kolejka monotoniczna, Najkrótsze ścieżki pomiędzy każdą parą, Najkrótsze ścieżki z jednego źródła z ujemnymi wagami krawędzi, Mosty i punkty artykulacji, Normalizacja wektorów o współrzędnych całkowitych, Odwrotność modularna, Przekorzenianie w programowaniu dynamicznym na drzewie, Rozkład grafu funkcyjnego, Stars and bars, Średnica drzewa, Wzór Stirlinga. Dodatkowa lista, którą można się zainspirować, znajduje się [w biblioteczce digitcrushera](https://github.com/digitcrusher/algorytmy#algorytmy).

### TODO

Pomysły na przyszłe odpowiedzi na pytania:
- "Jak testować interaktywy?"
- "Jak wygrać OI/OIJ?"
- "Jak dużo czasu muszę poświecić żeby zdobyć tytuł finalisty OI lub OIJ?"
- "Jaki rating na Codeforces muszę wbić żeby mieć dany etap OI lub OIJ w kieszeni?"
- "Jakie ratingi zadań/litery na konteście na Codeforces odpowiadają poszczególnym etapom OI i OIJ?"
- "Które etapy OI odpowiadają którym etapom OIJ pod względem trudności?"
- coś o (braku) przydatności Pythona na OI
- "Przez co muszę przejść żeby dostać się na IOI lub EJOI?"

## Praca z wyglądem

Typst jest najlepszym systemem składu ze wszystkich, które targetujemy, więc najpierw tam powinny być rozwijane wszystkie zmiany w wyglądzie.

Przestrzenią kolorów, w której pracujemy, jest Oklab w cylindrycznym układzie współrzędnych (Oklch). Nie używaj innych przestrzeni, bo kolor będzie odstawać od reszty, i pod żadnym pozorem nie używaj sRGB ani innych percepcyjnie niejednorodnych przestrzeni, bo wtedy pójdziesz do piekła.

Zestaw ikon, który używamy to Google Material Symbols ([wyszukiwarka](https://fonts.google.com/icons)). W repozytorium jest już pobrana jedna wersja tej czcionki, więc jeśli ikonka na stronie wygląda inaczej niż w zbuildowanym PDF-ie, to oznacza, że pewnie trzeba zaktualizować czcionkę w repozytorium. W HTML-u nowe ikony trzeba dodawać do `@import`-a importującego tę czcionkę.

## Praca z szablonami

Szablony są napisane w języku Jinja ([dokumentacja](https://jinja.palletsprojects.com/en/stable/templates/)) i żyją sobie w folderze `templates/`. Dla nas to produkt końcowy. Po nas pałeczkę przejmuje odpowiedni interpreter danej formy prezentacji. Szablony przyjmują tekst źródłowy zpreprocesowany przez `process_source` w `build.py`, strukturę którego opisuje `preprocessed_source.rnc`. Korzeń dokumentu przekazywany jest w zmiennej globalnej `document`. `problems.csv` - jako słownik wierszy po polu `id` w zmiennej globalnej `problems`. Wszystkie zmienne globalne i filtry są wylistowane w `render` w `build.py`. Powodzenia!
