# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir þeirra og fleira, undir frjálsu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur eins og er 201 nafnorð, 11 lýsingarorð, 8 sagnorð, 40 töluorð.

## Forkröfur (Requirements)

`Python3.10.6` eða nýrra, `pip` og pakkar listaðir í `requirements.txt`, setur upp pakka með

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

Fyrir lesendur sem hafa áhuga á að leggja til orð sem þykja vanta í grunninn þá er ofangreind skipanalínuskipun til einhvers brúks en því miður er skipanalínutólið til að bæta við orðum enn sem komið er mjög takmarkað, og sé vilji til að bæta við mismunandi týpum sagnorða eða samsettum orðum er eina leiðin enn sem komið er að kynna sér strúktúr JSON skráa fyrir sambærileg orð og handvirkt afrita einhverja þeirra skráa í viðeigandi nefnda nýja skrá, breyta innihaldi hennar og keyra síðan

```bash
python main.py --rebuild-db --write-files
```

til að endursmíða gagnagrunninn með viðbættu skránum og skrifa síðan innihald grunnsins aftur í textaskrár.

## Orðframlög (Contributing)

**Til ykkar sem hafið hug á að leggja til orð í grunninn!**

Mikilvægt er við framlag orða að ekki sé um afritun úr öðrum orðagrunnum að ræða er heyra undir útgáfuskilmála sem þykja ósamrýmanlegir almenningseignarleyfi þessa verkefnis.

Orðagjöfum ber að tryggja að orð sem lögð eru til verkefnisins séu þeim frjálst að gefa, þá er öruggast að orðin komi beint úr höfði þeirra sem reiðir þau fram.

Orð sem bætt er í grunninn munu heyra undir almenningseignarleyfi verkefnisins og því verða almenningseign.
