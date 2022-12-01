# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir þeirra og fleira, undir frjálsu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur eftirfarandi fjölda orða:

|   | ób.l | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Nafnorð**     |   | 99 | 86 | 82 | 267 | 20 | 12 | 10 | 42 | **309** |
| **Lýsingarorð** | 6 |   |   |   | 11 |   |   |   | 11 | **22** |
| **Sagnorð**     |   |   |   |   | 12 |   |   |   | 1 | **13** |
| **Töluorð**     |   |   |   |   | 69 |   |   |   | 10 | **79** |
| **Fornöfn**     |   |   |   |   | 38 |   |   |   | 2 | **40** |
| **Smáorð**      |   |   |   |   |   |   |   |   |   | **98** |
| **Alls**        |   |   |   |   | **539** |   |   |   | **99** | **638** |


## Forkröfur (Requirements)

`Python3.10.6` eða nýrra (þó eldri útgáfur gætu mögulega virkað), `pip` og pakkar listaðir í `requirements.txt`, sækir og setur upp pakka með

```bash
pip install -Ur requirements.txt
```

## Notkun (Usage)

```bash
python main.py --help
```

Smíða gagnagrunn:

```bash
python main.py --build-db
```

Skrifa orð úr grunni í textaskrár:

```bash
python main.py --write-files
```

Bæta við orði í gegnum skipanalínu (CLI):

```bash
python main.py --add-word
```

### Orðaviðbætur

Fyrir lesendur sem hafa áhuga á að leggja til orð sem þykja vanta í grunninn þá er ofangreind `--add-word` skipun til einhvers brúks en því miður er virknin til að bæta við orðum í gegnum skipanalínuna enn sem komið er mjög takmörkuð, og sé vilji til að bæta við mismunandi týpum sagnorða, samsettum orðum og fleira er eina leiðin enn sem komið er að kynna sér strúktúr JSON skráa fyrir sambærileg orð og handvirkt afrita viðeigandi skrá í nýja, breyta innihaldi hennar og keyra svo

```bash
python main.py --build-db --write-files
```

eða


```bash
python main.py --rebuild-db --write-files
```

til að smíða/endursmíða gagnagrunninn með viðbættu orðunum og færa síðan innihald gagnagrunnsins aftur í textaskrár.

Athugið að þegar verið er að henda saman JSON skrá fyrir samsett orð þá þarf ekki að græja beygingarmyndir þar sem þær eru leiddar út frá upplýsingunum í `"samsett"` listanum. **Dæmi:** þegar ég bætti við orðinu "hóflegur" var nóg að sjá til þess að allir orðhlutar orðsins væru til staðar og útbúa síðan svoútlítandi skrá og vista sem `lysingarord/hóflegur.json`:

```json
{
	"orð": "hóflegur",
	"flokkur": "lýsingarorð",
	"samsett": [
		{
			"mynd": "hóf",
			"samsetning": "stofn",
			"orð": "hóf",
			"flokkur": "nafnorð",
			"kyn": "hk",
			"hash": ""
		},
		{
			"orð": "legur",
			"flokkur": "lýsingarorð",
			"ósjálfstætt": true,
			"hash": ""
		}
	],
	"hash": ""
}
```

svo þegar búið var að smíða grunninn og skrifa út JSON skrár úr grunninum þá bættust beygingarmyndirnar við út frá upplýsingunum í `"samsett"` listanum. Hakkastrengirnir í `"hash"` gildinu eru ekki notaðir í import ferlinu en verða til í export ferlinu og eru síðan notaðir þegar smíðuð er sjón fyrir sjáanda (sjá neðar).

### Orðaleit

Til að athuga hvort orð sé til staðar í grunni er hægt að gera uppflettingu í smíðuðum gagnagrunni með tólum að eigin vali, leita að JSON skrá með nafni sem inniheldur umrætt orð, eða með því að smíða sjón fyrir sjáanda (e. sight for seer):

```bash
python main.py --build-sight
```

ofangreind skipun býr til forsmíðaða orðauppflettingu útfrá orðagögnum í JSON skrám og vistar í `lokaord/database/data/disk/lokaord/sight.pointless` (eða `lokaord/database/data/disk/lokaord/sight.pickle` á windows), þessa forsmíðuðu leit þarf að endursmíða í hvert sinn sem JSON skrárnar breytast, en hana er svo hægt að nota fyrir uppflettingu stöku orði:

```bash
python main.py --search "orð"
```

eða fyrir heilu setningarnar:

```bash
python main.py --scan-sentence "Hér er haugur orða í hóflega langri setningu."
```

## Frávik frá hefðbundinni íslensku (Deviances from traditional icelandic)

Í grunninum eru frávik frá hefðbundinni íslensku þegar kemur að skrift orða sem innihalda tvöfalt L. Þá eru þau "tvöfalt-L" orð sem borin eru fram með svokölluðu klikk-hljóði skrifuð með "łl" í stað "ll", þ.e. fyrra ełlið er hið pólska Ł. Þetta frávik er innleitt með það í huga að geta greint á miłli orða eins og "galli" (amfestingur eða einhver flík) og "gałli" (vankantur eða brestur).

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
