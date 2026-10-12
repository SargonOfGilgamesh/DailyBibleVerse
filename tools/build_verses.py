#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generate the verse data files of the Daily Bible Verse plasmoid.

The widget never ships verse text typed by hand. This script reads
public-domain Bible source files, extracts the 366 references listed in
tools/references.txt and writes one JavaScript data file per translation to
contents/code/verses/.

Usage (run from anywhere):

    python3 tools/build_verses.py --download   # fetch missing source files
    python3 tools/build_verses.py              # build every translation
    python3 tools/build_verses.py en_kjv       # build only the given ids
    python3 tools/build_verses.py --check      # also list verses worth a look

Source files are expected in tools/sources/ under the file names given in
TRANSLATIONS below. Only the Python 3 standard library is used.

Adding a translation:
  1. Add an entry to TRANSLATIONS (source file, names, numbering).
  2. Run this script.
  3. Add one ".import" line and one registry entry to
     contents/code/translations.js.
"""

import argparse
import html
import json
import re
import statistics
import struct
import sys
import urllib.parse
import urllib.request
import zipfile
import zlib
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SOURCES_DIR = TOOLS_DIR / "sources"
REFERENCES_FILE = TOOLS_DIR / "references.txt"
THEMES_FILE = TOOLS_DIR / "themes.txt"
OUTPUT_DIR = TOOLS_DIR.parent / "contents" / "code" / "verses"

MAX_VERSES_PER_REFERENCE = 3
EXPECTED_REFERENCES = 366

# The 66 books in canonical order, as 3-letter USFM codes. Sources that list
# their books without codes (scrollmapper JSON) are matched by position.
BOOK_CODES = (
    "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB "
    "PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP "
    "HAG ZEC MAL MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI "
    "2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV"
).split()

EBIBLE_URL = "https://ebible.org/Scriptures/{file}"
SCROLLMAPPER_URL = ("https://raw.githubusercontent.com/scrollmapper/"
                    "bible_databases/master/formats/json/{file}")
CROSSWIRE_URL = "https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/{file}"


def ebible(translation_id):
    file = f"{translation_id}_usfm.zip"
    return {"type": "usfm", "file": file, "url": EBIBLE_URL.format(file=file)}


def scrollmapper(name):
    file = f"{name}.json"
    return {"type": "json", "file": file, "url": SCROLLMAPPER_URL.format(file=file)}


def crosswire(name):
    file = f"{name}.zip"
    return {"type": "sword", "file": file, "url": CROSSWIRE_URL.format(file=file)}


SEFARIA_URL = "https://www.sefaria.org/download/version/{name}"


def sefaria(book, title, version):
    """One book of a Sefaria text version, e.g. a Targum."""
    name = f"{title} - he - {version}.json"
    return {"type": "sefaria", "file": "sefaria_" + title.replace(" ", "_") + ".json",
            "url": SEFARIA_URL.format(name=urllib.parse.quote(name)), "book": book}


def only(source, books):
    """Use only the given books of a source."""
    return dict(source, books=tuple(books))


def book_names(names):
    """Turn 66 '|'-separated names in canonical order into {code: name}."""
    names = [name.strip() for name in names.split("|")]
    assert len(names) == len(BOOK_CODES), names
    return dict(zip(BOOK_CODES, names))


# Book names as written in scrollmapper JSON files, used to find the books.
SCROLLMAPPER_BOOKS = book_names(
    "Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|I Samuel|"
    "II Samuel|I Kings|II Kings|I Chronicles|II Chronicles|Ezra|Nehemiah|"
    "Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Solomon|Isaiah|Jeremiah|"
    "Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|"
    "Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|"
    "Romans|I Corinthians|II Corinthians|Galatians|Ephesians|Philippians|"
    "Colossians|I Thessalonians|II Thessalonians|I Timothy|II Timothy|Titus|"
    "Philemon|Hebrews|James|I Peter|II Peter|I John|II John|III John|Jude|"
    "Revelation of John")

# Localized book names for sources that have none, or only long or
# upper-case headings. "Psalm" is singular because a reference names one.
SWEDISH_BOOKS = book_names(
    "1 Mosebok|2 Mosebok|3 Mosebok|4 Mosebok|5 Mosebok|Josua|Domarboken|Rut|"
    "1 Samuelsboken|2 Samuelsboken|1 Kungaboken|2 Kungaboken|1 Krönikeboken|"
    "2 Krönikeboken|Esra|Nehemja|Ester|Job|Psaltaren|Ordspråksboken|"
    "Predikaren|Höga Visan|Jesaja|Jeremia|Klagovisorna|Hesekiel|Daniel|Hosea|"
    "Joel|Amos|Obadja|Jona|Mika|Nahum|Habackuk|Sefanja|Haggai|Sakarja|Malaki|"
    "Matteus|Markus|Lukas|Johannes|Apostlagärningarna|Romarbrevet|"
    "1 Korintierbrevet|2 Korintierbrevet|Galaterbrevet|Efesierbrevet|"
    "Filipperbrevet|Kolosserbrevet|1 Tessalonikerbrevet|2 Tessalonikerbrevet|"
    "1 Timoteusbrevet|2 Timoteusbrevet|Titusbrevet|Filemonbrevet|"
    "Hebreerbrevet|Jakobsbrevet|1 Petrusbrevet|2 Petrusbrevet|"
    "1 Johannesbrevet|2 Johannesbrevet|3 Johannesbrevet|Judasbrevet|"
    "Uppenbarelseboken")

DUTCH_BOOKS = book_names(
    "Genesis|Exodus|Leviticus|Numeri|Deuteronomium|Jozua|Richteren|Ruth|"
    "1 Samuël|2 Samuël|1 Koningen|2 Koningen|1 Kronieken|2 Kronieken|Ezra|"
    "Nehemia|Esther|Job|Psalm|Spreuken|Prediker|Hooglied|Jesaja|Jeremia|"
    "Klaagliederen|Ezechiël|Daniël|Hosea|Joël|Amos|Obadja|Jona|Micha|Nahum|"
    "Habakuk|Zefanja|Haggaï|Zacharia|Maleachi|Mattheüs|Markus|Lukas|Johannes|"
    "Handelingen|Romeinen|1 Korinthe|2 Korinthe|Galaten|Efeze|Filippenzen|"
    "Kolossenzen|1 Thessalonicenzen|2 Thessalonicenzen|1 Timotheüs|"
    "2 Timotheüs|Titus|Filemon|Hebreeën|Jakobus|1 Petrus|2 Petrus|1 Johannes|"
    "2 Johannes|3 Johannes|Judas|Openbaring")

ITALIAN_BOOKS = book_names(
    "Genesi|Esodo|Levitico|Numeri|Deuteronomio|Giosuè|Giudici|Rut|1 Samuele|"
    "2 Samuele|1 Re|2 Re|1 Cronache|2 Cronache|Esdra|Neemia|Ester|Giobbe|"
    "Salmo|Proverbi|Ecclesiaste|Cantico dei Cantici|Isaia|Geremia|"
    "Lamentazioni|Ezechiele|Daniele|Osea|Gioele|Amos|Abdia|Giona|Michea|Naum|"
    "Abacuc|Sofonia|Aggeo|Zaccaria|Malachia|Matteo|Marco|Luca|Giovanni|Atti|"
    "Romani|1 Corinzi|2 Corinzi|Galati|Efesini|Filippesi|Colossesi|"
    "1 Tessalonicesi|2 Tessalonicesi|1 Timoteo|2 Timoteo|Tito|Filemone|Ebrei|"
    "Giacomo|1 Pietro|2 Pietro|1 Giovanni|2 Giovanni|3 Giovanni|Giuda|"
    "Apocalisse")

PORTUGUESE_BOOKS = book_names(
    "Gênesis|Êxodo|Levítico|Números|Deuteronômio|Josué|Juízes|Rute|1 Samuel|"
    "2 Samuel|1 Reis|2 Reis|1 Crônicas|2 Crônicas|Esdras|Neemias|Ester|Jó|"
    "Salmo|Provérbios|Eclesiastes|Cânticos|Isaías|Jeremias|Lamentações|"
    "Ezequiel|Daniel|Oseias|Joel|Amós|Obadias|Jonas|Miqueias|Naum|Habacuque|"
    "Sofonias|Ageu|Zacarias|Malaquias|Mateus|Marcos|Lucas|João|Atos|Romanos|"
    "1 Coríntios|2 Coríntios|Gálatas|Efésios|Filipenses|Colossenses|"
    "1 Tessalonicenses|2 Tessalonicenses|1 Timóteo|2 Timóteo|Tito|Filemom|"
    "Hebreus|Tiago|1 Pedro|2 Pedro|1 João|2 João|3 João|Judas|Apocalipse")

RUSSIAN_BOOKS = book_names(
    "Бытие|Исход|Левит|Числа|Второзаконие|Иисус Навин|Судьи|Руфь|1 Царств|"
    "2 Царств|3 Царств|4 Царств|1 Паралипоменон|2 Паралипоменон|Ездра|Неемия|"
    "Есфирь|Иов|Псалом|Притчи|Екклесиаст|Песнь Песней|Исаия|Иеремия|"
    "Плач Иеремии|Иезекииль|Даниил|Осия|Иоиль|Амос|Авдий|Иона|Михей|Наум|"
    "Аввакум|Софония|Аггей|Захария|Малахия|От Матфея|От Марка|От Луки|"
    "От Иоанна|Деяния|Римлянам|1 Коринфянам|2 Коринфянам|Галатам|Ефесянам|"
    "Филиппийцам|Колоссянам|1 Фессалоникийцам|2 Фессалоникийцам|1 Тимофею|"
    "2 Тимофею|Титу|Филимону|Евреям|Иакова|1 Петра|2 Петра|1 Иоанна|2 Иоанна|"
    "3 Иоанна|Иуды|Откровение")

POLISH_BOOKS = book_names(
    "Rodzaju|Wyjścia|Kapłańska|Liczb|Powtórzonego Prawa|Jozuego|Sędziów|Rut|"
    "1 Samuela|2 Samuela|1 Królewska|2 Królewska|1 Kronik|2 Kronik|Ezdrasza|"
    "Nehemiasza|Estery|Hioba|Psalm|Przysłów|Kaznodziei|Pieśń nad Pieśniami|"
    "Izajasza|Jeremiasza|Lamentacje|Ezechiela|Daniela|Ozeasza|Joela|Amosa|"
    "Abdiasza|Jonasza|Micheasza|Nahuma|Habakuka|Sofoniasza|Aggeusza|"
    "Zachariasza|Malachiasza|Mateusza|Marka|Łukasza|Jana|Dzieje Apostolskie|"
    "Rzymian|1 Koryntian|2 Koryntian|Galacjan|Efezjan|Filipian|Kolosan|"
    "1 Tesaloniczan|2 Tesaloniczan|1 Tymoteusza|2 Tymoteusza|Tytusa|Filemona|"
    "Hebrajczyków|Jakuba|1 Piotra|2 Piotra|1 Jana|2 Jana|3 Jana|Judy|"
    "Objawienie")

FINNISH_BOOKS = book_names(
    "1. Mooseksen kirja|2. Mooseksen kirja|3. Mooseksen kirja|"
    "4. Mooseksen kirja|5. Mooseksen kirja|Joosua|Tuomarien kirja|Ruut|"
    "1. Samuelin kirja|2. Samuelin kirja|1. Kuningasten kirja|"
    "2. Kuningasten kirja|1. Aikakirja|2. Aikakirja|Esra|Nehemia|Ester|Job|"
    "Psalmi|Sananlaskut|Saarnaaja|Korkea veisu|Jesaja|Jeremia|Valitusvirret|"
    "Hesekiel|Daniel|Hoosea|Jooel|Aamos|Obadja|Joona|Miika|Naahum|Habakuk|"
    "Sefanja|Haggai|Sakarja|Malakia|Matteus|Markus|Luukas|Johannes|"
    "Apostolien teot|Roomalaiskirje|1. Korinttilaiskirje|2. Korinttilaiskirje|"
    "Galatalaiskirje|Efesolaiskirje|Filippiläiskirje|Kolossalaiskirje|"
    "1. Tessalonikalaiskirje|2. Tessalonikalaiskirje|1. Timoteuksen kirje|"
    "2. Timoteuksen kirje|Tituksen kirje|Filemonin kirje|Heprealaiskirje|"
    "Jaakobin kirje|1. Pietarin kirje|2. Pietarin kirje|1. Johanneksen kirje|"
    "2. Johanneksen kirje|3. Johanneksen kirje|Juudaksen kirje|Ilmestyskirja")

# Copied from the book headings of the public-domain Korean Bible on
# eBible.org (translation id kor); the Korean source used here has none.
KOREAN_BOOKS = book_names(
    "창세기|출애굽기|레위기|민수기|신명기|여호수아|사사기|룻기|사무엘상|사무엘하|"
    "열왕기상|열왕기하|역대상|역대하|에스라|느헤미야|에스더|욥기|시편|잠언|전도서|"
    "아가|이사야|예레미야|예레미야 애가|에스겔|다니엘|호세아|요엘|아모스|오바댜|"
    "요나|미가|나훔|하박국|스바냐|학개|스가랴|말라기|마태복음|마가복음|누가복음|"
    "요한복음|사도행전|로마서|고린도전서|고린도후서|갈라디아서|에베소서|빌립보서|"
    "골로새서|데살로니가전서|데살로니가후서|디모데전서|디모데후서|디도서|빌레몬서|"
    "히브리서|야고보서|베드로전서|베드로후서|요한1서|요한2서|요한3서|유다서|"
    "요한계시록")

# The Hebrew and Arabic sources have good Old Testament names; only the New
# Testament names (machine-made or very long headings) are replaced.
NEW_TESTAMENT = BOOK_CODES[39:]

HEBREW_NT_BOOKS = dict(zip(NEW_TESTAMENT, (
    "מתי|מרקוס|לוקס|יוחנן|מעשי השליחים|רומים|קורינתים א|קורינתים ב|גלטים|"
    "אפסים|פיליפים|קולוסים|תסלוניקים א|תסלוניקים ב|טימותיאוס א|טימותיאוס ב|"
    "טיטוס|פילימון|עברים|יעקב|פטרוס א|פטרוס ב|יוחנן א|יוחנן ב|יוחנן ג|יהודה|"
    "התגלות").split("|")))

ARABIC_NT_BOOKS = dict(zip(NEW_TESTAMENT, (
    "متى|مرقس|لوقا|يوحنا|أعمال الرسل|رومية|كورنثوس الأولى|كورنثوس الثانية|"
    "غلاطية|أفسس|فيلبي|كولوسي|تسالونيكي الأولى|تسالونيكي الثانية|"
    "تيموثاوس الأولى|تيموثاوس الثانية|تيطس|فليمون|العبرانيين|يعقوب|"
    "بطرس الأولى|بطرس الثانية|يوحنا الأولى|يوحنا الثانية|يوحنا الثالثة|"
    "يهوذا|رؤيا يوحنا").split("|")))
assert len(HEBREW_NT_BOOKS) == len(ARABIC_NT_BOOKS) == len(NEW_TESTAMENT)

# Psalms whose title is a verse of its own in Hebrew numbering, so that the
# following verses are numbered 1 (Psalm 51: 2) higher than in the KJV.
# All such Psalms are listed (taken from the verse counts of the Leningrad
# Codex source).
HEBREW_PSALM_OFFSETS = {
    3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 12: 1, 18: 1, 19: 1, 20: 1,
    21: 1, 22: 1, 30: 1, 31: 1, 34: 1, 36: 1, 38: 1, 39: 1, 40: 1, 41: 1,
    42: 1, 44: 1, 45: 1, 46: 1, 47: 1, 48: 1, 49: 1, 51: 2, 52: 2, 53: 1,
    54: 2, 55: 1, 56: 1, 57: 1, 58: 1, 59: 1, 60: 2, 61: 1, 62: 1, 63: 1,
    64: 1, 65: 1, 67: 1, 68: 1, 69: 1, 70: 1, 75: 1, 76: 1, 77: 1, 80: 1,
    81: 1, 83: 1, 84: 1, 85: 1, 88: 1, 89: 1, 92: 1, 102: 1, 108: 1, 140: 1,
    142: 1,
}

# The Russian Synodal translation counts the Psalms as the Greek Bible does:
# KJV Psalms 11 to 113 and 117 to 146 are one lower there. (KJV 9 and 10,
# 114 to 116 and 147 are joined or split and need a "references" rule.)
SYNODAL_PSALM_CHAPTERS = {chapter: chapter - 1
                          for chapter in (*range(11, 114), *range(117, 147))}

CHINESE_CLEANUP = [
    ("(?<=[，。；：、！？」』]) (?=\\S)", ""),
    # Also between two characters, except the space of respect before 神.
    ("(?<=[\u4e00-\u9fff]) (?=(?!神)[\u4e00-\u9fff])", ""),
]

# Names of the Hebrew letters that head the verses of an acrostic poem
# (Psalms 34, 37, 111, 112, 145, Proverbs 31, Lamentations) in some sources.
ACROSTIC_CLEANUP = [(
    r"(?:^|(?<=[.;:!?,] ))(?:Aleph|Beth|Gimel|Daleth|He|Vau|Zain|Cheth|Teth|"
    r"Jod|Caph|Lamed|Mem|Nun|Samech|Ain|Pe|Tsade|Koph|Resch|Schin|Thau)\. ", "")]

# Syriac (Aramaic) names of the books used in references.txt and themes.txt,
# typed by hand: the Aramaic sources carry no book names. A native reader
# should check them.
SYRIAC_BOOKS = {
    "GEN": "ܒܪܝܬܐ", "EXO": "ܡܦܩܢܐ", "LEV": "ܟܗܢ̈ܐ", "NUM": "ܡܢܝܢܐ",
    "DEU": "ܬܢܝܢ ܢܡܘܣܐ", "JOS": "ܝܫܘܥ ܒܪ ܢܘܢ", "RUT": "ܪܥܘܬ",
    "1SA": "ܫܡܘܐܝܠ ܐ", "2SA": "ܫܡܘܐܝܠ ܒ", "1CH": "ܕܒܪܝܡܝܢ ܐ",
    "2CH": "ܕܒܪܝܡܝܢ ܒ", "NEH": "ܢܚܡܝܐ", "EST": "ܐܣܬܝܪ", "JOB": "ܐܝܘܒ",
    "PSA": "ܡܙܡܘܪܐ", "PRO": "ܡܬ̈ܠܐ", "ECC": "ܩܘܗܠܬ",
    "SNG": "ܬܫܒܚܬ ܬܫܒ̈ܚܬܐ", "ISA": "ܐܫܥܝܐ", "JER": "ܐܪܡܝܐ",
    "LAM": "ܐܘܠܝ̈ܬܐ", "EZK": "ܚܙܩܝܐܝܠ", "DAN": "ܕܢܝܐܝܠ", "HOS": "ܗܘܫܥ",
    "JOL": "ܝܘܐܝܠ", "AMO": "ܥܡܘܣ", "MIC": "ܡܝܟܐ", "NAM": "ܢܚܘܡ",
    "HAB": "ܚܒܩܘܩ", "ZEP": "ܨܦܢܝܐ", "ZEC": "ܙܟܪܝܐ", "MAL": "ܡܠܐܟܝ",
    "MAT": "ܡܬܝ", "MRK": "ܡܪܩܘܣ", "LUK": "ܠܘܩܐ", "JHN": "ܝܘܚܢܢ",
    "ACT": "ܦܪܟܣܝܣ", "ROM": "ܪ̈ܗܘܡܝܐ", "1CO": "ܩܘܪ̈ܝܢܬܝܐ ܐ",
    "2CO": "ܩܘܪ̈ܝܢܬܝܐ ܒ", "GAL": "ܓܠܛܝ̈ܐ", "EPH": "ܐܦܣܝ̈ܐ",
    "PHP": "ܦܝܠܝܦܣܝ̈ܐ", "COL": "ܩܘܠܣܝ̈ܐ", "1TH": "ܬܣܠܘܢܝܩܝ̈ܐ ܐ",
    "2TH": "ܬܣܠܘܢܝܩܝ̈ܐ ܒ", "1TI": "ܛܝܡܬܐܘܣ ܐ", "2TI": "ܛܝܡܬܐܘܣ ܒ",
    "TIT": "ܛܝܛܘܣ", "PHM": "ܦܝܠܡܘܢ", "HEB": "ܥܒܪ̈ܝܐ", "JAS": "ܝܥܩܘܒ",
    "1PE": "ܦܛܪܘܣ ܐ", "2PE": "ܦܛܪܘܣ ܒ", "1JN": "ܝܘܚܢܢ ܐ",
    "2JN": "ܝܘܚܢܢ ܒ", "3JN": "ܝܘܚܢܢ ܓ", "JUD": "ܝܗܘܕܐ", "REV": "ܓܠܝܢܐ",
}

# Aramaic. Old Testament: the Targums, the Jewish Aramaic translations, one
# Sefaria file per book. No Targum exists for Daniel and Nehemiah; for those
# the original text is used (Daniel 2:4 to 7:28 is Aramaic in the original,
# the rest of Daniel and Nehemiah are Hebrew). New Testament: the Syriac
# Peshitta, the Aramaic New Testament of the Syriac churches.
MIKRAOT_GEDOLOT = "Mikraot Gedolot"
ARAMAIC_SOURCES = [
    sefaria("GEN", "Onkelos Genesis", "Onkelos Genesis"),
    sefaria("EXO", "Onkelos Exodus", "Onkelos Exodus"),
    sefaria("LEV", "Onkelos Leviticus", "Onkelos Leviticus"),
    sefaria("NUM", "Onkelos Numbers", "Onkelos Numbers"),
    sefaria("DEU", "Onkelos Deuteronomy", "Onkelos Deuteronomy"),
    sefaria("JOS", "Targum Jonathan on Joshua", MIKRAOT_GEDOLOT),
    sefaria("RUT", "Aramaic Targum to Ruth", MIKRAOT_GEDOLOT),
    sefaria("1SA", "Targum Jonathan on I Samuel", MIKRAOT_GEDOLOT),
    sefaria("2SA", "Targum Jonathan on II Samuel", MIKRAOT_GEDOLOT),
    sefaria("1CH", "Targum of I Chronicles", "Wikisource Aramaic Targum to Chronicles"),
    sefaria("2CH", "Targum of II Chronicles", "Wikisource Aramaic Targum to Chronicles"),
    sefaria("EST", "Aramaic Targum to Esther", MIKRAOT_GEDOLOT),
    sefaria("JOB", "Aramaic Targum to Job", MIKRAOT_GEDOLOT),
    sefaria("PSA", "Aramaic Targum to Psalms", MIKRAOT_GEDOLOT),
    sefaria("PRO", "Aramaic Targum to Proverbs", MIKRAOT_GEDOLOT),
    sefaria("ECC", "Aramaic Targum to Ecclesiastes", MIKRAOT_GEDOLOT),
    sefaria("SNG", "Aramaic Targum to Song of Songs", MIKRAOT_GEDOLOT),
    sefaria("ISA", "Targum Jonathan on Isaiah", MIKRAOT_GEDOLOT),
    sefaria("JER", "Targum Jonathan on Jeremiah", MIKRAOT_GEDOLOT),
    sefaria("LAM", "Aramaic Targum to Lamentations", MIKRAOT_GEDOLOT),
    sefaria("EZK", "Targum Jonathan on Ezekiel", MIKRAOT_GEDOLOT),
    sefaria("HOS", "Targum Jonathan on Hosea", MIKRAOT_GEDOLOT),
    sefaria("JOL", "Targum Jonathan on Joel", MIKRAOT_GEDOLOT),
    sefaria("AMO", "Targum Jonathan on Amos", MIKRAOT_GEDOLOT),
    sefaria("MIC", "Targum Jonathan on Micah", MIKRAOT_GEDOLOT),
    sefaria("NAM", "Targum Jonathan on Nahum", MIKRAOT_GEDOLOT),
    sefaria("HAB", "Targum Jonathan on Habakkuk", MIKRAOT_GEDOLOT),
    sefaria("ZEP", "Targum Jonathan on Zephaniah", MIKRAOT_GEDOLOT),
    sefaria("ZEC", "Targum Jonathan on Zechariah", MIKRAOT_GEDOLOT),
    sefaria("MAL", "Targum Jonathan on Malachi", MIKRAOT_GEDOLOT),
    only(ebible("hboWLC"), ("DAN", "NEH")),
    only(scrollmapper("Peshitta"), NEW_TESTAMENT),
]

# Other places where the Hebrew Bible divides chapters differently.
HEBREW_REFERENCES = {
    "MAL.4.6": "3:24",  # Malachi 4 is 3:19-24
    # Psalm 13 has six verses in both numberings, but the title is verse 1
    # and the last two verses of the KJV are verse 6.
    "PSA.13.5-6": "13:6",
}

# Leningrad Codex: remove the cantillation marks (te'amim), meteg and paseq
# but keep the vowel points; remove the section marks (petuha, setuma) that
# follow some verses and the leftover markup around enlarged letters.
HEBREW_CLEANUP = [
    (r"'/?(?:l|seg)\b[^']*'", ""),
    ("[\u0591-\u05af\u05bd\u05c0]", ""),
    (r"(?<=\u05c3)\s*[\u05e4\u05e1]$", ""),
]

# ---------------------------------------------------------------------------
# Translations. The first entry must be the King James Version: its verse
# numbering is the one used in references.txt.
#
# id            file name of the generated module (<id>.js) and registry id
# name          translation name shown in the settings dialog
# language      language name shown in the settings dialog
# sources       one or more source files; later files fill in books that the
#               earlier ones do not contain (an OT-only plus an NT-only text)
#                 usfm:  zip of USFM files as published by eBible.org
#                 json:  a scrollmapper/bible_databases formats/json file
#                 sword: a CrossWire zText module (rawzip, KJV versification)
#                 sefaria: one book as downloaded from Sefaria; the file must
#                        state the licence "Public Domain"
#               only(source, books) takes just those books from a source
# book_names    book names; they override the names found in the source.
#               Sources without localized names need all names used.
# numbering     where the source numbers verses differently from the KJV:
#                 chapters    {book: {chapter: local chapter}}: the chapter
#                             has another number than in the KJV
#                 offsets     {book: {chapter: n}}: verse numbers in that
#                             (KJV) chapter are n higher than in the KJV
#                 references  {reference id: "chapter:verses"} for anything
#                             else, e.g. a verse split in two
#                 excerpts    {reference id: ("from" or "until", text)}: use
#                             only the part of the source text starting at,
#                             or ending before, the given words. For sources
#                             that merge two verses or append a note.
#                 display     {reference id: "chapter:verses"} to show when
#                             the position in the source file is not the
#                             numbering printed in that translation
#                 verified    chapters whose verse count differs from the KJV
#                             although the references in them need no change
#                             (checked by hand)
#               A referenced chapter whose verse count differs from the KJV
#               and is covered by none of these stops the build.
# verse_markers True: the source is squeezed into the KJV verse count and
#               notes the real number at the start of a renumbered verse, as
#               "{51:12}". The marker is removed and shown as the reference.
# squeezed      True: the source keeps its own (Hebrew) Psalm numbering but
#               has only as many verses per chapter as the KJV, so the last
#               verse of such a chapter holds two verses. The build then
#               demands an "excerpts" rule for references that land there.
# psalm_titles  "first_sentence": the source prints Psalm titles as the first
#               sentence of verse 1; remove it. Sources that mark titles
#               (USFM \d) or number them as a separate verse need nothing.
#               "excerpt": titles are joined to verse 1 without punctuation;
#               the build demands an "excerpts" rule for verse 1 of a Psalm
#               that has a title.
# initial_capitals  True: the source prints the first word of a chapter or
#               paragraph in capitals (a drop-cap convention); write it
#               normally
# cleanup       (regular expression, replacement) pairs applied to every
#               verse, for markup or notes the source leaves in the text
# credit        source and licence line written into the generated file
# ---------------------------------------------------------------------------
TRANSLATIONS = [
    {
        "id": "en_kjv",
        "name": "King James Version",
        "language": "English",
        "sources": [ebible("eng-kjv2006")],
        "book_names": {"PSA": "Psalm"},
        "credit": "King James Version (1769), public domain. "
                  "Source: eBible.org, translation id eng-kjv2006.",
    },
    {
        "id": "en_web",
        "name": "World English Bible",
        "language": "English",
        "sources": [ebible("engwebp")],
        "book_names": {"PSA": "Psalm"},
        # Romans 16:25-27 stands at the end of chapter 14.
        "numbering": {"verified": "ROM 14"},
        "credit": "World English Bible, public domain. "
                  "Source: eBible.org, translation id engwebp.",
    },
    {
        "id": "sv_1917",
        "name": "Bibeln 1917",
        "language": "Svenska",
        "sources": [scrollmapper("Swe1917")],
        "squeezed": True,
        "book_names": SWEDISH_BOOKS,
        # This file squeezes the Swedish (Hebrew) Psalm numbering into the
        # KJV verse count: the last two verses of a Psalm with a title verse
        # are merged into one. "excerpts" cuts out the wanted verse.
        "numbering": {
            # Ecclesiastes 7 starts one verse earlier in the Swedish Bible.
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS, "ECC": {7: 1}},
            "references": {
                "PSA.4.8": "4:8",
                "PSA.13.5-6": "13:6",
                "PSA.19.14": "19:14",
                "PSA.30.11-12": "30:12",
                "PSA.31.24": "31:24",
                "PSA.42.11": "42:11",
                "PSA.59.17": "59:17",
                "PSA.84.12": "84:12",
                "2CO.13.14": "13:13",
            },
            "excerpts": {
                # Verse 3 follows in the same line of the source.
                "COL.4.2": ("until", " 3; Och"),
                "PSA.4.8": ("from", "I frid vill"),
                "PSA.5.11": ("until", " Ty du, HERRE, välsignar"),
                "PSA.31.24": ("from", "Varen frimodiga"),
                "PSA.42.11": ("from", "Varför är du"),
                "PSA.59.17": ("from", "Min starkhet"),
                "PSA.84.12": ("from", "HERRE Sebaot, salig"),
                "PSA.19.14": ("from", "Låt min muns"),
                "PSA.46.10": ("until", " HERREN Sebaot"),
                "PSA.55.22": ("until", " Gud, du skall"),
                "PSA.84.11": ("until", " HERRE Sebaot"),
                "JHN.3.30": ("until", " --"),
                "EPH.4.32": ("until", " Ord markerade"),
            },
            "display": {
                "PSA.4.8": "4:9", "PSA.19.14": "19:15", "PSA.30.11-12": "30:12-13",
                "PSA.31.24": "31:25", "PSA.42.11": "42:12", "PSA.59.17": "59:18",
                "PSA.84.12": "84:13",
            },
            "verified": "3JN 1",
        },
        "psalm_titles": "first_sentence",
        "cleanup": [
            # Pointers to the glossary of the printed edition.
            (r"(\s+Se \S+(?: \S+)? i Ordförkl\w*\.?)+$", ""),
            # Alternative renderings appended to a verse.
            (r"\s+Eller(?: fastmer)?:.*$", ""),
            # Dashes are typed as two hyphens.
            (r"\s--(?=\s|$)", " \u2013"),
        ],
        "credit": "Svenska Bibeln, 1917 års kyrkobibel, public domain. "
                  "Source: scrollmapper/bible_databases, Swe1917.",
    },
    {
        "id": "de_luther1912",
        "name": "Luther 1912",
        "language": "Deutsch",
        "sources": [ebible("deu1912")],
        # "1. Chonik" is a typing error in the source.
        "book_names": {"PSA": "Psalm", "1CH": "1. Chronik"},
        # Luther divides John 10:10-12 differently from the KJV.
        "numbering": {
            "references": {"JHN.10.10": "10:10-11", "JHN.10.11": "10:12"},
            "excerpts": {"JHN.10.11": ("until", " Der Mietling")},
            # Luther counts Malachi 4 as 3:19-24; the source says so in the text.
            "display": {"MAL.4.6": "3:24"},
        },
        "psalm_titles": "first_sentence",
        "cleanup": [(r"\[\d+:\d+\]\s*", "")],
        "credit": "Lutherbibel 1912, public domain. "
                  "Source: eBible.org, translation id deu1912.",
    },
    {
        "id": "es_rv1909",
        "name": "Reina-Valera 1909",
        "language": "Español",
        "sources": [ebible("spaRV1909")],
        "book_names": {"PSA": "Salmo", "SNG": "Cantares", "MAT": "Mateo", "LUK": "Lucas"},
        "numbering": {
            "references": {"2CO.13.14": "13:13"},
            "excerpts": {
                # The source appends the subscription of the letter.
                "2CO.13.14": ("until", " La segunda Epístola"),
                # The verse starts with the heading of the acrostic stanza.
                "PSA.119.105": ("from", "Lámpara"),
            },
        },
        "psalm_titles": "first_sentence",
        "initial_capitals": True,
        "credit": "Reina-Valera 1909, public domain. "
                  "Source: eBible.org, translation id spaRV1909.",
    },
    {
        "id": "fr_lsg1910",
        "name": "Louis Segond 1910",
        "language": "Français",
        "sources": [ebible("fraLSG")],
        "book_names": {"PSA": "Psaume", "SNG": "Cantique des Cantiques"},
        "numbering": {
            "offsets": {
                "PSA": HEBREW_PSALM_OFFSETS,
                "ECC": {12: 2},
                "ISA": {9: -1, 64: -1},
            },
            "references": {"PSA.13.5-6": "13:6", "2CO.13.14": "13:13"},
            # Titles of two sentences ("De David. Cantique."), which the
            # first-sentence rule would remove only half of.
            "excerpts": {
                "PSA.32.1-2": ("from", "Heureux"),
                "PSA.127.1": ("from", "Si l\u2019Éternel"),
                "PSA.133.1": ("from", "Voici"),
                "PSA.145.1-3": ("from", "Je t\u2019exalterai"),
            },
            "verified": "ECC 4, NAM 1, MRK 9, MRK 10, 3JN 1",
        },
        "psalm_titles": "first_sentence",
        "credit": "Louis Segond 1910, public domain. "
                  "Source: eBible.org, translation id fraLSG.",
    },
    {
        "id": "nl_sv",
        "name": "Statenvertaling",
        "language": "Nederlands",
        "sources": [scrollmapper("DutSVV")],
        "squeezed": True,
        "book_names": DUTCH_BOOKS,
        # Squeezed into the KJV verse count like the Swedish file, see there.
        "numbering": {
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS},
            "references": {
                "PSA.4.8": "4:8", "PSA.13.5-6": "13:6",
                "PSA.19.14": "19:14", "PSA.30.11-12": "30:12",
                "PSA.31.24": "31:24", "PSA.42.11": "42:11", "PSA.59.17": "59:17",
                "PSA.84.12": "84:12",
            },
            "excerpts": {
                "PSA.4.8": ("from", "Ik zal in vrede"),
                "PSA.5.11": ("until", " Want Gij, HEERE, zult"),
                "PSA.31.24": ("from", "Zijt sterk"),
                "PSA.42.11": ("from", "Wat buigt gij"),
                "PSA.59.17": ("from", "Van U, o mijn Sterkte"),
                "PSA.84.12": ("from", "HEERE der heirscharen! welgelukzalig"),
                "PSA.19.14": ("from", "Laat de redenen"),
                "PSA.46.10": ("until", " De HEERE der heirscharen"),
                "PSA.55.22": ("until", " Maar Gij, o God"),
                "PSA.84.11": ("until", " HEERE der heirscharen"),
                # The verse starts with the heading of the acrostic stanza.
                "PSA.119.105": ("from", "Uw woord"),
            },
            "display": {
                "PSA.4.8": "4:9", "PSA.19.14": "19:15", "PSA.30.11-12": "30:12-13",
                "PSA.31.24": "31:25", "PSA.42.11": "42:12", "PSA.59.17": "59:18",
                "PSA.84.12": "84:13", "ISA.9.6": "9:5",
            },
        },
        "psalm_titles": "first_sentence",
        "cleanup": ACROSTIC_CLEANUP,
        "credit": "Statenvertaling (1637), public domain. "
                  "Source: scrollmapper/bible_databases, DutSVV.",
    },
    {
        "id": "it_diodati",
        "name": "Diodati",
        "language": "Italiano",
        "sources": [ebible("ita1885")],
        "book_names": ITALIAN_BOOKS,
        "initial_capitals": True,
        "numbering": {
            "offsets": {"ECC": {12: 2}, "ISA": {9: -1}},
            "references": {
                "PSA.18.2": "18:1",
                "2CO.13.14": "13:13",
                "GAL.3.26-28": "3:26-29",
                # Colossians 4:1 of the KJV closes chapter 3 here.
                "COL.4.2": "4:1",
            },
            "verified": "ISA 50, MRK 9, 2CO 1, COL 3, REV 7, 3JN 1",
        },
        "credit": "Diodati (1641, edition of 1885), public domain. "
                  "Source: eBible.org, translation id ita1885.",
    },
    {
        "id": "pt_almeida1911",
        "name": "Almeida 1911",
        "language": "Português",
        "sources": [crosswire("PorAlmeida1911")],
        "book_names": PORTUGUESE_BOOKS,
        "numbering": {"references": {"2CO.13.14": "13:13"}},
        # Stray marks left by the text recognition of the printed book.
        "cleanup": [(r"\*", "")] + ACROSTIC_CLEANUP,
        "credit": "João Ferreira de Almeida, edition of 1911 (reprint of the "
                  "1900 edition), text in the public domain; module "
                  "distributed under the GPL. Source: CrossWire Bible "
                  "Society, SWORD module PorAlmeida1911.",
    },
    {
        "id": "he_wlc",
        "name": "Leningrad Codex + Salkinson-Ginsburg NT",
        "language": "עברית",
        "sources": [ebible("hboWLC"), ebible("hebsg")],
        "book_names": dict(HEBREW_NT_BOOKS, ISA="ישעיהו", PRO="משלי", ECC="קהלת"),
        "numbering": {
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS, "ISA": {9: -1, 64: -1}},
            "references": HEBREW_REFERENCES,
            "verified": "ECC 4, DAN 3, JOL 2, NAM 1, MAL 3",
        },
        "cleanup": HEBREW_CLEANUP,
        "credit": "Old Testament: Westminster Leningrad Codex, public domain "
                  "(eBible.org, hboWLC). New Testament: Salkinson-Ginsburg "
                  "Hebrew New Testament, public domain (eBible.org, hebsg).",
    },
    {
        "id": "ar_vandyck",
        "name": "Van Dyck (فان دايك)",
        "language": "العربية",
        "sources": [ebible("arb-vd")],
        "book_names": dict(ARABIC_NT_BOOKS, PSA="مزمور"),
        "numbering": {"verified": "1TI 6, 3JN 1"},
        "credit": "Smith & Van Dyck Arabic Bible (1865), public domain. "
                  "Source: eBible.org, translation id arb-vd.",
    },
    {
        "id": "arc_targum_peshitta",
        "name": "Targum + Peshitta",
        "language": "Aramaic",
        "sources": ARAMAIC_SOURCES,
        "book_names": SYRIAC_BOOKS,
        "numbering": {
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS, "ISA": {9: -1, 64: -1}},
            "references": HEBREW_REFERENCES,
            "verified": "EXO 20, ECC 4, DAN 3, JOL 2, NAM 1, MAL 3, MRK 9",
        },
        # '(ס"א ...)' is an editor's note giving the reading of another
        # edition.
        # The Syriac end-of-verse mark stays on the line of the last word.
        "cleanup": HEBREW_CLEANUP + [(r'\s*\(ס"א[^)]*\)', ""),
                                     (" (?=\u0700)", "\u00a0")],
        "credit": "Old Testament: Targum Onkelos, Targum Jonathan and the "
                  "Targums to the Writings, public domain (Sefaria; Mikraot "
                  "Gedolot and Wikisource editions). Daniel and Nehemiah: "
                  "original text, Westminster Leningrad Codex, public domain "
                  "(eBible.org, hboWLC). New Testament: Syriac Peshitta, "
                  "British and Foreign Bible Society 1905, public domain "
                  "(scrollmapper/bible_databases, Peshitta).",
    },
    {
        "id": "ru_synodal",
        "name": "Синодальный перевод",
        "language": "Русский",
        "sources": [ebible("russyn")],
        "book_names": RUSSIAN_BOOKS,
        "numbering": {
            "chapters": {"PSA": SYNODAL_PSALM_CHAPTERS},
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS},
            "references": {
                # KJV Psalms 9 and 10 are Psalm 9 here, 114 and 115 are
                # Psalm 113, and 147:1-11 is Psalm 146.
                "PSA.9.1": "9:2", "PSA.9.9": "9:10", "PSA.9.10": "9:11",
                "PSA.13.5-6": "12:6",
                "PSA.115.11": "113:19",
                "PSA.147.3": "146:3", "PSA.147.11": "146:11",
                # Proverbs 13 has one verse more from verse 14 on.
                "PRO.13.12": "13:12", "PRO.13.20": "13:21",
                "2CO.13.14": "13:13",
            },
            "verified": "JOS 24, PRO 4, ECC 4, DAN 3, ROM 14, 3JN 1",
        },
        "credit": "Russian Synodal translation (1876), public domain. "
                  "Source: eBible.org, translation id russyn.",
    },
    {
        "id": "pl_gdanska",
        "name": "Biblia Gdańska",
        "language": "Polski",
        "sources": [scrollmapper("PolGdanska")],
        "squeezed": True,
        "book_names": POLISH_BOOKS,
        # Squeezed into the KJV verse count like the Swedish file, see there.
        "numbering": {
            "offsets": {"PSA": HEBREW_PSALM_OFFSETS},
            "references": {
                "PSA.4.8": "4:8",
                "PSA.13.5-6": "13:6",
                "PSA.19.14": "19:14",
                "PSA.30.11-12": "30:12",
                "PSA.31.24": "31:24",
                "PSA.42.11": "42:11",
                "PSA.59.17": "59:17",
                "PSA.84.12": "84:12",
                "2CO.13.14": "13:13",
            },
            "excerpts": {
                "PSA.4.8": ("from", "W pokoju"),
                "PSA.5.11": ("until", " Albowiem ty, Panie! sprawiedliwemu"),
                "PSA.31.24": ("from", "Zmacniajcie się"),
                "PSA.42.11": ("from", "Przeczże się smucisz"),
                "PSA.59.17": ("from", "O mocy moja"),
                "PSA.84.12": ("from", "Panie zastępów! błogosławiony"),
                "PSA.19.14": ("from", "Niechże będą"),
                "PSA.46.10": ("until", " Pan zastępów z nami"),
                "PSA.55.22": ("until", " Ale ich ty"),
                "PSA.84.11": ("until", " Panie zastępów"),
            },
            "display": {
                "PSA.4.8": "4:9", "PSA.19.14": "19:15", "PSA.30.11-12": "30:12-13",
                "PSA.31.24": "31:25", "PSA.42.11": "42:12", "PSA.59.17": "59:18",
                "PSA.84.12": "84:13",
            },
            "verified": "JER 29",
        },
        "psalm_titles": "first_sentence",
        "credit": "Biblia Gdańska (1632, edition of 1881), public domain. "
                  "Source: scrollmapper/bible_databases, PolGdanska.",
    },
    {
        "id": "fi_1938",
        "name": "Pyhä Raamattu 1933/1938",
        "language": "Suomi",
        "sources": [scrollmapper("FinPR")],
        "book_names": FINNISH_BOOKS,
        "verse_markers": True,
        # No marker here although the numbering differs (see HEBREW_REFERENCES).
        "numbering": {"references": {"PSA.13.5-6": "13:6"}},
        "psalm_titles": "first_sentence",
        "credit": "Pyhä Raamattu, Finnish church Bible of 1933 (Old "
                  "Testament) and 1938 (New Testament), public domain. "
                  "Source: scrollmapper/bible_databases, FinPR.",
    },
    {
        "id": "zh_union_simplified",
        "name": "和合本 (简体)",
        "language": "中文",
        "sources": [ebible("cmn-cu89s")],
        "numbering": {
            # Ephesians 6:2 and 6:3 are printed as one verse.
            "references": {"EPH.6.1-3": "6:1-2"},
            "display": {"EPH.6.1-3": "6:1-3"},
            "verified": "3JN 1",
        },
        # Line breaks of poetry arrive as spaces; Chinese is written without.
        "cleanup": CHINESE_CLEANUP,
        "credit": "Chinese Union Version with new punctuation, simplified "
                  "script, public domain. Source: eBible.org, translation id "
                  "cmn-cu89s.",
    },
    {
        "id": "zh_union_traditional",
        "name": "和合本 (繁體)",
        "language": "中文",
        "sources": [ebible("cmn-cu89t")],
        "numbering": {
            # Ephesians 6:2 and 6:3 are printed as one verse.
            "references": {"EPH.6.1-3": "6:1-2"},
            "display": {"EPH.6.1-3": "6:1-3"},
            "verified": "3JN 1",
        },
        # Line breaks of poetry arrive as spaces; Chinese is written without.
        "cleanup": CHINESE_CLEANUP,
        "credit": "Chinese Union Version with new punctuation, traditional "
                  "script, public domain. Source: eBible.org, translation id "
                  "cmn-cu89t.",
    },
    {
        "id": "ko_krv",
        "name": "개역한글",
        "language": "한국어",
        "sources": [scrollmapper("KorRV")],
        "book_names": KOREAN_BOOKS,
        "psalm_titles": "excerpt",
        "numbering": {
            "references": {"2CO.13.14": "13:13"},
            # Psalm titles are joined to verse 1 without any punctuation.
            "excerpts": {
                "PSA.9.1": ("from", "내가 전심으로"),
                "PSA.32.1-2": ("from", "허물의"),
                "PSA.34.1": ("from", "내가 여호와를 항상"),
                "PSA.46.1-2": ("from", "하나님은 우리의"),
                "PSA.47.1": ("from", "너희 만민들아"),
                "PSA.51.1-2": ("from", "하나님이여 주의 인자를"),
                "PSA.92.1-2": ("from", "지존자여"),
                "PSA.100.1-2": ("from", "온 땅이여"),
                "PSA.125.1": ("from", "여호와를 의뢰하는"),
                "PSA.133.1": ("from", "형제가"),
                "PSA.145.1-3": ("from", "왕이신"),
                "PSA.19.1": ("from", "하늘이"),
                "PSA.23.1-3": ("from", "여호와는 나의 목자"),
                "PSA.27.1": ("from", "여호와는 나의 빛"),
                "PSA.40.1-3": ("from", "내가 여호와를 기다리고"),
                "PSA.42.1-2": ("from", "하나님이여 사슴이"),
                "PSA.46.1": ("from", "하나님은 우리의"),
                "PSA.63.1": ("from", "하나님이여 주는"),
                "PSA.103.1-2": ("from", "내 영혼아"),
                "PSA.121.1-2": ("from", "내가 산을"),
                "PSA.127.1": ("from", "여호와께서 집을"),
            },
            "verified": "3JN 1",
        },
        "credit": "Korean Revised Version (개역한글, 1952/1961), public "
                  "domain. Source: scrollmapper/bible_databases, KorRV.",
    },
]


class BuildError(Exception):
    """A problem that must be fixed before the data can be published."""


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------

REFERENCE_RE = re.compile(r"^([1-3A-Z][A-Z]{2}) (\d+):(\d+)(?:-(\d+))?$")


def parse_reference(path, number, line):
    """'PSA 23:1-3' -> ('PSA', 23, 1, 3)"""
    match = REFERENCE_RE.match(line)
    if not match:
        raise BuildError(f"{path.name}:{number}: cannot parse '{line}'")
    book, chapter, first, last = match.groups()
    if book not in BOOK_CODES:
        raise BuildError(f"{path.name}:{number}: unknown book code '{book}'")
    first = int(first)
    last = int(last) if last else first
    if not first <= last < first + MAX_VERSES_PER_REFERENCE:
        raise BuildError(
            f"{path.name}:{number}: '{line}' must cover 1 to "
            f"{MAX_VERSES_PER_REFERENCE} verses")
    return (book, int(chapter), first, last)


def content_lines(path):
    """(line number, text) of the lines that are not blank or comments."""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line and not line.startswith("#"):
            yield number, line


def read_references(path):
    """Return the daily references as a list of (book, chapter, first, last)."""
    references = [parse_reference(path, number, line)
                  for number, line in content_lines(path)]

    if len(references) != EXPECTED_REFERENCES:
        raise BuildError(
            f"{path.name}: expected {EXPECTED_REFERENCES} references, "
            f"found {len(references)}")

    # No verse may be used twice, not even as part of two different ranges.
    seen = {}
    for reference in references:
        book, chapter, first, last = reference
        for verse in range(first, last + 1):
            key = (book, chapter, verse)
            if key in seen:
                raise BuildError(
                    f"{path.name}: {reference_id(reference)} overlaps "
                    f"{reference_id(seen[key])}")
            seen[key] = reference
    return references


THEME_RE = re.compile(r"^\[([a-z][a-z0-9_]*)\]$")


def read_themes(path):
    """Return {theme id: [references]} in file order."""
    themes = {}
    current = None
    for number, line in content_lines(path):
        match = THEME_RE.match(line)
        if match:
            if match.group(1) in themes:
                raise BuildError(f"{path.name}:{number}: theme '{line}' twice")
            current = themes.setdefault(match.group(1), [])
            continue
        if current is None:
            raise BuildError(f"{path.name}:{number}: reference before any [theme]")
        reference = parse_reference(path, number, line)
        if reference in current:
            raise BuildError(f"{path.name}:{number}: '{line}' twice in one theme")
        current.append(reference)
    for theme, references in themes.items():
        if not references:
            raise BuildError(f"{path.name}: theme '{theme}' is empty")
    return themes


def reference_id(reference):
    """('PSA', 23, 1, 3) -> 'PSA.23.1-3'. This is the key used by the widget."""
    book, chapter, first, last = reference
    verses = str(first) if first == last else f"{first}-{last}"
    return f"{book}.{chapter}.{verses}"


# ---------------------------------------------------------------------------
# Verse numbering
# ---------------------------------------------------------------------------

def parse_chapters(text):
    """'ECC 4, NAM 1' -> {('ECC', 4), ('NAM', 1)}"""
    chapters = set()
    for item in filter(None, (part.strip() for part in text.split(","))):
        book, chapter = item.split()
        chapters.add((book, int(chapter)))
    return chapters


def map_reference(numbering, reference):
    """Convert a KJV-numbered reference to the numbering of a source text.

    Returns ((book, chapter, first, last), handled). `handled` is True if the
    numbering rules of the translation say something about this reference.
    """
    book, chapter, first, last = reference
    key = reference_id(reference)
    if key in numbering.get("references", {}):
        local_chapter, verses = numbering["references"][key].split(":")
        local_first, _, local_last = verses.partition("-")
        return (book, int(local_chapter), int(local_first),
                int(local_last or local_first)), True
    local_chapter = numbering.get("chapters", {}).get(book, {}).get(chapter)
    offset = numbering.get("offsets", {}).get(book, {}).get(chapter)
    if local_chapter is not None or offset is not None:
        offset = offset or 0
        return (book, local_chapter or chapter, first + offset, last + offset), True
    verified = (book, chapter) in parse_chapters(numbering.get("verified", ""))
    return reference, verified


def chapter_lengths(bible):
    """{(book, chapter): highest verse number}"""
    lengths = {}
    for code, book in bible.items():
        for chapter, verse in book["verses"]:
            lengths[(code, chapter)] = max(lengths.get((code, chapter), 0), verse)
    return lengths


# ---------------------------------------------------------------------------
# Source parsers. Each returns {book code: {"name": str or None,
#                                           "verses": {(chapter, verse): text},
#                                           "titled": chapters with a title}}
# ---------------------------------------------------------------------------

# Footnotes and cross references, including their content.
USFM_NOTE_RE = re.compile(r"\\(f|fe|ef|x|ex)\s.*?\\\1\*", re.DOTALL)
# Alternate chapter/verse numbers printed inside the text.
USFM_ALT_NUMBER_RE = re.compile(r"\\(va|vp|ca)\s.*?\\\1\*", re.DOTALL)
# Word attributes such as |strong="H1234" before a closing marker.
USFM_ATTRIBUTE_RE = re.compile(r"\|[^\\\n]*(?=\\\+?[a-z]+\d*\*)")
USFM_CLOSING_RE = re.compile(r"\\\+?([a-z]+\d*)\*")
USFM_OPENING_RE = re.compile(r"\\\+?[a-z]+\d*\s?")
USFM_LINE_MARKER_RE = re.compile(r"^\\([a-z]+\d*)(?:\s+(.*))?$")
USFM_VERSE_RE = re.compile(r"\\v\s+(\S+)\s?")
# Paragraph-level markers whose text is not part of any verse: headers,
# titles, section headings, introductions, Psalm titles (\d) and similar.
USFM_NON_VERSE_RE = re.compile(
    r"^(id|ide|usfm|sts|rem|h\d?|toc\d|toca\d|mt\d?|mte\d?|ms\d?|mr|s\d?|sr|r|"
    r"sp|sd\d?|d|cl|cp|cd|qa|periph|i[a-z]+\d?)$")


def parse_usfm_book(text):
    """Parse one USFM file.

    Returns (book code, name, {(chapter, verse): text}, titled chapters).
    """
    text = USFM_NOTE_RE.sub("", text)
    text = USFM_ALT_NUMBER_RE.sub("", text)
    text = USFM_ATTRIBUTE_RE.sub("", text)
    # Markers that have a closing form (\w ...\w*) are character markers and
    # may start a continuation line; everything else starts a new paragraph.
    character_markers = set(USFM_CLOSING_RE.findall(text))

    code = None
    names = {}
    chapter = None
    verse = None
    in_verse_text = False
    pieces = {}
    titled = set()

    def add_content(content):
        nonlocal verse
        parts = USFM_VERSE_RE.split(content)
        if verse is not None and parts[0].strip():
            pieces[(chapter, verse)].append(parts[0])
        for number, verse_text in zip(parts[1::2], parts[2::2]):
            match = re.match(r"(\d+)", number)
            if not match or chapter is None:
                raise BuildError(f"{code}: unexpected verse marker '\\v {number}'")
            # A bridged verse ("1-2") is stored under its first number.
            verse = int(match.group(1))
            pieces.setdefault((chapter, verse), []).append(verse_text)

    for line in text.splitlines():
        line = line.strip()
        match = USFM_LINE_MARKER_RE.match(line)
        if not match or match.group(1) in character_markers:
            if in_verse_text:
                add_content(line)
            continue
        marker, rest = match.group(1), match.group(2) or ""
        if marker == "id":
            code = rest.split()[0].upper() if rest.split() else None
            in_verse_text = False
        elif marker == "c":
            chapter = int(re.match(r"\d+", rest).group(0))
            verse = None
            in_verse_text = False
        elif marker == "v":
            in_verse_text = True
            add_content(line)
        elif USFM_NON_VERSE_RE.match(marker) and "\\v " not in rest:
            if marker in ("h", "toc2") and rest.strip():
                names[marker] = rest.strip()
            elif marker == "d":
                titled.add(chapter)
            in_verse_text = False
        else:
            in_verse_text = True
            add_content(rest)

    verses = {key: clean_usfm_text(" ".join(value)) for key, value in pieces.items()}
    return code, names.get("toc2") or names.get("h"), verses, titled


def clean_usfm_text(text):
    text = USFM_CLOSING_RE.sub("", text)
    text = USFM_OPENING_RE.sub("", text)
    return clean_text(text)


def clean_text(text):
    """Remove paragraph signs and normalise white space.

    No-break spaces are kept: they hold a word and a following mark together.
    """
    text = text.replace("\u00b6", " ")
    return re.sub(r"[^\S\u00a0]+", " ", text).strip()


def parse_usfm_zip(path):
    books = {}
    with zipfile.ZipFile(path) as archive:
        for member in sorted(archive.namelist()):
            if not member.lower().endswith((".usfm", ".sfm")):
                continue
            code, name, verses, titled = parse_usfm_book(
                archive.read(member).decode("utf-8-sig"))
            if code in BOOK_CODES and verses:
                books[code] = {"name": name, "verses": verses, "titled": titled}
    return books


def parse_scrollmapper_json(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    codes = {name: code for code, name in SCROLLMAPPER_BOOKS.items()}
    books = {}
    for source_book in data["books"]:
        code = codes.get(source_book["name"])
        if code is None:
            continue  # deuterocanonical book
        verses = {}
        for chapter in source_book["chapters"]:
            for verse in chapter["verses"]:
                # "[1]" style footnote callers are left over in some files.
                text = clean_text(re.sub(r"\[\d+\]", "", verse["text"]))
                if text:
                    verses[(int(chapter["chapter"]), int(verse["verse"]))] = text
        if verses:
            # The book names in these files are English; localized names
            # come from the translation's "book_names" table.
            books[code] = {"name": None, "verses": verses, "titled": set()}
    return books


def parse_sefaria_json(path, book):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("license") != "Public Domain":
        raise BuildError(f"{path.name}: licence is '{data.get('license')}', "
                         "only public-domain texts may be bundled")
    verses = {}
    for chapter, chapter_verses in enumerate(data["text"], start=1):
        for verse, text in enumerate(chapter_verses, start=1):
            text = clean_text(XML_TAG_RE.sub("", text or ""))
            if text:
                verses[(chapter, verse)] = text
    return {book: {"name": None, "verses": verses, "titled": set()}}


OSIS_DROP_RE = re.compile(r"<(title|note)\b.*?</\1>", re.DOTALL)
XML_TAG_RE = re.compile(r"<[^>]+>")


def parse_sword_ztext(path, kjv_lengths):
    """Read a CrossWire zText module that uses the KJV versification.

    Each testament has three files: .bzz holds zlib-compressed blocks, .bzs
    lists the blocks (offset, compressed size, plain size) and .bzv has one
    entry per verse slot (block, offset in block, size). The slots follow
    the KJV versification: two headings per testament, one per book and one
    per chapter, each followed by its verses.
    """
    with zipfile.ZipFile(path) as archive:
        files = {Path(name).name: archive.read(name) for name in archive.namelist()}
    books = {}
    for prefix, codes in (("ot", BOOK_CODES[:39]), ("nt", BOOK_CODES[39:])):
        block_index, verse_index, data = (
            files[f"{prefix}.bzs"], files[f"{prefix}.bzv"], files[f"{prefix}.bzz"])
        blocks = {}

        def block(number):
            if number not in blocks:
                offset, size, _ = struct.unpack_from("<III", block_index, number * 12)
                blocks[number] = zlib.decompress(data[offset:offset + size])
            return blocks[number]

        slot = 2
        for code in codes:
            slot += 1
            verses = {}
            chapter = 1
            while (code, chapter) in kjv_lengths:
                slot += 1
                for verse in range(1, kjv_lengths[(code, chapter)] + 1):
                    number, start, size = struct.unpack_from("<IIH", verse_index, slot * 10)
                    slot += 1
                    raw = block(number)[start:start + size].decode("utf-8")
                    text = clean_text(html.unescape(
                        XML_TAG_RE.sub(" ", OSIS_DROP_RE.sub(" ", raw))))
                    if text:
                        verses[(chapter, verse)] = text
                chapter += 1
            if verses:
                books[code] = {"name": None, "verses": verses, "titled": set()}
        # Some modules have a few unused slots after the last verse.
        if slot * 10 > len(verse_index):
            raise BuildError(f"{path.name}: {prefix} index does not match the "
                             "KJV versification")
    return books


def load_bible(translation, kjv_lengths=None):
    """Load and merge all source files of a translation."""
    bible = {}
    for source in translation["sources"]:
        path = SOURCES_DIR / source["file"]
        if not path.exists():
            raise BuildError(
                f"missing source file {path}\n"
                f"  download it from {source['url']}\n"
                f"  or run: python3 tools/build_verses.py --download")
        if source["type"] == "usfm":
            books = parse_usfm_zip(path)
        elif source["type"] == "json":
            books = parse_scrollmapper_json(path)
        elif source["type"] == "sefaria":
            books = parse_sefaria_json(path, source["book"])
        else:
            books = parse_sword_ztext(path, kjv_lengths)
        for code, book in books.items():
            if "books" not in source or code in source["books"]:
                bible.setdefault(code, book)
    return bible


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

VERSE_MARKER_RE = re.compile(r"\{(\d+):(\d+)\}\s*")
FIRST_SENTENCE_RE = re.compile(r"^([^.]*\.)\s+(?=\S)")
# An optional one-letter word ("O SIGNORE") and the first longer word.
INITIAL_WORD_RE = re.compile(r"^((?:\w )?)([^\W\d_]{2,})\b")


def normal_initial_word(text):
    """'IL Signore' -> 'Il Signore', 'O SIGNORE, mia' -> 'O Signore, mia'."""
    match = INITIAL_WORD_RE.match(text)
    if not match or not match.group(2).isupper():
        return text
    return match.group(1) + match.group(2).capitalize() + text[match.end():]


def build_translation(translation, references, kjv):
    """Extract the references. Returns (books, verses, numbering, notes)."""
    kjv_lengths = chapter_lengths(kjv)
    bible = load_bible(translation, kjv_lengths)
    lengths = chapter_lengths(bible)
    numbering_rules = translation.get("numbering", {})
    name_overrides = translation.get("book_names", {})
    books = {}
    verses = {}
    numbering = {}
    problems = []
    notes = []

    for reference in references:
        key = reference_id(reference)
        book, chapter = reference[0], reference[1]
        if book not in bible:
            problems.append(f"{key}: book {book} is not in the source")
            continue

        local, handled = map_reference(numbering_rules, reference)
        if not handled and lengths.get((book, chapter)) != kjv_lengths[(book, chapter)]:
            problems.append(
                f"{key}: {book} {chapter} has {lengths.get((book, chapter))} verses, "
                f"the KJV has {kjv_lengths[(book, chapter)]}; check the verse and "
                f"add a 'numbering' rule")
        _, local_chapter, first, last = local
        # In a file squeezed into the KJV verse count, the last verse of a
        # renumbered chapter holds two verses; an excerpt must pick one.
        by_offset = local != reference and key not in numbering_rules.get("references", {})
        if (translation.get("squeezed") and by_offset
                and last >= lengths.get((book, local_chapter), 0)
                and key not in numbering_rules.get("excerpts", {})):
            problems.append(
                f"{key}: maps to the last verse of {book} {local_chapter}, "
                f"which is merged in this source; add an 'excerpts' rule")

        # A source with its own numbering must have as many more verses in
        # the chapter as the offset says, or the offset table is wrong for it.
        offset = numbering_rules.get("offsets", {}).get(book, {}).get(chapter)
        if (by_offset and offset is not None and not translation.get("squeezed")
                and lengths.get((book, local_chapter))
                != kjv_lengths[(book, chapter)] + offset):
            problems.append(
                f"{key}: {book} {local_chapter} has {lengths.get((book, local_chapter))} "
                f"verses, expected {kjv_lengths[(book, chapter)] + offset} "
                f"(KJV {kjv_lengths[(book, chapter)]} + offset {offset})")

        texts = []
        for verse in range(first, last + 1):
            text = bible[book]["verses"].get((local_chapter, verse))
            if not text:
                problems.append(f"{key}: {book} {local_chapter}:{verse} missing or empty")
            else:
                texts.append(text)
        titled_first = (book == "PSA" and first == 1
                        and chapter in kjv["PSA"]["titled"])

        # With verse markers, a Psalm title is what stands before the last
        # marker of verse 1 ("Title, {51:2} more title. {51:3} Text").
        title_removed = False
        if translation.get("verse_markers") and titled_first and texts:
            parts = VERSE_MARKER_RE.split(texts[0])
            if len(parts) > 1:
                notes.append(f"title removed from {key}: "
                             + VERSE_MARKER_RE.sub("", texts[0][:-len(parts[-1])]).strip())
                texts[0] = "{%s:%s} %s" % (parts[-3], parts[-2], parts[-1])
                title_removed = True
        text = " ".join(texts)

        # "{51:12}" at the start of a verse: its number in this translation.
        marked = None
        if translation.get("verse_markers"):
            markers = VERSE_MARKER_RE.findall(text)
            text = VERSE_MARKER_RE.sub("", text)
            if markers and len(markers) != last - first + 1:
                problems.append(f"{key}: {len(markers)} verse markers for "
                                f"{last - first + 1} verse(s)")
            elif markers:
                marked = f"{markers[0][0]}:{markers[0][1]}"
                if len(markers) > 1:
                    marked += f"-{markers[-1][1]}"

        excerpt = numbering_rules.get("excerpts", {}).get(key)
        if excerpt:
            mode, anchor = excerpt
            position = text.find(anchor)
            if position < 0:
                problems.append(f"{key}: excerpt text '{anchor}' not found in '{text}'")
            elif mode == "from":
                text = text[position:]
            else:
                text = text[:position]

        # A Psalm title printed at the start of verse 1 is not verse text.
        if (translation.get("psalm_titles") == "excerpt" and titled_first
                and not excerpt):
            problems.append(f"{key}: verse 1 of a Psalm with a title needs an "
                            f"'excerpts' rule: '{text[:60]}'")
        if (translation.get("psalm_titles") == "first_sentence"
                and titled_first and not title_removed and not excerpt):
            match = FIRST_SENTENCE_RE.match(text)
            if match:
                notes.append(f"title removed from {key}: {match.group(1)}")
                text = text[match.end():]
            else:
                problems.append(f"{key}: expected a Psalm title in '{text[:60]}'")

        if translation.get("initial_capitals"):
            text = normal_initial_word(text)
        for pattern, replacement in translation.get("cleanup", []):
            text = re.sub(pattern, replacement, clean_text(text))
        verses[key] = clean_text(text)

        name = name_overrides.get(book) or bible[book]["name"]
        if not name:
            problems.append(f"{key}: no book name for {book}")
        books[book] = name

        # Remember the local numbering where it differs from the KJV one, so
        # the widget shows the reference a reader of this translation expects.
        if key in numbering_rules.get("display", {}):
            numbering[key] = numbering_rules["display"][key]
        elif marked:
            numbering[key] = marked
        elif local != reference:
            numbering[key] = reference_id(local).split(".", 1)[1].replace(".", ":")

    if problems:
        raise BuildError(
            f"{translation['id']}: {len(problems)} problem(s):\n  "
            + "\n  ".join(problems))
    return books, verses, numbering, notes


def unusual_lengths(verses, kjv_verses):
    """References whose length, compared with the KJV, is far from typical.

    A cheap hint for numbering mistakes: a wrong verse usually has a
    different length than the right one.
    """
    ratios = {key: len(verses[key]) / len(kjv_verses[key]) for key in verses}
    typical = statistics.median(ratios.values())
    return sorted(key for key, ratio in ratios.items()
                  if not 0.6 <= ratio / typical <= 1.6)


def to_js(value):
    """Serialise to a JavaScript literal (JSON is a subset, plus two escapes)."""
    text = json.dumps(value, ensure_ascii=False, indent=4)
    return text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


GENERATED_HEADER = (
    ".pragma library\n"
    "// GENERATED FILE - do not edit by hand.\n"
    "// Created by tools/build_verses.py from tools/references.txt.\n"
)


def write_translation(translation, books, verses, numbering):
    ordered_books = {code: books[code] for code in BOOK_CODES if code in books}
    content = (
        GENERATED_HEADER
        + f"//\n// {translation['language']}: {translation['name']}\n"
        + f"// {translation['credit']}\n\n"
        + "// Localized book names, keyed by USFM book code.\n"
        + f"var books = {to_js(ordered_books)};\n\n"
        + "// Chapter:verse as numbered in this translation, only where it\n"
        + "// differs from the King James numbering used in the keys.\n"
        + f"var numbering = {to_js(numbering)};\n\n"
        + "// Verse text, keyed by reference id.\n"
        + f"var verses = {to_js(verses)};\n"
    )
    path = OUTPUT_DIR / f"{translation['id']}.js"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def write_reference_list(references, themes):
    content = (
        GENERATED_HEADER
        + "//\n// The daily references in day-of-year order: index 0 is January 1,\n"
        + "// index 59 is February 29 and index 365 is December 31.\n\n"
        + f"var list = {to_js([reference_id(r) for r in references])};\n\n"
        + "// Themed lists from tools/themes.txt. With a theme selected, day N\n"
        + "// shows entry N modulo the length of its list.\n"
        + "var themes = "
        + to_js([{"id": theme, "list": [reference_id(r) for r in theme_references]}
                 for theme, theme_references in themes.items()])
        + ";\n"
    )
    path = OUTPUT_DIR / "references.js"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def download_sources(translations):
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    for translation in translations:
        for source in translation["sources"]:
            path = SOURCES_DIR / source["file"]
            if path.exists():
                print(f"have      {source['file']}")
                continue
            print(f"download  {source['url']}")
            request = urllib.request.Request(
                source["url"], headers={"User-Agent": "dailybibleverse-build"})
            with urllib.request.urlopen(request, timeout=120) as response:
                path.write_bytes(response.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("ids", nargs="*", help="translation ids to build (default: all)")
    parser.add_argument("--download", action="store_true",
                        help="download missing source files, then build")
    parser.add_argument("--check", action="store_true",
                        help="print removed Psalm titles and verses whose "
                             "length differs unusually from the KJV")
    args = parser.parse_args()

    known = {translation["id"] for translation in TRANSLATIONS}
    unknown = set(args.ids) - known
    if unknown:
        parser.error(f"unknown translation id(s): {', '.join(sorted(unknown))}")
    selected = [t for t in TRANSLATIONS if not args.ids or t["id"] in args.ids]

    try:
        daily = read_references(REFERENCES_FILE)
        themes = read_themes(THEMES_FILE)
        # Every reference once: the daily ones, then those only in a theme.
        references = list(dict.fromkeys(
            daily + [r for theme in themes.values() for r in theme]))
        if args.download:
            download_sources(TRANSLATIONS[:1] + selected)
        # The KJV is always needed: it defines the verse numbering.
        kjv = load_bible(TRANSLATIONS[0])
        kjv_verses = build_translation(TRANSLATIONS[0], references, kjv)[1]
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"wrote {write_reference_list(daily, themes).name}: "
              f"{len(daily)} daily references, {len(themes)} themes, "
              f"{len(references)} references in all")
        for translation in selected:
            books, verses, numbering, notes = build_translation(
                translation, references, kjv)
            path = write_translation(translation, books, verses, numbering)
            longest = max(verses, key=lambda key: len(verses[key]))
            print(f"wrote {path.name}: {len(verses)} verses, {len(books)} books, "
                  f"{len(numbering)} renumbered, longest {longest} "
                  f"({len(verses[longest])} characters)")
            if args.check:
                for key, local in sorted(numbering.items()):
                    print(f"    renumbered {key} -> {local}")
                for note in notes:
                    print(f"    {note}")
                for key in unusual_lengths(verses, kjv_verses):
                    print(f"    unusual length {key}: {verses[key]}")
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
