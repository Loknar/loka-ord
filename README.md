# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir þeirra og fleira, undir frjálsu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur eftirfarandi fjölda orða:

|   | ób.l | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Nafnorð**     |   | 242 | 287 | 206 | 735 | 128 | 151 | 164 | 443 | **1178** |
| **Lýsingarorð** | 11 |   |   |   | 75 |   |   |   | 61 | **136** |
| **Sagnorð**     |   |   |   |   | 149 |   |   |   | 44 | **193** |
| **Töluorð**     |   |   |   |   | 69 |   |   |   | 10 | **79** |
| **Fornöfn**     |   |   |   |   | 40 |   |   |   | 2 | **42** |
| **Smáorð**      |   |   |   |   |   |   |   |   |   | **188** |
| **Alls** |   |   |   |   | **1239** |   |   |   | **578** | **1817** |

| Sérnöfn | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Eiginnöfn | 107 | 120 |   | 227 | 26 | 140 |   | 166 | **393** |
| Gælunöfn  | 6 | 4 |   | 10 | 1 |  |   | 1 | **11** |
| Kenninöfn |  |  |   |  | 8 | 9 |   | 17 | **17** |
| Miłlinöfn |   |   |   |   |   |   |   |   | **11** |
| Örnefni   |  | 2 | 2 | 4 | 23 | 16 | 11 | 50 | **54** |
| **Alls**  |   |   |   | **252** |   |   |   | **234** | **486** |

**Samtals:** 2303 orð.

56 skammstafanir.

## Forkröfur (Requirements)

`Python3.10` eða nýrra, `pip` og pakkar listaðir í `requirements.txt`, sækir og setur upp pakka með

```bash
pip install -Ur requirements.txt
```

## Notkun (Usage)

```bash
python main.py --help
```

Smíða gagnagrunn:

```bash
python main.py build-db
```

Skrifa orð úr grunni í textaskrár:

```bash
python main.py write-files
```

Bæta við orði í gegnum skipanalínu (CLI):

```bash
python main.py add-word
```

### Orðaviðbætur

Fyrir lesendur sem hafa áhuga á að leggja til orð sem þykja vanta í grunninn þá er ofangreind `add-word` skipun til einhvers brúks en því miður er virknin til að bæta við orðum í gegnum skipanalínuna enn sem komið er mjög takmörkuð, og sé vilji til að bæta við mismunandi týpum sagnorða, samsettum orðum og fleira er eina leiðin enn sem komið er að kynna sér strúktúr JSON skráa fyrir sambærileg orð og handvirkt afrita viðeigandi skrá í nýja, breyta innihaldi hennar og keyra svo

```bash
python main.py build-db -ch write-files -tr
```

eða

```bash
python main.py build-db -r write-files
```

til að smíða/endursmíða gagnagrunninn með viðbættu orðunum og færa síðan innihald gagnagrunnsins aftur í textaskrár.

Athugið að þegar verið er að henda saman JSON skrá fyrir samsett orð þá þarf ekki að græja beygingarmyndir þar sem þær eru leiddar út frá upplýsingunum í `"samsett"` listanum. **Dæmi:** þegar ég bætti við orðinu "hóflegur" var nóg að sjá til þess að ałlir orðhlutar orðsins væru til staðar og útbúa síðan svoútlítandi skrá og vista sem `lysingarord/hóflegur.json`:

```json
{
	"orð": "hóflegur",
	"flokkur": "lýsingarorð",
	"samsett": [
		{
			"mynd": "hóf",
			"samsetning": "stofn",
			"kennistrengur": "no-hóf-hk"
		},
		{
			"kennistrengur": "lo-legur-ó"
		}
	],
	"kennistrengur": "lo-hóflegur"
}
```

svo þegar búið var að smíða grunninn og skrifa út JSON skrár úr grunninum þá bættust beygingarmyndirnar við út frá upplýsingunum í `"samsett"` listanum.

### Orðaleit

Til að athuga hvort orð sé til staðar í grunni er hægt að gera uppflettingu í smíðuðum gagnagrunni með tólum að eigin vali, leita að JSON skrá með nafni sem inniheldur umrætt orð, eða með því að smíða sjón fyrir sjáanda (e. sight for seer):

```bash
python main.py build-sight
```

ofangreind skipun býr til forsmíðaða orðauppflettingu útfrá orðagögnum í JSON skrám og vistar í `lokaord/database/data/disk/lokaord/sight.pointless` (eða `lokaord/database/data/disk/lokaord/sight.pickle` á windows), þessa forsmíðuðu leit þarf að endursmíða þegar JSON skrárn hafa breyst, en er svo hægt að nota fyrir uppflettingu á stökum orðum:

