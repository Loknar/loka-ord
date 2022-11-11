# Loka-Orð

Frjálst gagnasafn yfir íslensk orð, beygingamyndir þeirra og fleira, undir opnu almenningseignarleyfi (e. public domain licence).

Gagnasafnið telur 140 nafnorð, 8 lýsingarorð, 5 sagnorð.

## Forkröfur

`Python3.10.6` eða nýrra, `pip` og pakkar listaðir í `requirements.txt`, setur upp pakka með

```bash
pip install -Ur requirements.txt
```

## Notkun

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
