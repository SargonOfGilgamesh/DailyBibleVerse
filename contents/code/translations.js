.pragma library
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Registry of the bundled Bible translations.
//
// To add a translation:
//   1. Generate its data file with tools/build_verses.py.
//   2. Add an ".import" line for it below.
//   3. Add one entry to `list`.
// QML can only import script files by a fixed name, which is why step 2 is
// needed in addition to the registry entry.

.import "verses/references.js" as References
.import "verses/en_kjv.js" as EnKjv
.import "verses/en_web.js" as EnWeb
.import "verses/sv_1917.js" as Sv1917
.import "verses/de_luther1912.js" as DeLuther1912
.import "verses/es_rv1909.js" as EsRv1909
.import "verses/fr_lsg1910.js" as FrLsg1910
.import "verses/nl_sv.js" as NlSv
.import "verses/it_diodati.js" as ItDiodati
.import "verses/pt_almeida1911.js" as PtAlmeida1911
.import "verses/he_wlc.js" as HeWlc
.import "verses/ar_vandyck.js" as ArVandyck
.import "verses/arc_targum_peshitta.js" as ArcTargumPeshitta
.import "verses/ru_synodal.js" as RuSynodal
.import "verses/pl_gdanska.js" as PlGdanska
.import "verses/fi_1938.js" as Fi1938
.import "verses/zh_union_simplified.js" as ZhUnionSimplified
.import "verses/zh_union_traditional.js" as ZhUnionTraditional
.import "verses/ko_krv.js" as KoKrv

// The 366 daily reference ids in day-of-year order (see logic.js).
var references = References.list;

// Themed lists: [{ id: "hope", list: [reference ids] }, ...].
var themes = References.themes;

// The reference list for a theme id; the daily list for "" or an unknown id.
function referencesForTheme(themeId) {
    for (var i = 0; i < themes.length; ++i) {
        if (themes[i].id === themeId) {
            return themes[i].list;
        }
    }
    return references;
}

// Used when the system language has no bundled translation.
var defaultId = "en_kjv";

