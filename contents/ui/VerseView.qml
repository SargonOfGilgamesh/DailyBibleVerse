// SPDX-License-Identifier: GPL-2.0-or-later
//
// Shows one verse (optionally in two translations) and its reference,
// styled by the Appearance settings. All settings are read through
// bindings, so changes apply immediately.

import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

Item {
    id: view

    property string verseText: ""
    property string referenceText: ""
    // [opening, closing] quotation marks of the translation's language.
    property var quotes: null
    // True for Hebrew and Arabic: "left" and "right" alignment swap sides,
    // so that "left" always means the side where a line starts.
    property bool rightToLeft: false
    // Font the translation asks for (a script style); empty for none. It
    // wins over the font setting, which would not have the script anyway.
    property string translationFont: ""
    property string secondTranslationFont: ""
    // The same verse in a second translation, shown under the first.
    // Empty: no second translation.
    property string secondVerseText: ""
    property var secondQuotes: null
    property bool secondRightToLeft: false
    // False in the panel popup, which already has its own background.
    property bool drawCustomBackground: true

    readonly property var cfg: Plasmoid.configuration

    // Values of the "reference position" setting.
    readonly property int positionBelow: 0
    readonly property int positionAbove: 1
    readonly property int positionInline: 2

    readonly property bool referenceInline: cfg.showReference
        && cfg.referencePosition === positionInline
    readonly property bool referenceAbove: cfg.showReference
        && cfg.referencePosition === positionAbove
    readonly property bool referenceBelow: cfg.showReference
        && cfg.referencePosition === positionBelow

    // --- Shown content -----------------------------------------------------

    // What is on screen right now. It follows the properties above, but
    // with a fade in between when the "fade" setting is on (see refresh()).
    property var shown: ({
        verseText: "", referenceText: "", quotes: null, rightToLeft: false,
        font: "", secondVerseText: "", secondQuotes: null,
        secondRightToLeft: false, secondFont: ""
    })
    property bool loaded: false

    readonly property bool hasSecond: shown.secondVerseText !== ""
    // Extra room between the two translations.
    readonly property real secondGap: Kirigami.Units.largeSpacing

    // The verse as displayed: optional quotation marks, optional reference.
    readonly property string displayText: {
        let text = cfg.quotationMarks ? quoted(shown.verseText, shown.quotes) : shown.verseText;
        if (referenceInline && shown.referenceText) {
            text += " — " + shown.referenceText;
        }
        return text;
    }
    readonly property string secondDisplayText: cfg.quotationMarks
        ? quoted(shown.secondVerseText, shown.secondQuotes) : shown.secondVerseText
    // The reference as displayed on its own line.
    readonly property string referenceLine: (cfg.referenceDash ? "— " : "") + shown.referenceText

    function applyContent() {
        shown = {
            verseText: verseText, referenceText: referenceText,
            quotes: quotes, rightToLeft: rightToLeft, font: translationFont,
            secondVerseText: secondVerseText, secondQuotes: secondQuotes,
            secondRightToLeft: secondRightToLeft, secondFont: secondTranslationFont
        };
    }

    // Bring the shown content up to date. Several properties change in the
    // same moment when the day or the translation changes, so the callers
    // go through Qt.callLater() and this runs once.
    function refresh() {
        if (loaded && cfg.fadeOnChange && visible && Kirigami.Units.longDuration > 0) {
            fade.restart();
        } else {
            fade.stop();
            applyContent();
            column.opacity = 1;
        }
    }

    onVerseTextChanged: Qt.callLater(refresh)
    onReferenceTextChanged: Qt.callLater(refresh)
    onSecondVerseTextChanged: Qt.callLater(refresh)

    Component.onCompleted: {
        applyContent();
        loaded = true;
    }

    // Fade out, swap the content, fade in. longDuration is 0 when the user
    // has turned animations off in System Settings.
    SequentialAnimation {
        id: fade
        NumberAnimation {
            target: column
            property: "opacity"
            to: 0
            duration: Kirigami.Units.longDuration
            easing.type: Easing.InOutQuad
        }
        ScriptAction {
            script: view.applyContent()
        }
        NumberAnimation {
            target: column
            property: "opacity"
            to: 1
            duration: Kirigami.Units.longDuration
            easing.type: Easing.InOutQuad
        }
    }

    // --- Style -------------------------------------------------------------

    readonly property string fontFamily: cfg.fontFamily || Kirigami.Theme.defaultFont.family
    readonly property color verseColor: cfg.useThemeColors
        ? Kirigami.Theme.textColor : cfg.textColor
    readonly property color referenceColor: cfg.useThemeColors
        ? Kirigami.Theme.disabledTextColor : cfg.referenceColor

    function quoted(text, pair) {
        const marks = (pair && pair.length === 2) ? pair : ["“", "”"];
        return marks[0] + text + marks[1];
    }

    // 0 left, 1 center, 2 right; mirrored for right-to-left text.
    function effectiveAlignment(setting, rtl) {
        return (rtl && setting !== 1) ? 2 - setting : setting;
    }

    // Alignment setting -> Text alignment flag.
    function alignmentFlag(setting, rtl) {
        const side = effectiveAlignment(setting, rtl);
        return side === 0 ? Text.AlignLeft : side === 2 ? Text.AlignRight : Text.AlignHCenter;
    }

    // Where the text block sits in the widget; follows the first translation.
    readonly property int blockSide: effectiveAlignment(cfg.textAlignment, shown.rightToLeft)

    // --- Size --------------------------------------------------------------

    // Width of the text block: the widget width minus padding, limited by
    // the "maximum text width" setting.
    readonly property real availableWidth: Math.max(0, width - 2 * cfg.padding)
    readonly property real textWidth: cfg.maxTextWidth > 0
        ? Math.min(availableWidth, cfg.maxTextWidth) : availableWidth

    // Height the content needs at the current width and full font size.
    readonly property real contentHeight: Math.ceil(heightProbe.implicitHeight)
        + (hasSecond ? Math.ceil(secondHeightProbe.implicitHeight) + column.spacing + secondGap : 0)
        + (referenceAbove ? referenceAboveText.implicitHeight + column.spacing : 0)
        + (referenceBelow ? referenceBelowText.implicitHeight + column.spacing : 0)

    implicitWidth: Kirigami.Units.gridUnit * 22
    implicitHeight: contentHeight + 2 * cfg.padding

    Layout.minimumWidth: Kirigami.Units.gridUnit * 10
    Layout.minimumHeight: Kirigami.Units.gridUnit * 4
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight

    // --- Custom background -------------------------------------------------

    // Drawn only in "Custom color" mode; the Plasma background modes are
    // handled by Plasmoid.backgroundHints in main.qml.
    Rectangle {
        anchors.fill: parent
        visible: view.drawCustomBackground && view.cfg.backgroundMode === 3
        color: Qt.rgba(view.cfg.backgroundColor.r, view.cfg.backgroundColor.g,
                       view.cfg.backgroundColor.b, view.cfg.backgroundOpacity / 100)
        radius: Math.min(view.cfg.cornerRadius, width / 2, height / 2)
    }

    // --- Text --------------------------------------------------------------

    // Invisible copies of the verses at their full font size. The visible
    // verses shrink to fit, so their own height cannot size the widget.
    Text {
        id: heightProbe
        visible: false
        width: column.width
        text: verse.text
        font: verse.font
        lineHeight: verse.lineHeight
        wrapMode: verse.wrapMode
    }
    Text {
        id: secondHeightProbe
        visible: false
        width: column.width
        text: secondVerse.text
        font: secondVerse.font
        lineHeight: secondVerse.lineHeight
        wrapMode: secondVerse.wrapMode
    }

    // A verse. It never clips: if the widget is too small, the font shrinks
    // until the whole text fits. `probe` is its full-size copy above.
    component VerseText: Text {
        property var host
        property var probe
        property bool rtl: false
        property string preferredFont: ""
        property real sizeFactor: 1

        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredHeight: Math.ceil(probe.implicitHeight)
        Layout.maximumHeight: Math.ceil(probe.implicitHeight)

        color: host.verseColor
        font.family: preferredFont || host.fontFamily
        font.weight: host.cfg.verseBold ? Font.Bold : host.cfg.fontWeight
        font.pointSize: Math.max(1, host.cfg.fontSize * sizeFactor)
        font.italic: host.cfg.verseItalic
        font.letterSpacing: host.cfg.letterSpacing
        lineHeight: host.cfg.lineSpacing / 100
        wrapMode: Text.Wrap
        horizontalAlignment: host.alignmentFlag(host.cfg.textAlignment, rtl)
        verticalAlignment: Text.AlignVCenter
        style: host.cfg.outlineEnabled ? Text.Outline : Text.Normal
        styleColor: host.cfg.outlineColor

        fontSizeMode: Text.Fit
        minimumPointSize: 6
    }

    // The reference line. An inline component cannot see the ids of this
    // file, so the view is handed in through `host`.
    component ReferenceText: Text {
        property var host

        Layout.fillWidth: true
        text: host.referenceLine
        color: host.referenceColor
        font.family: host.shown.font || host.fontFamily
        font.pointSize: host.cfg.referenceFontSize
        font.bold: host.cfg.referenceBold
        font.italic: host.cfg.referenceItalic
        font.letterSpacing: host.cfg.letterSpacing
        wrapMode: Text.Wrap
        horizontalAlignment: host.alignmentFlag(host.cfg.referenceAlignment, host.shown.rightToLeft)
        style: host.cfg.outlineEnabled ? Text.Outline : Text.Normal
        styleColor: host.cfg.outlineColor
    }

    ColumnLayout {
        id: column

        // The block sits on the side the text is aligned to.
        x: view.blockSide === 0 ? view.cfg.padding
            : view.blockSide === 2 ? view.width - view.cfg.padding - width
            : (view.width - width) / 2
        y: view.cfg.padding
        width: view.textWidth
        height: Math.max(0, view.height - 2 * view.cfg.padding)
        spacing: Kirigami.Units.smallSpacing

        // Drop shadow behind all text, for readability on any wallpaper.
        layer.enabled: view.cfg.shadowEnabled
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: view.cfg.shadowColor
            shadowBlur: view.cfg.shadowBlur / 100
            shadowHorizontalOffset: view.cfg.shadowOffset
            shadowVerticalOffset: view.cfg.shadowOffset
            blurMax: 32
            autoPaddingEnabled: true
        }

        // The two spacers keep verse and reference together in the middle
        // when the widget is taller than its content.
        Item {
            Layout.fillHeight: true
        }

        ReferenceText {
            id: referenceAboveText
            host: view
            visible: view.referenceAbove
        }

        VerseText {
            id: verse
            host: view
            probe: heightProbe
            rtl: view.shown.rightToLeft
            preferredFont: view.shown.font
            text: view.displayText
        }

        VerseText {
            id: secondVerse
            host: view
            probe: secondHeightProbe
            rtl: view.shown.secondRightToLeft
            preferredFont: view.shown.secondFont
            Layout.topMargin: view.secondGap
            sizeFactor: view.cfg.secondFontScale / 100
            text: view.secondDisplayText
            visible: view.hasSecond
        }

        ReferenceText {
            id: referenceBelowText
            host: view
            visible: view.referenceBelow
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
