// SPDX-License-Identifier: GPL-2.0-or-later
//
// Configuration page "Appearance": font, colors, background, text effects
// and layout. Every cfg_ property maps to an entry in config/main.xml.

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Dialogs as Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.kquickcontrols as KQuickControls

KCM.SimpleKCM {
    id: page

    // Font and text
    property alias cfg_useThemeColors: useThemeColors.checked
    property string cfg_fontFamily
    property int cfg_fontWeight
    property alias cfg_fontSize: fontSize.value
    property alias cfg_referenceFontSize: referenceFontSize.value
    property alias cfg_verseBold: verseBold.checked
    property alias cfg_verseItalic: verseItalic.checked
    property alias cfg_referenceBold: referenceBold.checked
    property alias cfg_referenceItalic: referenceItalic.checked
    property alias cfg_textColor: textColor.color
    property alias cfg_referenceColor: referenceColor.color
    property alias cfg_textAlignment: textAlignment.currentIndex
    property alias cfg_lineSpacing: lineSpacing.value
    property alias cfg_letterSpacing: letterSpacing.value
    property alias cfg_secondFontScale: secondFontScale.value

    // Background
    property alias cfg_backgroundMode: backgroundMode.currentIndex
    property alias cfg_backgroundColor: backgroundColor.color
    property int cfg_backgroundOpacity
    property int cfg_cornerRadius

    // Text effects
    property alias cfg_shadowEnabled: shadowEnabled.checked
    property alias cfg_shadowColor: shadowColor.color
    property int cfg_shadowBlur
    property alias cfg_shadowOffset: shadowOffset.value
    property alias cfg_outlineEnabled: outlineEnabled.checked
    property alias cfg_outlineColor: outlineColor.color
    property alias cfg_fadeOnChange: fadeOnChange.checked

    // Layout
    property alias cfg_showReference: showReference.checked
    property alias cfg_referencePosition: referencePosition.currentIndex
    property alias cfg_referenceAlignment: referenceAlignment.currentIndex
    property alias cfg_maxTextWidth: maxTextWidth.value
    property alias cfg_padding: padding.value
    property alias cfg_quotationMarks: quotationMarks.checked
    property alias cfg_referenceDash: referenceDash.checked

    readonly property bool customBackground: backgroundMode.currentIndex === 3
    readonly property var alignmentNames: [i18n("Left"), i18n("Center"), i18n("Right")]

    Dialogs.FontDialog {
        id: fontDialog
        title: i18n("Choose Verse Font")
        onAccepted: {
            page.cfg_fontFamily = selectedFont.family;
            if (selectedFont.pointSize > 0) {
                fontSize.value = Math.round(selectedFont.pointSize);
            }
            // Bold and heavier go to the "Bold" box, lighter weights
            // (Light, Medium, ...) are kept as the normal weight.
            verseBold.checked = selectedFont.weight >= Font.Bold;
            if (selectedFont.weight < Font.Bold) {
                page.cfg_fontWeight = selectedFont.weight;
            }
            verseItalic.checked = selectedFont.italic;
        }
    }

    Kirigami.FormLayout {

        // --- Font and text -------------------------------------------------

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Font and Text")
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Font:")

            QQC2.Button {
                icon.name: "preferences-desktop-font"
                text: page.cfg_fontFamily || i18n("Plasma default font")
                onClicked: {
                    fontDialog.selectedFont = Qt.font({
                        family: page.cfg_fontFamily || Kirigami.Theme.defaultFont.family,
                        pointSize: fontSize.value,
                        weight: verseBold.checked ? Font.Bold : page.cfg_fontWeight,
                        italic: verseItalic.checked
                    });
                    fontDialog.open();
                }
            }
            QQC2.Button {
                icon.name: "edit-reset"
                text: i18n("Use Plasma Font")
                enabled: page.cfg_fontFamily !== ""
                onClicked: {
                    page.cfg_fontFamily = "";
                    page.cfg_fontWeight = Font.Normal;
                }
            }
        }

        QQC2.SpinBox {
            id: fontSize
            Kirigami.FormData.label: i18n("Verse size:")
            from: 6
            to: 96
            textFromValue: (value, locale) => i18nc("font size in points", "%1 pt", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.SpinBox {
            id: referenceFontSize
            Kirigami.FormData.label: i18n("Reference size:")
            from: 6
            to: 96
            textFromValue: (value, locale) => i18nc("font size in points", "%1 pt", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Verse style:")
            QQC2.CheckBox {
                id: verseBold
                text: i18n("Bold")
            }
            QQC2.CheckBox {
                id: verseItalic
                text: i18n("Italic")
            }
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Reference style:")
            QQC2.CheckBox {
                id: referenceBold
                text: i18n("Bold")
            }
            QQC2.CheckBox {
                id: referenceItalic
                text: i18n("Italic")
            }
        }

        QQC2.ComboBox {
            id: textAlignment
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Text alignment:")
            model: page.alignmentNames
        }

        QQC2.SpinBox {
            id: lineSpacing
            Kirigami.FormData.label: i18n("Line spacing:")
            from: 80
            to: 200
            stepSize: 5
            textFromValue: (value, locale) => i18nc("percentage", "%1%", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.SpinBox {
            id: letterSpacing
            Kirigami.FormData.label: i18n("Letter spacing:")
            from: -2
            to: 10
            textFromValue: (value, locale) => i18nc("length in pixels", "%1 px", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.SpinBox {
            id: secondFontScale
            Kirigami.FormData.label: i18n("Second translation size:")
            from: 50
            to: 100
            stepSize: 5
            textFromValue: (value, locale) => i18nc("percentage", "%1%", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.CheckBox {
            id: useThemeColors
            Kirigami.FormData.label: i18n("Colors:")
            text: i18n("Use Plasma theme colors")
        }

        KQuickControls.ColorButton {
            id: textColor
            Kirigami.FormData.label: i18n("Text color:")
            enabled: !useThemeColors.checked
            showAlphaChannel: true
            dialogTitle: i18n("Text Color")
        }

        KQuickControls.ColorButton {
            id: referenceColor
            Kirigami.FormData.label: i18n("Reference color:")
            enabled: !useThemeColors.checked
            showAlphaChannel: true
            dialogTitle: i18n("Reference Color")
        }

        // --- Background ----------------------------------------------------

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Background")
        }

        QQC2.ComboBox {
            id: backgroundMode
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Background:")
            model: [
                i18n("None (transparent)"),
                i18n("Plasma standard"),
                i18n("Plasma translucent (blurred)"),
                i18n("Custom color")
            ]
        }

        KQuickControls.ColorButton {
            id: backgroundColor
            Kirigami.FormData.label: i18n("Custom color:")
            enabled: page.customBackground
            dialogTitle: i18n("Background Color")
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Opacity:")
            enabled: page.customBackground
            QQC2.Slider {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                from: 0
                to: 100
                stepSize: 1
                value: page.cfg_backgroundOpacity
                onMoved: page.cfg_backgroundOpacity = Math.round(value)
            }
            QQC2.Label {
                text: i18nc("percentage", "%1%", page.cfg_backgroundOpacity)
            }
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Corner radius:")
            enabled: page.customBackground
            QQC2.Slider {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                from: 0
                to: 60
                stepSize: 1
                value: page.cfg_cornerRadius
                onMoved: page.cfg_cornerRadius = Math.round(value)
            }
            QQC2.Label {
                text: i18nc("length in pixels", "%1 px", page.cfg_cornerRadius)
            }
        }

        // --- Text effects --------------------------------------------------

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Text Effects")
        }

        QQC2.CheckBox {
            id: shadowEnabled
            Kirigami.FormData.label: i18n("Shadow:")
            text: i18n("Drop shadow")
        }

        KQuickControls.ColorButton {
            id: shadowColor
            Kirigami.FormData.label: i18n("Shadow color:")
            enabled: shadowEnabled.checked
            showAlphaChannel: true
            dialogTitle: i18n("Shadow Color")
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Shadow blur:")
            enabled: shadowEnabled.checked
            QQC2.Slider {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                from: 0
                to: 100
                stepSize: 1
                value: page.cfg_shadowBlur
                onMoved: page.cfg_shadowBlur = Math.round(value)
            }
            QQC2.Label {
                text: i18nc("percentage", "%1%", page.cfg_shadowBlur)
            }
        }

        QQC2.SpinBox {
            id: shadowOffset
            Kirigami.FormData.label: i18n("Shadow offset:")
            enabled: shadowEnabled.checked
            from: 0
            to: 20
            textFromValue: (value, locale) => i18nc("length in pixels", "%1 px", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.CheckBox {
            id: outlineEnabled
            Kirigami.FormData.label: i18n("Outline:")
            text: i18n("Outline the text")
        }

        KQuickControls.ColorButton {
            id: outlineColor
            Kirigami.FormData.label: i18n("Outline color:")
            enabled: outlineEnabled.checked
            dialogTitle: i18n("Outline Color")
        }

        QQC2.CheckBox {
            id: fadeOnChange
            Kirigami.FormData.label: i18n("Animation:")
            text: i18n("Fade when the verse changes")
        }

        // --- Layout --------------------------------------------------------

        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Layout")
        }

        QQC2.CheckBox {
            id: showReference
            Kirigami.FormData.label: i18n("Reference:")
            text: i18n("Show the reference")
        }

        QQC2.ComboBox {
            id: referencePosition
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Reference position:")
            enabled: showReference.checked
            model: [
                i18n("Below the verse"),
                i18n("Above the verse"),
                i18n("Inline, after the verse")
            ]
        }

        QQC2.CheckBox {
            id: referenceDash
            // An inline reference always has its own dash.
            enabled: showReference.checked && referencePosition.currentIndex !== 2
            text: i18n("Put a dash before the reference")
        }

        QQC2.ComboBox {
            id: referenceAlignment
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Reference alignment:")
            // An inline reference is part of the verse text.
            enabled: showReference.checked && referencePosition.currentIndex !== 2
            model: page.alignmentNames
        }

        QQC2.SpinBox {
            id: maxTextWidth
            Kirigami.FormData.label: i18n("Maximum text width:")
            from: 0
            to: 4000
            stepSize: 20
            textFromValue: (value, locale) => value === 0
                ? i18n("No limit") : i18nc("length in pixels", "%1 px", value)
            valueFromText: (text, locale) => parseInt(text) || 0
        }

        QQC2.SpinBox {
            id: padding
            Kirigami.FormData.label: i18n("Padding:")
            from: 0
            to: 200
            textFromValue: (value, locale) => i18nc("length in pixels", "%1 px", value)
            valueFromText: (text, locale) => parseInt(text)
        }

        QQC2.CheckBox {
            id: quotationMarks
            Kirigami.FormData.label: i18n("Quotation marks:")
            text: i18n("Put the verse in quotation marks")
        }
    }
}
