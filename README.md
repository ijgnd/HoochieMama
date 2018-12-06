# HoochieMama
AnkiAddon: Randomize Queue

Title is in reference to Seinfeld, no relations to the current slang term.

"'Randomization of sub-decks on the v1 scheduler' in an add-on for 2.0 means to have the best part of the V2 scheduler (imo) while you can sync with AnkiDroid and use all the add-ons that haven't been ported yet." -ijgnd

## About:
This is the back-ported _fillRev method from the v2 scheduler with some added features from serenityNow and works on both v1 and v2 scheduler. It allows randomization of sub-decks on the v1 scheduler without switching to the v2 scheduler.

Note: V2 randomizes sub-decks but uses max reviews from the parent deck. This creates an imbalance where users with large amount of over due low priority cards could potentially end up focusing on one sub-deck. A typical example: say Leaves, Clouds, Knots, and Math with a max review of 5 each and a cap at 20 for the parent deck. If the user have a large amount of overdue, say 25 each, the V2 scheduler would grab 20 cards sorted by dues resulting in 13 Leaves, 4 Clouds, 2 Knots, and 1 Math.

### Enhancements:
- Focus on today's dues first. So for the previous example, it would be 4 dues today from each subdeck follow by any extra over dues from yesterday or later.
- Customize sorting by dues, intervals, or reps.
- Enforce sub-deck limits.


## Configs:
To prevent conflicts with other similar addons, this must be activated in preferences.

Note: If you have serenityNow installed, please update to the latest version or disable it. If you have any other addons that also monkey patches _fillRev, disable them as well. (e.g. <a href="https://ankiweb.net/shared/info/3731265543">Change Order of Review Cards in Regular Decks</a>)

<img src="https://github.com/lovac42/HoochieMama/blob/master/screenshots/prefmenu.jpg?raw=true">


## Bugs/Features:
In the event where subdecks have a large amount of overdues and both parent and child are capped at a small number, there is a mis-count issue with the V1 scheduler. The deck browser would report a review total calculated from each subdeck limit (V1), but in the overview and with the actual reviews, the numbers are based on the limit from the parent deck (V2). This discrepancy may cause some confusion, but it is only a cosmetic difference. Patching this will break compatibility with other popular addons, so I decided to leave this as it is. With the addon <a href="https://ankiweb.net/shared/info/877182321">Enhanced Main Window</a> or similar plugins, you should be able to get a ballpark of the actual review count making any fixes unnecessary.

