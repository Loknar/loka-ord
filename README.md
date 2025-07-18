# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir og samsetningu þeirra og fleira, undir frjálsu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur eftirfarandi fjölda orða:

|   | ó.l | kk | kvk | hk | kjarna orð | kk | kvk | hk | samsett orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Nafnorð**     |   | 1613 | 1533 | 1353 | 4499 | 9146 | 11702 | 9639 | 30487 | **34986** |
| **Lýsingarorð** | 348 |   |   |   | 694 |   |   |   | 3858 | **4552** |
| **Sagnorð**     |   |   |   |   | 1215 |   |   |   | 1329 | **2544** |
| **Töluorð**     |   |   |   |   | 62 |   |   |   | 29 | **91** |
| **Fornöfn**     |   |   |   |   | 39 |   |   |   | 15 | **54** |
| **Smáorð**      |   |   |   |   | 329 |   |   |   | 468 | **797** |
| **Alls** |   |   |   |   | **6839** |   |   |   | **36186** | **43025** |

| Sérnöfn | kk | kvk | hk | kjarna orð | kk | kvk | hk | samsett orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Eiginnöfn | 1303 | 1264 | 13 | 2580 | 983 | 1262 | 7 | 2252 | **4832** |
| Kenninöfn |  |  |  |  | 4744 | 4742 | 4718 | 14204 | **14204** |
| Miłlinöfn |   |   |   |   |   |   |   |   | **752** |
| Gælunöfn  | 182 | 78 | 1 | 261 | 117 | 129 | 4 | 250 | **511** |
| Örnefni   | 26 | 119 | 126 | 271 | 1585 | 1147 | 1196 | 3928 | **4199** |
| **Alls**  |   |   |   | **3710** |   |   |   | **20788** | **24498** |

**Samtals:** 67523 orð.

442 skammstafanir.

## Forkröfur (Requirements)

