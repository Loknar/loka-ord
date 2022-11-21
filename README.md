# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir þeirra og fleira, undir frjálsu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur eftirfarandi fjölda orða:

|   | ób.l | kk | kvk | hk | kjarna-orð | kk | kvk | hk | samsett-orð | samtals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Nafnorð**     |   | 64 | 63 | 61 | 188 | 16 | 2 | 9 | 27 | **215** |
| **Lýsingarorð** | 6 |   |   |   | 9 |   |   |   | 7 | **16** |
| **Sagnorð**     |   |   |   |   | 7 |   |   |   | 1 | **8** |
| **Töluorð**     |   |   |   |   | 69 |   |   |   | 10 | **79** |
| **Fornöfn**     |   |   |   |   | 38 |   |   |   | 2 | **40** |
| **Smáorð**      |   |   |   |   |   |   |   |   |   | **96** |
| **Alls**        |   |   |   |   | **408** |   |   |   | **47** | **455** |


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

Fyrir lesendur sem hafa áhuga á að leggja til orð sem þykja vanta í grunninn þá er ofangreind `--add-word` skipun til einhvers brúks en því miður er virknin til að bæta við orðum í gegnum skipanalínuna enn sem komið er mjög takmarkað, og sé vilji til að bæta við mismunandi týpum sagnorða, samsettum orðum og fleira er eina leiðin enn sem komið er að kynna sér strúktúr JSON skráa fyrir sambærileg orð og handvirkt afrita viðeigandi skrá í nýja, breyta innihaldi hennar og keyra svo

```bash
python main.py --build-db --write-files
```

eða


```bash
python main.py --rebuild-db --write-files
```

til að smíða/endursmíða gagnagrunninn með viðbættu orðunum og færa síðan innihald gagnagrunnsins aftur í textaskrár.

## Orðframlög (Contributing)

**Til ykkar sem hafið hug á að leggja til orð í grunninn!**

Mikilvægt er við framlag orða að ekki sé um afritun úr öðrum orðagrunnum að ræða er heyra undir útgáfuskilmála sem þykja ósamrýmanlegir almenningseignarleyfi þessa verkefnis.

Orðagjöfum ber að tryggja að orð sem lögð eru til verkefnisins séu þeim frjálst að gefa, þá er öruggast að orðin komi beint úr höfði þeirra sem reiðir þau fram.

Orð sem bætt er í grunninn heyra undir almenningseignarleyfi verkefnisins og verða því almenningseign.

## Frávik frá hefðbundinni íslensku (Deviances from traditional icelandic)

Í þessum grunni má finna frávik frá hefðbundinni íslensku þegar kemur að orðum sem innihalda tvöfalt L. Þá eru þau "tvöfalt-L" orð sem borin eru fram með svokölluðu klikk-hljóði skrifuð með "łl" í stað "ll", þ.e. fyrra ełlið er hið pólska Ł. Þetta frávik er innleitt með það í huga að geta greint á miłli orða eins og "galli" (amfestingur eða einhver flík) og "gałli" (vankantur eða brestur).

Tungumál breytast og þróast. Samhliða því að leggja áherslu á að vanda okkur við notkun tungumáls okkar verðum við að vera opin fyrir breytingum sem bæta það eða leysa vandamál við notkun þess.

Ég tel að geta til að greina á miłli "tvöfalt-L" orða sem borin eru fram með klikk-hljóði og annarra sé mjög nytsamleg og jafnvel nauðsynleg þegar kemur að orðhugbúnaðartæknivæðingu. Slík geta (útfrá orðinu stöku, þ.e. þurfa ekki að leiða það út frá textasamhengi) mundi auðvelda til muna smíði talgervils og málgreinis.

## Viðhaldari (Maintainer)

Hæ, og takk ef þú last svona langt. Ég skapa lokaorð orðagrunninn og gef hann hér út undir LGPLv3 leyfi. Það geri ég vegna þess að ég vil að hverjum og einum sé frjálst að smíða og nota grunninn á hvern þann hátt sem viðkomandi þóknast. En samhliða óska ég þess að hverjar þær breytingar á virkni, gögnum eða gagnastrúktúr orðagrunnsins séu gefnar út undir sama LGPLv3 leyfi, svo að viðbætur eða breytingar eins notanda geti orðið öðrum notendum sem grunninn nota að gagni.

[@Loknar](https://github.com/Loknar)
