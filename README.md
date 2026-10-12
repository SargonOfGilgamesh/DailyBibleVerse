Daily Bible Verse

A Plasma 6 widget that shows a new Bible verse on your desktop every day. Works fully offline, with 18 public-domain translations in 16 languages.

Features
A new verse every day at midnight, the same for everyone on the same day
Optional themes (Hope, Love, Peace, Strength, and more)
Show two translations at once
Customizable font, colors, background, shadow, outline and layout
Right-click to copy the verse
Works on the desktop or in a panel

Requires Plasma 6.0 or newer.

Install

Right-click the desktop → Add Widgets… → Get New Widgets → search "Daily Bible Verse".

Or from a file:

kpackagetool6 -t Plasma/Applet -i dailybibleverse.plasmoid

If a language shows empty boxes, install a font for it (e.g. noto-fonts-cjk for Chinese and Korean).

Development

Test with plasmoidviewer (from plasma-sdk):

plasmoidviewer -a ./dailybibleverse

Verse data is already included. To rebuild it after changing tools/references.txt or tools/themes.txt:

python3 tools/build_verses.py --download
python3 tools/build_verses.py --check

Only add public-domain translations.