`Python3.10` eða nýrra, `pip` og [PyPI](https://pypi.org/) pakkar listaðir í skránni `requirements.txt`.

Þurfirðu eða viljirðu setja upp Python virtualenv í stað þess að nota system python (t.d. ef system python er stillt sem `externally-managed-environment`) þá geturðu útbúið sýndarumhverfi (e. virtual environment):

```bash
python -m venv env
```

þar sem `env` er nafnið á sýndarumhverfinu sem búið er til, samnefnd mappa verður til, þú virkjar það í núverandi skipanalínu með

```bash
source env/bin/activate
```

getur afvirkjað sýndarumhverfið með skipuninni `deactivate`. Athugaðu að sýndarumhverfið er ekki sjálfkrafa virkjað þegar þú opnar nýja skipanalínu, þú þarft að velja/virkja það með `source env/bin/activate`.

Þú sækir og setur upp nauðsynlega pakka með

```bash
pip install -Ur requirements.txt
```

## Notkun (Usage)

```bash
python main.py --help
```

Í upphafi eru orðagögnin einungis í formi textaskráa, stofna þarf SQLite gagnagrunn og lesa öłl orðin inn í hann, og svo er einnig hægt að smíða orðaforleit. Þetta má gera með skipuninni:

```bash
python main.py init
```

Ofangreind skipun jafngildir `python main.py build-db write-files build-sight md-stats`, eða eftirfarandi röð skipana:

```bash
# smíða grunn
python main.py build-db
# skrifa orð úr grunni í textaskrár
python main.py write-files
# smíða orðaforleit
python main.py build-sight
# prenta út töluleg gögn á markdown sniði
python main.py md-stats
```

Ber að nefna að við núverandi útfærslu og fjölda orða (kringum 5600 orð) þá tekur `init` ferlið sinn tíma. Tölva með temmilega góðan vélbúnað og linux stýrikerfi klárar það á tæpum þremur mínútum, meðalgóð fartölva með linux þarf kringum sjö mínútur, þá hefur sýnt sig að á tölvum keyrandi windows stýrikerfi sé ferlið umtalsvert lengra, geti jafnvel tekið yfir hálftíma (skrifast líklega að mestu á mismunandi meðhöndlun fyrir transactions í SQLite miłli windows og linux).

**TODO: laga þessa virkni, er brotin eins og er** Bæta við orði í gegnum skipanalínu (CLI):

```bash
python main.py add-word
```

### Orðaviðbætur

Fyrir lesendur sem hafa áhuga á að leggja til orð sem þykja vanta í grunninn þá er ofangreind `add-word` skipun til einhvers brúks en því miður er virknin til að bæta við orðum í gegnum skipanalínuna enn sem komið er mjög takmörkuð, og sé vilji til að bæta við mismunandi týpum sagnorða, samsettum orðum og fleira er eina leiðin enn sem komið er að kynna sér strúktúr JSON skráa fyrir sambærileg orð og handvirkt afrita viðeigandi skrá í nýja, breyta innihaldi hennar og keyra svo

```bash
python main.py update
```

sem jafngildir skipuninni `python main.py build-db -ch write-files -tr build-sight md-stats`.

Hægt er að endursmíða gagnagrunn með

```bash
python main.py init -r
```

sem jafngildir

```bash
python main.py build-db -r write-files build-sight md-stats
```

`init` með flaggið `-r` eyðir núverandi gagnagrunni og smíðar síðan nýjan útfrá orðaskrám.

Athugið að þegar sett er saman JSON skrá fyrir samsett orð þá þarf ekki að ganga frá beygingarmyndum þar sem þær eru leiddar út frá upplýsingunum í `"samsett"` listanum. **Dæmi:** þegar bætt var við orðinu "hóflegur" var nóg að sjá til þess að ałlir orðhlutar orðsins væru til staðar og útbúa síðan svoútlítandi skrá og vista sem `lysingarord/hóflegur.json`:

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
	"kennistrengur": "lo-hóflegur",
	"hash": "tba"
}
```

svo þegar keyrt var `update` þá bættust beygingarmyndirnar við út frá `"samsett"` upplýsingalistanum.

Gildið í `"hash"` á að vera strengur sem er ekki tómur, gildið er sett sem sextándakerfis hakkagildi sem endurspeglar gögn orðsins þegar `update` og/eða `write-files` er keyrt, svo að fyrir sömu gögn er hakkagildið það sama, og þegar gögn breytast þá breytist hakkagildið (sjá `Ord.get_data_hash` í `handlers.py`).

Athugið að kröfur til skráarnafna eru mismunandi miłli orðflokka, til dæmis þurfa nafnorð að hafa kyn orðsins í skráarnafni, þá eru "ósjálfstæð" orð (notað fyrir orðhluta sem ekki eru látnir standa einir) með `-ó` í skráarnafni, og þau orð sem eru sérstaklega aðgreind með "merkingu" innihalda merkinguna í skráarnafni á sniðinu `-_merking_` (sjá t.d. skrána `mæla-_segja_.json`).

### Orðaleit

Til að athuga hvort orð sé til staðar í grunni er hægt að gera uppflettingu í smíðuðum gagnagrunni með tólum að eigin vali, leita að JSON skrá með nafni sem inniheldur umrætt orð, eða með því að smíða sjón fyrir sjáanda (e. sight for seer):

```bash
python main.py build-sight
```

ofangreind skipun býr til forsmíðaða orðauppflettingu útfrá orðagögnum í JSON skrám og vistar í `lokaord/database/data/disk/lokaord/sight.pointless` (eða `lokaord/database/data/disk/lokaord/sight.pickle` á windows), þessa forsmíðuðu leit þarf að endursmíða þegar JSON skrár hafa breyst, en er svo hægt að nota fyrir uppflettingu á stökum orðum:

```bash
python main.py search "orð"
```

eða fyrir heilu setningarnar:

```bash
python main.py scan-sentence "Hér er haugur orða í hóflega langri setningu."
```

einnig er stytt nafn `ss` fyrir þessa skipun, þ.e. `python main.py ss "Hér er setning."`. Síðan er einnig hægt að láta lesa texta úr textaskrá:

```bash
python main.py ss -i input.txt
```

### Þægilegri keyrsluskipun

Til þæginda er hægt á linux/unix að skilgreina alias eins og til dæmis

```bash
alias lokaord="$HOME/repos/loka-ord/bin/lokaord"
```

og vista í `.bashrc` eða sambærilegri skrá, þá er hægt að spara sér að þurfa að skrifa endalaust `python main.py` og skrifa í staðinn einfaldlega `lokaord`. Fyrir Windows er hægt að notast við `.bat` skrána á sambærilegan hátt og `bin/lokaord` skriptuna, þ.e. bæta henni í path eða útbúa sambærilegt alias á Windows.

### Smíða allt uppá nýtt eða einungis breytingar

Eftirfarandi skipun endursmíðar gagnagrunn, skrifar út í skrár, byggir sjón og prentar út tölulegar upplýsingar í formi markdown töflu eins og þeirrar sem sýnd er ofar í þessari textaskrá.

```bash
lokaord build-db -r write-files build-sight md-stats
```

Hér er svo skipun til að færa einungis gögn úr breyttum skrám í grunn og skrifa svo aftur í skrár breytt orð (notar git, og svo `Edited` tímaskráningu á orðum sem er uppfærð þegar orð í grunni breytast)

```bash
lokaord build-db -ch write-files -ts "2023-04-20T22:30" build-sight md-stats
```

þar sem tímapunkturinn `"2023-04-20T22:30"` tilgreinir hve gamlar breytingar á orðum eigi að skrifa úr grunni í orð (til þæginda stendur flaggið `-to` og gildin `"last2min"`, `"last10min"` og `"last30min"` einnig til boða, sem og flaggið `-tr` fyrir tímapunkt upphafs núverandi keyrslu).

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
