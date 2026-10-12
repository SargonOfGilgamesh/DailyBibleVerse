// SPDX-License-Identifier: GPL-2.0-or-later
//
// Daily Bible Verse - root item of the plasmoid.
//
// Chooses today's verse, keeps it up to date across midnight and suspend,
// and shows it through VerseView (directly on the desktop, or in a popup
// behind an icon when the widget sits in a panel).

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

import "../code/logic.js" as Logic
import "../code/translations.js" as Translations

PlasmoidItem {
    id: root

    // --- Translation -------------------------------------------------------

    // The configured translation. An empty setting means "automatic": the
    // translation matching the system language, English KJV if there is none.
    readonly property string translationId: Plasmoid.configuration.translation
        || Logic.translationIdForLocale(Qt.locale().name, Translations.list, Translations.defaultId)
    readonly property var translation: Translations.byId(translationId)

    // Optional second translation, shown under the first. Null when none is
    // set, when it is the same as the first, or when its id is unknown.
    readonly property var secondTranslation: {
        const id = Plasmoid.configuration.secondTranslation;
        return (id && id !== translation.id && Translations.indexOf(id) >= 0)
            ? Translations.byId(id) : null;
    }

    // The font setting as shipped (config/main.xml).
    readonly property string builtInFont: "Red Hat Mono"

    // Font a translation needs instead of the configured one; "" for none.
    // See `fontFamily` and `systemFont` in translations.js.
    function fontFor(translation) {
        if (!translation) {
            return "";
        }
        if (translation.fontFamily) {
            return translation.fontFamily;
        }
        return (translation.systemFont && Plasmoid.configuration.fontFamily === builtInFont)
            ? Kirigami.Theme.defaultFont.family : "";
    }

    // --- Today's verse -----------------------------------------------------

    // Local calendar day currently shown, as "yyyy-mm-dd".
    property string shownDate: ""
    // Reference id of the verse for that day, e.g. "JHN.3.16".
    property string referenceId: ""

    readonly property string verseText: referenceId ? translation.verses[referenceId] : ""
    readonly property string referenceText: referenceId
        ? Logic.formatReference(referenceId, translation.books, translation.numbering) : ""

    readonly property string secondVerseText: (referenceId && secondTranslation)
        ? secondTranslation.verses[referenceId] : ""

    // The list today's verse is taken from: the 366 daily references, or
    // the list of the theme chosen in the settings.
    readonly property var referenceList:
        Translations.referencesForTheme(Plasmoid.configuration.theme)
    onReferenceListChanged: showVerseFor(new Date())

    function showVerseFor(date) {
        shownDate = Logic.dateKey(date);
        referenceId = Logic.referenceIdForDate(date, referenceList);
    }

    // Switch to today's verse if the calendar day has changed.
    function checkDate() {
        const today = new Date();
        if (Logic.dateKey(today) !== shownDate) {
            showVerseFor(today);
        }
    }

    // Polling once a minute instead of one long timer to midnight: a timer
    // does not advance while the computer sleeps, a date comparison does.
    Timer {
        interval: 60 * 1000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.checkDate()
    }

    // --- Presentation ------------------------------------------------------

    readonly property bool inPanel: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
        || Plasmoid.formFactor === PlasmaCore.Types.Vertical

    // On the desktop the verse is shown directly. In a panel the default
    // compact representation (the widget icon) opens the verse in a popup.
    preferredRepresentation: inPanel ? compactRepresentation : fullRepresentation

    // Background setting: 0 none, 1 Plasma standard, 2 Plasma translucent,
    // 3 custom color (drawn by VerseView on top of no Plasma background).
    Plasmoid.backgroundHints: {
        switch (Plasmoid.configuration.backgroundMode) {
        case 0:
        case 3:
            return PlasmaCore.Types.NoBackground;
        case 2:
            return PlasmaCore.Types.TranslucentBackground;
        default:
            return PlasmaCore.Types.StandardBackground;
        }
    }

    // --- Copy to clipboard -------------------------------------------------

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("Copy Verse")
            icon.name: "edit-copy"
            onTriggered: root.copyVerse()
        }
    ]

    // The verse(s), then the reference with the translation name.
    function copyVerse() {
        let text = verseText;
        if (secondVerseText) {
            text += "\n" + secondVerseText;
        }
        text += "\n" + referenceText + " (" + translation.name + ")";
        clipboard.text = text;
        clipboard.selectAll();
        clipboard.copy();
        clipboard.text = "";
    }

    // QML has no clipboard object; a hidden TextEdit can copy its selection.
    TextEdit {
        id: clipboard
        visible: false
    }

    toolTipMainText: referenceText
    toolTipSubText: verseText

    fullRepresentation: VerseView {
        verseText: root.verseText
        referenceText: root.referenceText
        quotes: root.translation.quotes || null
        rightToLeft: root.translation.rightToLeft
        translationFont: root.fontFor(root.translation)
        secondVerseText: root.secondVerseText
        secondQuotes: root.secondTranslation ? root.secondTranslation.quotes : null
        secondRightToLeft: root.secondTranslation ? root.secondTranslation.rightToLeft : false
        secondTranslationFont: root.fontFor(root.secondTranslation)
        drawCustomBackground: !root.inPanel
    }
}