// id            stable id, stored in the widget configuration
// name          translation name
// language      language name, written in that language
// languageCode  ISO 639-1 code matched against the system locale; the first
//               entry of a language is its default translation
// territories   optional: territory codes of the system locale for which
//               this entry is preferred over the first one of its language
// fontFamily    optional: font always used for this translation. Here: the
//               Eastern (Assyrian) style of the Syriac letters instead of
//               Estrangela.
// systemFont    optional, true: while the font setting is the built-in
//               default (a monospace Latin font), show this translation in
//               the Plasma font instead. Hebrew and Arabic look wrong in the
//               monospace fonts the system would substitute.
// rightToLeft   true for right-to-left scripts
// quotes        [opening, closing] quotation marks used in that language
// module        the generated data file the entry comes from
// books, numbering, verses: the data of that module
var list = [
    {
        id: "en_kjv",
        name: "King James Version",
        language: "English",
        languageCode: "en",
        rightToLeft: false,
        quotes: ["\u201c", "\u201d"],
        module: "verses/en_kjv.js",
        books: EnKjv.books,
        numbering: EnKjv.numbering,
        verses: EnKjv.verses
    },
    {
        id: "en_web",
        name: "World English Bible",
        language: "English",
        languageCode: "en",
        rightToLeft: false,
        quotes: ["\u201c", "\u201d"],
        module: "verses/en_web.js",
        books: EnWeb.books,
        numbering: EnWeb.numbering,
        verses: EnWeb.verses
    },
    {
        id: "sv_1917",
        name: "Bibeln 1917",
        language: "Svenska",
        languageCode: "sv",
        rightToLeft: false,
        quotes: ["\u201d", "\u201d"],
        module: "verses/sv_1917.js",
        books: Sv1917.books,
        numbering: Sv1917.numbering,
        verses: Sv1917.verses
    },
    {
        id: "de_luther1912",
        name: "Luther 1912",
        language: "Deutsch",
        languageCode: "de",
        rightToLeft: false,
        quotes: ["\u201e", "\u201c"],
        module: "verses/de_luther1912.js",
        books: DeLuther1912.books,
        numbering: DeLuther1912.numbering,
        verses: DeLuther1912.verses
    },
    {
        id: "es_rv1909",
        name: "Reina-Valera 1909",
        language: "Español",
        languageCode: "es",
        rightToLeft: false,
        quotes: ["\u00ab", "\u00bb"],
        module: "verses/es_rv1909.js",
        books: EsRv1909.books,
        numbering: EsRv1909.numbering,
        verses: EsRv1909.verses
    },
    {
        id: "fr_lsg1910",
        name: "Louis Segond 1910",
        language: "Français",
        languageCode: "fr",
        rightToLeft: false,
        quotes: ["\u00ab\u00a0", "\u00a0\u00bb"],
        module: "verses/fr_lsg1910.js",
        books: FrLsg1910.books,
        numbering: FrLsg1910.numbering,
        verses: FrLsg1910.verses
    },
    {
        id: "nl_sv",
        name: "Statenvertaling",
        language: "Nederlands",
        languageCode: "nl",
        rightToLeft: false,
        quotes: ["\u201c", "\u201d"],
        module: "verses/nl_sv.js",
        books: NlSv.books,
        numbering: NlSv.numbering,
        verses: NlSv.verses
    },
    {
        id: "it_diodati",
        name: "Diodati",
        language: "Italiano",
        languageCode: "it",
        rightToLeft: false,
        quotes: ["\u00ab", "\u00bb"],
        module: "verses/it_diodati.js",
        books: ItDiodati.books,
        numbering: ItDiodati.numbering,
        verses: ItDiodati.verses
    },
    {
        id: "pt_almeida1911",
        name: "Almeida 1911",
        language: "Português",
        languageCode: "pt",
        rightToLeft: false,
        quotes: ["\u201c", "\u201d"],
        module: "verses/pt_almeida1911.js",
        books: PtAlmeida1911.books,
        numbering: PtAlmeida1911.numbering,
        verses: PtAlmeida1911.verses
    },
    {
        id: "he_wlc",
        name: "Leningrad Codex + Salkinson-Ginsburg NT",
        language: "עברית",
        languageCode: "he",
        systemFont: true,
        rightToLeft: true,
        quotes: ["\u201c", "\u201d"],
        module: "verses/he_wlc.js",
        books: HeWlc.books,
        numbering: HeWlc.numbering,
        verses: HeWlc.verses
    },
    {
        id: "ar_vandyck",
        name: "Van Dyck",
        language: "العربية",
        languageCode: "ar",
        systemFont: true,
        rightToLeft: true,
        quotes: ["\u00ab", "\u00bb"],
        module: "verses/ar_vandyck.js",
        books: ArVandyck.books,
        numbering: ArVandyck.numbering,
        verses: ArVandyck.verses
    },
    {
        id: "arc_targum_peshitta",
        name: "Targum + Peshitta",
        language: "Aramaic",
        languageCode: "arc",
        fontFamily: "Noto Sans Syriac Eastern",
        rightToLeft: true,
        quotes: ["\u201c", "\u201d"],
        module: "verses/arc_targum_peshitta.js",
        books: ArcTargumPeshitta.books,
        numbering: ArcTargumPeshitta.numbering,
        verses: ArcTargumPeshitta.verses
    },
    {
        id: "ru_synodal",
        name: "Синодальный перевод",
        language: "Русский",
        languageCode: "ru",
        rightToLeft: false,
        quotes: ["\u00ab", "\u00bb"],
        module: "verses/ru_synodal.js",
        books: RuSynodal.books,
        numbering: RuSynodal.numbering,
        verses: RuSynodal.verses
    },
    {
        id: "pl_gdanska",
        name: "Biblia Gdańska",
        language: "Polski",
        languageCode: "pl",
        rightToLeft: false,
        quotes: ["\u201e", "\u201d"],
        module: "verses/pl_gdanska.js",
        books: PlGdanska.books,
        numbering: PlGdanska.numbering,
        verses: PlGdanska.verses
    },
    {
        id: "fi_1938",
        name: "Pyhä Raamattu 1933/1938",
        language: "Suomi",
        languageCode: "fi",
        rightToLeft: false,
        quotes: ["\u201d", "\u201d"],
        module: "verses/fi_1938.js",
        books: Fi1938.books,
        numbering: Fi1938.numbering,
        verses: Fi1938.verses
    },
    {
        id: "zh_union_simplified",
        name: "和合本 (简体)",
        language: "中文",
        languageCode: "zh",
        rightToLeft: false,
        quotes: ["\u300c", "\u300d"],
        module: "verses/zh_union_simplified.js",
        books: ZhUnionSimplified.books,
        numbering: ZhUnionSimplified.numbering,
        verses: ZhUnionSimplified.verses
    },
    {
        id: "zh_union_traditional",
        name: "和合本 (繁體)",
        language: "中文",
        languageCode: "zh",
        territories: ["TW", "HK", "MO"],
        rightToLeft: false,
        quotes: ["\u300c", "\u300d"],
        module: "verses/zh_union_traditional.js",
        books: ZhUnionTraditional.books,
        numbering: ZhUnionTraditional.numbering,
        verses: ZhUnionTraditional.verses
    },
    {
        id: "ko_krv",
        name: "개역한글",
        language: "한국어",
        languageCode: "ko",
        rightToLeft: false,
        quotes: ["\u201c", "\u201d"],
        module: "verses/ko_krv.js",
        books: KoKrv.books,
        numbering: KoKrv.numbering,
        verses: KoKrv.verses
    }
];

// Position of a translation id in `list`, or -1.
function indexOf(id) {
    for (var i = 0; i < list.length; ++i) {
        if (list[i].id === id) {
            return i;
        }
    }
    return -1;
}

// The registry entry for an id; falls back to the default translation so the
// widget keeps working if a configured translation is removed later.
function byId(id) {
    var index = indexOf(id);
    return list[index >= 0 ? index : indexOf(defaultId)];
}
