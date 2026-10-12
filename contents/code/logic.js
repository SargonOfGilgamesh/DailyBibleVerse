.pragma library
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Verse selection logic of the Daily Bible Verse widget.
//
// Everything here is a pure function without any UI or data import, so it
// can be reasoned about (and tested) on its own.

// Days before the first day of each month in a leap year.
var DAYS_BEFORE_MONTH = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];

// Position of a date in a 366-day year: 0 = January 1, 59 = February 29,
// 365 = December 31. February 29 always owns slot 59, so a calendar date maps
// to the same slot in leap years and in normal years (which skip slot 59).
// Uses the local time zone of the Date object.
function dayIndex(date) {
    return DAYS_BEFORE_MONTH[date.getMonth()] + date.getDate() - 1;
}

// "2026-03-07" for the local calendar day. Used to detect a day change.
function dateKey(date) {
    function pad(number) {
        return number < 10 ? "0" + number : "" + number;
    }
    return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate());
}

// The reference id (e.g. "JHN.3.16") for a date. `references` is the list of
// 366 daily ids in day order, or the shorter list of a theme, which is then
// walked through again and again. The same date and list give the same id
// for everyone.
function referenceIdForDate(date, references) {
    return references[dayIndex(date) % references.length];
}

// "PSA.23.1-3" -> { book: "PSA", chapter: "23", verses: "1-3" }
function parseReferenceId(referenceId) {
    var parts = referenceId.split(".");
    return { book: parts[0], chapter: parts[1], verses: parts[2] };
}

// Human-readable reference, e.g. "Johannes 3:16" or "Psalm 23:1–3".
//   books:     localized book names keyed by book code
//   numbering: optional "chapter:verses" overrides keyed by reference id, for
//              translations that number a verse differently from the KJV
function formatReference(referenceId, books, numbering) {
    var parsed = parseReferenceId(referenceId);
    var numbers = (numbering && numbering[referenceId]) || (parsed.chapter + ":" + parsed.verses);
    var name = (books && books[parsed.book]) || parsed.book;
    return name + " " + numbers.replace("-", "–");
}

// Pick the translation for a locale name such as "sv_SE" or "de". An entry
// that lists the territory in `territories` wins (Chinese: "TW" selects the
// traditional script); otherwise the first registry entry whose language
// code matches, otherwise `fallbackId`.
function translationIdForLocale(localeName, translations, fallbackId) {
    var parts = String(localeName || "").split(/[_.@-]/);
    var language = parts[0].toLowerCase();
    var territory = (parts[1] || "").toUpperCase();
    var match = "";
    for (var i = 0; i < translations.length; ++i) {
        var translation = translations[i];
        if (translation.languageCode !== language) {
            continue;
        }
        if (territory && translation.territories
                && translation.territories.indexOf(territory) >= 0) {
            return translation.id;
        }
        if (!match) {
            match = translation.id;
        }
    }
    return match || fallbackId;
}