```bash
python main.py search "orð"
```

eða fyrir heilu setningarnar:

```bash
python main.py scan-sentence "Hér er haugur orða í hóflega langri setningu."
```

einnig er stytt nafn `ss` fyrir þessa skipun, þ.e. `python main.py ss "Hér er setning."`.

### Þægilegri keyrsluskipun

Til þæginda er hægt á linux/unix að skilgreina alias eins og til dæmis

```bash
alias lokaord="$HOME/repos/loka-ord/bin/lokaord"
```

og vista í `.bashrc` eða sambærilegri skrá, þá er hægt að spara sér að þurfa að skrifa endalaust `python main.py` og skrifa í staðinn einfaldlega `lokaord`. Fyrir Windows þyrfti að skrifa `.bat` skrá sambærilega bash `bin/lokaord` skriptunni og síðan bæta henni í path eða útbúa sambærilegt alias á Windows.

### Smíða allt uppá nýtt eða einungis breytingar

Eftirfarandi skipun endursmíðar gagnagrunn, skrifar út í skrár, byggir sjón og prentar út tölulegar upplýsingar í formi markdown töflu eins og þeirrar sem sýnd er ofar í þessari textaskrá.

```bash
lokaord build-db -r write-files build-sight md-stats
```

Hér er svo skipun til að færa einungis gögn úr breyttum skrám í grunn og skrifa svo aftur í skrár breytt orð (notar git, og svo `Edited` tímaskráningu á orðum sem er uppfærð þegar orð í grunni breytast)

```bash
lokaord build-db -ch write-files -ts "2023-04-20T22:30" build-sight md-stats
```

þar sem tímapunkturinn `"2023-04-20T22:30"` tilgreinir hve gamlar breytingar á orðum eigi að skrifa úr grunni í orð (til þæginda stendur flaggið `-to` og gildin `"last2min"`, `"last10min"` og `"last30min"` einnig til boða, sem og flaggið `-tr` fyrir núverandi keyrslu).

## Frávik frá hefðbundinni íslensku (Deviances from traditional icelandic)

Í grunninum eru frávik frá hefðbundinni íslensku þegar kemur að skrift orða sem innihalda tvöfalt L. Þá eru þau "tvöfalt-L" orð sem borin eru fram með svoköłluðu klikk-hljóði skrifuð með "łl" í stað "ll", þ.e. fyrra ełlið er hið pólska Ł. Þetta frávik er innleitt með það í huga að geta greint á miłli orða eins og "galli" (samfestingur eða flík) og "gałli" (vankantur eða brestur).

Tungumál breytast og þróast. Samhliða því að leggja áherslu á að vanda okkur við notkun tungumáls okkar verðum við að vera opin fyrir breytingum sem bæta það eða leysa vandamál við notkun þess.

Ég tel að geta til að greina á miłli "tvöfalt-L" orða sem borin eru fram með klikk-hljóði og annarra sé mjög nytsamleg og jafnvel nauðsynleg þegar kemur að orðhugbúnaðartæknivæðingu. Slík geta (útfrá orðinu stöku, þ.e. þurfa ekki að leiða það út frá textasamhengi) mundi auðvelda til muna smíði talgervils og málgreinis.

## Orðframlög (Contributing)

**Til ykkar sem hafið hug á að leggja til orð í grunninn!**

Mikilvægt er við framlag orða að ekki sé um afritun úr öðrum orðagrunnum að ræða er heyra undir útgáfuskilmála sem þykja ósamrýmanlegir almenningseignarleyfi þessa verkefnis.

Orðagjöfum ber að tryggja að orð sem lögð eru til verkefnisins séu þeim frjálst að gefa, þá er öruggast að orðin komi beint úr höfðum þeirra sem reiða þau fram.

Orð sem bætt er í grunninn heyra undir almenningseignarleyfi verkefnisins og verða því almenningseign.

## Viðhaldari (Maintainer)

Hæ, og takk ef þú last svona langt. Ég hef lagt grunn að **lokaorð** orðagrunninum og gef hann hér út undir LGPLv3 leyfi. Leyfið vel ég vegna þess að ég vil að hverjum og einum sé frjálst að smíða og nota grunninn á hvern þann hátt sem viðkomandi þóknast. En samhliða óska ég þess að hverjar þær breytingar á virkni, gögnum eða gagnastrúktúr orðagrunnsins séu gefnar út undir sama LGPLv3 leyfi, svo að viðbætur eða breytingar eins notanda geti gagnast öðrum notendum sem grunninn nota.

[@Loknar](https://github.com/Loknar)
