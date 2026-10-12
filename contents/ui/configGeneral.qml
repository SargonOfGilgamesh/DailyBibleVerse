// SPDX-License-Identifier: GPL-2.0-or-later
//
// Configuration page "General": choice of translation.

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

import "../code/translations.js" as Translations

KCM.SimpleKCM {
    id: page

    // Translation id; empty means "follow the system language".
    property string cfg_translation
    // Translation id of the second translation; empty means none.
    property string cfg_secondTranslation
    // Theme id; empty means the 366 daily verses.
    property string cfg_theme

    // Display names of the themes in tools/themes.txt. A theme without a
    // name here is listed under its id.
    readonly property var themeNames: ({
        hope: i18n("Hope"),
        trust: i18n("Trust"),
        love: i18n("Love"),
        family: i18n("Family"),
        peace: i18n("Peace"),
        strength: i18n("Strength and courage"),
        comfort: i18n("Comfort"),
        wisdom: i18n("Wisdom"),
        gratitude: i18n("Gratitude and praise"),
        forgiveness: i18n("Forgiveness and grace"),
        prayer: i18n("Prayer"),
        joy: i18n("Joy")
    })

    // ComboBox entries: `firstText` for the empty id, then every translation.
    function translationModel(firstText) {
        const entries = [{ text: firstText, value: "" }];
        for (const translation of Translations.list) {
            entries.push({
                text: i18nc("language: translation name", "%1: %2",
                            translation.language, translation.name),
                value: translation.id
            });
        }
        return entries;
    }

    Kirigami.FormLayout {
        QQC2.ComboBox {
            id: translationBox
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Translation:")

            textRole: "text"
            valueRole: "value"
            model: page.translationModel(i18n("Automatic (system language)"))

            Component.onCompleted: currentIndex = Math.max(0, indexOfValue(page.cfg_translation))
            onActivated: page.cfg_translation = currentValue
        }

        QQC2.ComboBox {
            id: themeBox
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Theme:")

            textRole: "text"
            valueRole: "value"
            model: {
                const entries = [{ text: i18n("All verses (one for every day of the year)"), value: "" }];
                for (const theme of Translations.themes) {
                    entries.push({
                        text: i18nc("theme name (number of verses)", "%1 (%2 verses)",
                                    page.themeNames[theme.id] || theme.id, theme.list.length),
                        value: theme.id
                    });
                }
                return entries;
            }

            Component.onCompleted: currentIndex = Math.max(0, indexOfValue(page.cfg_theme))
            onActivated: page.cfg_theme = currentValue
        }

        QQC2.ComboBox {
            id: secondTranslationBox
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            Kirigami.FormData.label: i18n("Second translation:")

            textRole: "text"
            valueRole: "value"
            model: page.translationModel(i18n("None"))

            Component.onCompleted: currentIndex = Math.max(0, indexOfValue(page.cfg_secondTranslation))
            onActivated: page.cfg_secondTranslation = currentValue
        }

        QQC2.Label {
            Layout.maximumWidth: Kirigami.Units.gridUnit * 20
            text: i18n("A theme shows one of its verses each day and starts again when all have been shown. The second translation shows the same verse under the first one.")
            wrapMode: Text.Wrap
            font: Kirigami.Theme.smallFont
            opacity: 0.7
        }
    }
}
