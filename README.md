# Daily Bible Verse

A KDE Plasma 6 desktop widget (plasmoid) that shows one Bible verse and its
reference, and changes it every day at local midnight.

- **Same verse for everyone.** The verse is chosen from a fixed list of 366
  references by the day of the year, so every user sees the same verse on the
  same date. Switching language shows the same verse in another translation.
- **Themes.** Instead of the daily list, a theme can be chosen: Hope, Trust,
  Love, Family, Peace, Strength and courage, Comfort, Wisdom, Gratitude and
  praise, Forgiveness and grace, Prayer, Joy. Each has 31 verses, one per
  day, and starts again when all have been shown. With the same theme,
  everyone still sees the same verse on the same date. In all, 590 verses
  are bundled in every translation.
- **Fully offline.** All verse text is bundled. The widget makes no network
  requests.
- **Eighteen public-domain translations** in sixteen languages (see
  [Credits](#credits)). The default follows the system language and falls back
  to the King James Version.
- **Two translations at once.** A second translation can be shown under the
  first, for example Hebrew with English below.
- **Survives sleep.** The date is checked once a minute, so the verse is
  correct after suspend or a clock change.
- **Configurable look.** Font, sizes, line and letter spacing, colors,
  alignment, background (none, Plasma standard, Plasma translucent, custom
  color), drop shadow, outline, reference position, maximum text width,
  padding and quotation marks. All settings apply immediately.
- **Copy the verse.** Right-click the widget and choose *Copy Verse*.
- **Soft fade** when the verse or the translation changes (can be turned
  off, and is off when animations are disabled in System Settings).
- **Works in a panel.** There it shows an icon that opens the verse in a
  popup.

Requires Plasma 6.0 or later. No dependencies beyond Plasma 6, KDE Frameworks 6
and Qt 6.

## Package layout

```
dailybibleverse/
├── metadata.json
├── contents/
│   ├── ui/        main.qml, VerseView.qml, configGeneral.qml, configAppearance.qml
│   ├── config/    main.xml (settings schema), config.qml (settings pages)
│   └── code/
│       ├── logic.js          verse selection, no UI
│       ├── translations.js   registry of translations
│       └── verses/           generated data, one file per translation
├── tools/
│   ├── build_verses.py       generates contents/code/verses/
│   ├── references.txt        the 366 daily references
│   └── themes.txt            the themed verse lists
├── LICENSE
└── README.md
```

## Testing

Run these from the directory that contains `dailybibleverse/`:

```
plasmoidviewer -a ./dailybibleverse
plasmoidviewer -a ./dailybibleverse -l floating -f planar
```

The first shows the widget as on a desktop. The second shows it floating at
its preferred size. To see the panel form (icon plus popup):

```
plasmoidviewer -a ./dailybibleverse -l topedge -f horizontal
```

`plasmoidviewer` is part of the `plasma-sdk` package.

### Fast test loop from another machine

When you edit on one machine and test on another, copy the package with
`rsync` over SSH instead of zipping it. Only changed files are sent, and
`--delete` keeps the copy on the test machine exact:

```
rsync -az --delete --exclude tools/sources/ --exclude __pycache__/ \
    dailybibleverse/ user@testmachine:dailybibleverse/
```

Then run `plasmoidviewer -a ~/dailybibleverse` on the test machine. In the
viewer, the widget's settings open with the toolbar button that shows
sliders (left of *Configure Containment*); there is no right-click menu.

## Installing

Install for the current user:

```
kpackagetool6 -t Plasma/Applet -i ./dailybibleverse
```

Upgrade an installed copy:

```
kpackagetool6 -t Plasma/Applet -u ./dailybibleverse
```

Remove it:

```
kpackagetool6 -t Plasma/Applet -r com.github.Sargonofgilgamesh.dailybibleverse
```

Plasma keeps loaded widgets in memory. After an upgrade, restart the shell to
see the new version:

```
systemctl --user restart plasma-plasmashell
```

Then add the widget with right-click on the desktop → *Enter Edit Mode* →
*Add Widgets…* → *Daily Bible Verse*.

## Generating the verse data

The generated files in `contents/code/verses/` are included, so this step is
only needed after changing `tools/references.txt` or adding a translation.
The script needs Python 3.8 or later and nothing else.

### 1. Get the source files

Either let the script download them:

```
python3 tools/build_verses.py --download
```

or download them yourself and put them, with exactly these file names, in
`dailybibleverse/tools/sources/` (create the directory):

| File | Download from |
|---|---|
| `eng-kjv2006_usfm.zip` | https://ebible.org/Scriptures/eng-kjv2006_usfm.zip |
| `engwebp_usfm.zip` | https://ebible.org/Scriptures/engwebp_usfm.zip |
| `deu1912_usfm.zip` | https://ebible.org/Scriptures/deu1912_usfm.zip |
| `spaRV1909_usfm.zip` | https://ebible.org/Scriptures/spaRV1909_usfm.zip |
| `fraLSG_usfm.zip` | https://ebible.org/Scriptures/fraLSG_usfm.zip |
| `ita1885_usfm.zip` | https://ebible.org/Scriptures/ita1885_usfm.zip |
| `arb-vd_usfm.zip` | https://ebible.org/Scriptures/arb-vd_usfm.zip |
| `hboWLC_usfm.zip` | https://ebible.org/Scriptures/hboWLC_usfm.zip |
| `hebsg_usfm.zip` | https://ebible.org/Scriptures/hebsg_usfm.zip |
| `Swe1917.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/Swe1917.json |
| `DutSVV.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/DutSVV.json |
| `PorAlmeida1911.zip` | https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/PorAlmeida1911.zip |
| `russyn_usfm.zip` | https://ebible.org/Scriptures/russyn_usfm.zip |
| `cmn-cu89s_usfm.zip` | https://ebible.org/Scriptures/cmn-cu89s_usfm.zip |
| `cmn-cu89t_usfm.zip` | https://ebible.org/Scriptures/cmn-cu89t_usfm.zip |
| `PolGdanska.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/PolGdanska.json |
| `FinPR.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/FinPR.json |
| `KorRV.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/KorRV.json |
| `Peshitta.json` | https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/Peshitta.json |

The Aramaic translation also needs 30 Targum files from Sefaria, one per
book (`sefaria_*.json`). Use `--download` for those; their addresses are in
`ARAMAIC_SOURCES` in `tools/build_verses.py`. The build refuses a Sefaria
file whose licence field is not "Public Domain".

Do not unpack the zip files. `tools/sources/` is not part of the widget and
must not go into the published package.

### 2. Build

From the `dailybibleverse/` directory:

```
python3 tools/build_verses.py
```

This rewrites `contents/code/verses/references.js` and one file per
translation. Useful variants:

```
python3 tools/build_verses.py sv_1917 de_luther1912   # only these translations
python3 tools/build_verses.py --check                 # also print a review list
```

`--check` lists every renumbered reference, every removed Psalm title and
every verse whose length is unusual compared with the King James Version.
Read that list after changing references: it is how numbering mistakes are
found.

The build stops with an error if a verse is missing, or if a referenced
chapter has a different number of verses than in the King James Version and
no numbering rule covers it.

### Changing the references

`tools/references.txt` holds the 366 references, one per line, in day order
(line 1 is January 1, line 60 is February 29). They use King James numbering
and 3-letter USFM book codes. A reference covers at most three verses and no
verse may appear twice.

### Themes

`tools/themes.txt` holds the themed lists: a `[id]` line starts a theme, the
references after it belong to it. A reference may be in several themes and
in `references.txt` too, but only once per theme. On day N of the year the
widget shows entry N modulo the length of the list, so lists may have any
length.

To add a theme, add a section, run the build script with `--check`, and add
the theme's display name to `themeNames` in `contents/ui/configGeneral.qml`.
Every new reference must be found in all translations; where a translation
numbers the verse differently, the build stops and says which numbering rule
is missing.

### Adding a translation

1. Add an entry to `TRANSLATIONS` in `tools/build_verses.py` (source file,
   names, numbering rules) and run the script with `--check`.
2. Add one `.import` line and one entry to `contents/code/translations.js`.
   The first entry of a language is the one "Automatic" picks; an entry can
   list `territories` (as the traditional Chinese one does) to be preferred
   for those regions.

Only add translations that are in the public domain, and record the source in
the entry's `credit` and in the table below.

## Publishing on the KDE Store

A `.plasmoid` file is a zip archive with `metadata.json` at its root. From
inside the `dailybibleverse/` directory:

```
zip -r ../dailybibleverse-1.0.0.plasmoid . \
    -x "tools/sources/*" -x "*__pycache__*" -x ".git*" -x "*.png" -x "*.plasmoid"
```

Check the archive before uploading:

```
unzip -l ../dailybibleverse-1.0.0.plasmoid | head
kpackagetool6 -t Plasma/Applet -i ../dailybibleverse-1.0.0.plasmoid
```

Upload it at https://store.kde.org in the category *Plasma 6 Widgets*, with
licence GPL-2.0-or-later. Raise `Version` in `metadata.json` for every update.

## Notes on the texts

- **Verse numbering.** Translations do not all number verses alike. Where a
  translation differs from the King James Version (mostly Psalms whose title
  counts as verse 1), the widget shows the numbering of that translation, for
  example Psalm 51:10 appears as *Psaume 51:12* in French.
- **Psalm titles.** Titles such as "A Psalm of David" are left out. The
  exception is Hebrew, where a short title is part of verse 1 itself.
- **Hebrew.** Vowel points are kept, cantillation marks are removed.
- **Swedish and Dutch.** The source files merge the last two verses of some
  Psalms; the build script cuts out the wanted verse (`excerpts` in
  `build_verses.py`).
- **Psalm 13.** The Hebrew numbering joins verses 5 and 6 of the King James
  Version, so the reference is 13:5-6 and shows as 13:6 in the translations
  that follow the Hebrew numbering.
- **Dutch and Portuguese.** The names of the Hebrew letters that head the
  verses of acrostic poems ("Aleph.", "Beth.") are removed.
- **Portuguese.** The 1911 Almeida text uses the spelling of its time
  (*Christo*, *elle*) and comes from a scanned book: a few verses lack their
  final full stop.
- **Russian.** The Synodal translation numbers most Psalms one lower than
  the King James Version (Psalm 23 is *Псалом 22*); the widget shows the
  Russian numbering.
- **Chinese.** Both scripts are included. With "Automatic", the traditional
  script is chosen for the system regions TW, HK and MO, the simplified
  script otherwise.
- **Default look.** White text in *Red Hat Mono* (regular).
  The font is not bundled: where it is not installed, the system's default
  font is used instead. White text suits a dark background; with a light
  Plasma theme choose another color or background on the Appearance page.
- **Hebrew and Arabic** are shown in the Plasma font while the font setting
  is the built-in Red Hat Mono: the monospace fonts a system substitutes
  for these scripts space the letters badly. A font you choose yourself is
  used for them too.
- **Fonts.** The widget uses the fonts installed on the system. If a
  translation shows as empty boxes, a font for that script is missing:
  install for example `noto-fonts-cjk` for Chinese and Korean, or a Noto
  Sans Syriac font for the Aramaic New Testament.
- **Korean.** Psalm titles are joined to verse 1 in the source without
  punctuation; the build script cuts them off (`excerpts`).
- **Aramaic.** No complete Aramaic Bible in the public domain was found, so
  this entry is put together from three texts:
  - Old Testament: the Targums (Onkelos, Jonathan and the Targums to the
    Writings), in Hebrew letters with vowel points. They are ancient Jewish
    Aramaic translations and often paraphrase: a verse can be several times
    longer than in other translations.
  - New Testament: the Syriac Peshitta (Classical Syriac), in Syriac letters
    without vowel marks. It is shown in the Eastern (Assyrian, Madnhaya)
    letter style when the font "Noto Sans Syriac Eastern" is installed and
    the font setting is "Plasma default"; otherwise in whatever Syriac font
    the system has. This is not the modern Assyrian language: the only
    Assyrian Neo-Aramaic Bible found (eBible.org `aii`, New Testament and
    Psalms) is under copyright with a non-commercial licence.
  - No Targum exists for Daniel and Nehemiah. Those verses are shown in
    their original language: Daniel 3:17-18 is Aramaic in the original,
    Nehemiah 8:10 and Daniel 12:3 are Hebrew. So on two days of the year
    the "Aramaic" text is Hebrew.
  - Book names are in Syriac letters (for example ܝܘܚܢܢ for John). They
    were typed by hand and should be checked by a native reader.
  The Syriac Peshitta Old Testament exists in digital form (ETCBC), but
  only under a non-commercial licence, so it is not used.
- The texts are otherwise reproduced as found in the sources. Only markup,
  footnotes and headings are removed.

## Credits

All bundled texts are in the public domain.

| Language | Translation | Source | Status |
|---|---|---|---|
| English | King James Version (1769) | eBible.org, `eng-kjv2006` | Public domain |
| English | World English Bible | eBible.org, `engwebp` | Public domain ("World English Bible" is a trademark of eBible.org) |
| Swedish | Bibeln 1917 (1917 års kyrkobibel) | scrollmapper/bible_databases, `Swe1917` (from the CrossWire module, text from Projekt Runeberg) | Public domain |
| German | Luther 1912 | eBible.org, `deu1912` | Public domain |
| Spanish | Reina-Valera 1909 | eBible.org, `spaRV1909` | Public domain |
| French | Louis Segond 1910 | eBible.org, `fraLSG` | Public domain |
| Dutch | Statenvertaling (1637) | scrollmapper/bible_databases, `DutSVV` (from the CrossWire module) | Public domain |
| Italian | Diodati (1641, edition of 1885) | eBible.org, `ita1885` | Public domain |
| Portuguese | João Ferreira de Almeida, edition of 1911 | CrossWire Bible Society, SWORD module `PorAlmeida1911` | Text in the public domain; module distributed under the GPL |
| Hebrew | Westminster Leningrad Codex (Old Testament) | eBible.org, `hboWLC` | Public domain |
| Hebrew | Salkinson-Ginsburg Hebrew New Testament | eBible.org, `hebsg` | Public domain |
| Arabic | Smith & Van Dyck (1865) | eBible.org, `arb-vd` | Public domain |
| Aramaic | Targum Onkelos, Targum Jonathan, Targums to the Writings (Old Testament) | Sefaria, versions "Onkelos …", "Mikraot Gedolot", "Wikisource Aramaic Targum to Chronicles" | Public domain |
| Aramaic | Syriac Peshitta, British and Foreign Bible Society 1905 (New Testament) | scrollmapper/bible_databases, `Peshitta` (from the CrossWire module) | Public domain |
| Russian | Synodal translation (1876) | eBible.org, `russyn` | Public domain |
| Polish | Biblia Gdańska (1632, edition of 1881) | scrollmapper/bible_databases, `PolGdanska` (from the CrossWire module) | Public domain |
| Finnish | Pyhä Raamattu (1933/1938) | scrollmapper/bible_databases, `FinPR` (from the CrossWire module) | Public domain |
| Chinese | Union Version with new punctuation (和合本), simplified and traditional | eBible.org, `cmn-cu89s`, `cmn-cu89t` | Public domain |
| Korean | Korean Revised Version (개역한글, 1952/1961) | scrollmapper/bible_databases, `KorRV` (from the CrossWire module, text from Wikisource) | Public domain |

Sources: [eBible.org](https://ebible.org),
[scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases),
[CrossWire Bible Society](https://www.crosswire.org),
[Sefaria](https://www.sefaria.org).

"Public domain" is the status stated by the publisher of each source file.

## Licence

The widget code and the build script are licensed under the GNU General
Public License, version 2 or (at your option) any later version. See
`LICENSE`. The Bible texts are in the public domain.

## Checklist before publishing

Display
- [ ] The verse and reference show on the desktop, wrap, and are never cut off.
- [ ] Making the widget very small shrinks the text instead of clipping it.
- [ ] A long verse (set the date to a day with a three-verse passage) still fits.
- [ ] In a panel the widget is an icon; clicking it opens the verse in a popup.

Day change
- [ ] The verse changes within a minute after local midnight.
- [ ] The verse is correct after suspending before midnight and resuming after.
- [ ] February 29 and March 1 show different verses in a leap year, and
      March 1 shows the same verse in a normal year.

Translations
- [ ] With "Automatic", the translation matches the system language; an
      unsupported language gives the King James Version.
- [ ] Every translation in the list shows text, with a localized book name.
- [ ] Hebrew and Arabic read right to left with correct letter shaping and
      vowel marks in the chosen font; the reference looks right.
- [ ] Switching translation keeps the same verse.
- [ ] Choosing a theme changes the verse; "All" brings the daily verse back;
      the theme's verse changes at midnight like the daily one.
- [ ] A second translation shows under the first; Hebrew over English keeps
      each text in its own direction; "None" removes it again.
- [ ] Two long verses in a small widget shrink instead of being cut off.
- [ ] Russian, Chinese and Korean show without missing-glyph boxes.
- [ ] Aramaic: an Old Testament day shows Hebrew letters, a New Testament
      day shows Syriac letters (needs a Syriac font).

Settings
- [ ] Every option on the Appearance page changes the widget right after
      *Apply*, without restarting Plasma.
- [ ] A fresh widget shows white text in Red Hat Mono (or the
      system font where Red Hat Mono is missing).
- [ ] The font dialog opens and its choice is kept, including a weight such
      as Light or Medium; *Use Plasma Font* switches to the system font.
- [ ] All four background modes work; opacity and corner radius work in
      "Custom color".
- [ ] With "Use Plasma theme colors", the text follows a switch between a
      light and a dark global theme.
- [ ] Shadow and outline are readable on a bright and on a busy wallpaper.
- [ ] Reference below, above, inline and hidden all look right.
- [ ] Line spacing, letter spacing and the dash before the reference apply.
- [ ] Changing the translation fades the text; with the fade option off it
      switches at once.
- [ ] On the real desktop, right-click → *Copy Verse* puts the verse and
      reference on the clipboard (the viewer has no right-click menu).
- [ ] Settings survive logging out and in.

Package
- [ ] `plasmoidviewer` prints no errors that mention `dailybibleverse`.
- [ ] The `.plasmoid` has `metadata.json` at its root and contains no
      `tools/sources/`, screenshots or `__pycache__`.
- [ ] Installing the `.plasmoid` with `kpackagetool6` on a clean user works.
- [ ] `Version` in `metadata.json` is correct, and the Id is the one you want
      to keep: it cannot change later without users losing their settings.
- [ ] The KDE Store page lists the translations and their public-domain status.
