# Repozytorium przewodnika OOOZ

Najnowszy build przewodnika można znaleźć na kanale `#przewodnik` na [naszym serwerze Discord](https://discord.gg/AMGxG4TvDS).

## Buildowanie

1. Zainstaluj programy Git LFS, Python 3 oraz [Typst](https://typst.app/open-source/#download).
2. Zainstaluj potrzebne pakiety w Pythonie za pomocą `pip3 install -r requirements.txt`.
3. Uruchom `./build.py --watch`. Od teraz przewodnik będzie buildowany po każdej zmianie w plikach źródłowych. Jeśli chcesz tylko jednorazowo zbuildować przewodnik, to usuń opcję `--watch`.

## Praca z treścią

> [!WARNING]
> Z każdą nową edycja przewodnika trzeba zaktualizować daty i linki w pytaniu "Jakie korzyści przynosi sukces w...", "Jak wystartować w…" i "Jak wygląda drugi i trzeci etap…".

Ze względu na to, iż przewodnik jest wydawany w dwóch zupełnie niepodobnych formach prezentacji (Discordowy Markdown i Typst), zastosowany został bardzo wyraźny podział na warstwę semantyczną i warstwę prezentacji dokumentu. Całość tej pierwszej znajduje się w pliku `source.xml` i, jak można się domyśleć, jest ona napisana w XML-u - języku spokrewnionym z HTML-em, ale mniej odjechanym. Sam XML oczywiście nie definiuje, jakie są typy znaczników; to robi użytkownik, czyli w tym przypadku my. Znaczniki dostępne w `source.xml` zostały opisane poniżej.

Kontynuując temat warstwy "semantycznej": Znaczniki, które tłumaczą się na pogrubiony tekst lub kursywę, nie przyjmują nazwy od ich wyglądu (np. "bold" czy "italic"), tylko od funkcji, jaką one pełnią w tekście (np. "important" lub "emphasis"). Takie rozwiązanie przy okazji wymusza jednolity wygląd dokumentu poprzez ograniczenie dostępu do komend stylizujących docelowego systemu prezentacji.

Istnieją dwa różne "konteksty" tekstu, w których mogą występować znaczniki: "inline" (czyli elementy wewnątrz paragrafu) oraz "block" (elementy, które zajmują całą szerokość strony, wizualnie tworząc blok).

|    Znacznik     | Może być w inline? | Może być w block? | Jaki kontekst wprowadza? |
| --------------- | :----------------: | :---------------: | :----------------------: |
| `code`          |         ✅         |         ✅        |  *Nie wprowadza tekstu*  |
| `emphasis`      |         ✅         |         ❌        |          Inline          |
| `important`     |         ✅         |         ❌        |          Inline          |
| `item` w `list` |  *Tylko w `list`*  |  *Tylko w `list`* |          Block           |
| `link`          |         ✅         |         ❌        |          Inline          |
| `list`          |         ❌         |         ✅        |  *Zawiera tylko `item`*  |
| `note`          |         ❌         |         ✅        |          Block           |
| `placeholder`   |         ✅         |         ❌        |   *Nie wprowadza nic*    |
| `ref`           |         ✅         |         ❌        |          Inline          |
| `todo`          |         ❌         |         ✅        |          Block           |
| `warning`       |         ❌         |         ✅        |          Block           |

Poniżej jest warstwa semantyczna przykładowego dokumentu prezentująca wszystkie dostępne znaczniki w `source.xml`. Wartości atrybutów oczywiście nie są poprawnie sformatowane i tylko opisują, co w nich *miałoby* się znaleźć.

```xml
<?xml version='1.0' encoding='UTF-8'?>
<document
  title='Tytuł dokumentu'
  version='(opcjonalnie) Data wydania dokumentu w formacie YYYY-MM-DD'>

  <preface>
    Wstęp dokumentu.
    <discord-only>Tekst widoczny tylko na Discordzie.</discord-only>
    <download-only>Tekst widoczny tylko w wydaniu pobieranym.</download-only>
  </preface>

  <!-- Pytania są dzielone na dwie kategorie: "ważne" i mniej ważne. -->
  <answer question='Treść pytania?' id='jakies-pytanie' important='yes'>
    <todo>
      Notatka autorów dokumentu dla nich samych, co trzeba dopisać, zmienić,
      poprawić...
    </todo>

    Przykładowe zdanie z <important>ważną informacją</important>, <code>kodem
    </code>, <emphasis>wymawianym naciskiem na słowo lub krótką frazę</emphasis>
    oraz <link url='https://example.com'>linkiem</link>.

    Kolejne paragrafy są oddzielane od siebie dwoma znakami nowej linii.
    Paragrafy mogą być rozbite na kilka kolejnych linii.
    Znaczniki, które mogą występować tylko w kontekście block, nie muszą być
    oddzielane dwoma znakami nowej linii od paragrafów.
    <note>
      Informacja, która niekoniecznie jest <emphasis>ważna</emphasis>, ale którą
      warto zapamiętać.
    </note>
    <warning>
      Ostrzeżenie.
    </warning>
    Blok kodu:

    <code lang='bash'>
      echo Musisz oddzielić go dwoma nowymi liniami od okalających paragrafów, \
           gdyż może również występować w kontekście inline tak, jak to \
           zostało zaprezentowane wyżej. Dostępne języki to bash i cpp.
    </code>

    Tekst po bloku kodu.
    <list>
      <item>Podpunkt listy.</item>
      <item>
        Elementy listy wprowadzają kontekst block, więc można mieć nawet i podlisty:
        <list>
          <item>Podpodpunkt 1</item>
          <item>Podpodpunkt 2</item>
        </list>
      </item>
    </list>
  </answer>

  <answer
    question='O co pytać na…'
    id='Do pytań można dodawać ID, do którego można później się odnosić za
        pomocą <ref>.'>

    Na początku pytania z podpytaniami może być tekst. <ref
    id='jakies-pytanie'>O! Link do pytania!</ref>
    <subanswer subquestion='…SIO2?'>
      ...
    </subanswer>
    <subanswer subquestion='…Discordzie?'>
      ...
    </subanswer>
  </answer>

  <footer>
    Stopka dokumentu. W wydaniu pobieranym faktycznie jest na dole dokumentu,
    a na Discordzie jest wsadzana do opisu kanału. Znacznik <placeholder
    for='contributors'/> zostanie podczas renderowania zastąpiony listą
    contributorów pooddzielaną przecinkami. Na Discordzie będą wzmianki
    użytkowników, a w wydaniu pobieranym będą ich nazwy z opcjonalnym linkiem do
    ich strony.
  </footer>

  <contributor
    name='Imię "Pseudonim" Nazwisko'
    discord-id='Jego ID użytkownika na Discordzie'
    website='(opcjonalnie) Link do jego strony internetowej'
    contribution='Krótki opis jego wkładu w powstanie przewodnika'/>
</document>
```

## Komentarze do treści

Przewodnik ma przede wszystkim charakter informacyjny - ma przekazać najważniejsze informacje. Nie chcemy zanudzać czytelnika długimi wywodami, które też są obciążeniem dla nas, gdyż trzeba dbać o ich aktualność.

Znaczna część wiedzy olimpijskiej, którą posiadają uczniowie ze szkół olimpijskich, przekazywana jest im od starszych kolegów lub studentów, którzy prowadzą zajęcia w ich szkołach. Chodzi tu konkretnie o tę wiedzę *nietechniczną*, czyli np. strategie na zawody, syllabus itp. Uczniowie spoza takich wielkich ośrodków są z tego powodu już na start w gorszym położeniu tylko i wyłącznie ze względu na szkołę, do której uczęszczają, gdyż nawet jeśli takie informacje siedzą gdzieś w internecie, to i tak są one fragmentaryczne lub nawet sprzeczne ze sobą i zebranie całej treści, która znajduje się w tym przewodniku, byłoby bardzo trudne i czasochłonne - o wiele bardziej niż by to było opłacalne. Zebranie wszystkich tajników programowania sportowego w jedno miejsce pozwoli *wszystkim* zainteresowanym szybciej wdrażać się w jego świat.

Aby lepiej dotrzeć do czytelnika, staramy się pisać zadania w taki sposób, aby bezpośrednio zwracały się do niego. To, jakie emocje i myśli wzbudzimy w nim, jest o wiele ważniejsze niż gramatyka czy składnia. Wstęp oraz pierwsze trzy pytania muszą być szczególnie kontrolowane pod względem skuteczności przekazu (użytych słów, ich nacechowania, spójności zdań itd.) - bo są najważniejsze. Drugą rzeczą, która polepsza przekaz, są *przykłady*. Dobrze jest skupić się na konkretach, które pozwolą czytelnikowi zobaczyć coś na własne oczy, zamiast na abstrakcyjnych opisach.

---

Przykłady użycia algorytmiki w pytaniu o przydatności umiejętności algorytmicznych powinny być rzeczami, z których czytelnik korzysta na co dzień. Powinny linkować do dokładnych wytłumaczeń tych algorytmów, nie tylko dla celów dydaktycznych, ale też żeby czytelnik zobaczył na własne oczy te algorytmy, których istnienie próbujemy mu sprzedać.

---

Opis tego, jak wygląda drugi i trzeci etap Olimpiady, nie ma charakteru informacyjnego, a bardziej przypomina opowieść kolegi. Chcemy w nim dokładnie zobrazować czytelnikowi, jak wyglądają dalsze etapy Olimpiady z perspektywy prawdziwego uczestnika. To jest też element "wprowadzania go w świat Olimpiady".

---

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

Jako notatkę dla przyszłych analizujących omówienia zostawiamy poniższą listę pojęć, na które warto uważać czytając omówienia: Arytmetyka modularna (bardziej dla OIJ), Dziel i zwyciężaj, Funkcja low, Kolejka monotoniczna, Najkrótsze ścieżki pomiędzy każdą parą, Najkrótsze ścieżki z jednego źródła z ujemnymi wagami krawędzi, Mosty i punkty artykulacji, Normalizacja wektorów o współrzędnych całkowitych, Odwrotność modularna, Przekorzenianie w programowaniu dynamicznym na drzewie, Rozkład grafu funkcyjnego, Stars and bars, Średnica drzewa, Wzór Stirlinga. Dodatkowa lista, którą można się zainspirować, znajduje się [w biblioteczce digitcrushera](https://github.com/digitcrusher/algorytmy#algorytmy).

---

Pomysły na przyszłe odpowiedzi na pytania:
- coś o tym, że dziewczyny też biorą udział w Olimpiadzie
- "Jak wygrać OI/OIJ?"
- "Jak dużo czasu muszę poświecić żeby zdobyć tytuł finalisty OI lub OIJ?"
- "Jaki rating na Codeforces muszę wbić żeby mieć dany etap OI lub OIJ w kieszeni?"
- "Jakie ratingi zadań/litery na konteście na Codeforces odpowiadają poszczególnym etapom OI i OIJ?"
- "Które etapy OI odpowiadają którym etapom OIJ pod względem trudności?"
- coś o (braku) przydatności Pythona na OI
- "Przez co muszę przejść żeby dostać się na IOI lub EJOI?"

## Praca z wyglądem

Przestrzenią kolorów, w której pracujemy, jest Oklab w cylindrycznym układzie współrzędnych (Oklch). Pod żadnym pozorem nie używaj sRGB ani innych percepcyjnie niejednorodnych przestrzeni.

Zestaw ikon, który używamy to Google Material Symbols. Ich wyszukiwarkę znajdziesz [tutaj](https://fonts.google.com/icons). W repozytorium jest ustalona wersja tej czcionki, więc jeśli ikonka na stronie wygląda inaczej w zbuildowanym dokumencie, to oznacza, że pewnie trzeba zaktualizować czcionkę w repozytorium.
