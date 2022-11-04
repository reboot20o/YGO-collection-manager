# YGO-Collection-Manager

A GUI tool to track your collection for the Yu-Gi-Oh! trading card game. Card information is
sourced using the [YGOPRODECK API](https://ygoprodeck.com/api-guide/).

## Installation

To install, clone the repository

```bash
git clone https://github.com/reboot20o/YGO-collection-manager.git
```

For dependencies, see `requirements.txt` in assets directory.

## Usage

### Add to collection

To launch the GUI, run `main.py`. To add cards to your collection, you must first select a 
set to add from the drop-down list located on the bottom left. This list contains every set 
printed for the TCG, including special editions and promotional cards. To filter the list, 
select the option *show only main sets*. After selecting the set to add, click the button 
*Add set to collection*.

After adding a set to the collection, the drop-down list on the top left will update. 
Selecting that set will populate the tree view with all the cards from that set.
Below the tree view, there is a summary that tells you how many cards from the set you own,
how many unique cards you own, and how many unique cards are available in the set.
Selecting a card from the tree view will populate the detailed card view on the right with
associated card data. 

To add a card to your collection, select the chosen card from the tree view. If the last 
column of the tree view is blank, you must select the set the card belongs to from the 
options included in the text box below the card art. Then specify how many copies you own by 
typing in the entry field under the **Owned:** label or use the arrows. To save the changes, 
click the button *Save edits*. If everything was done correctly, a pop-up will appear asking
for confirmation.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you 
would like to change.

Please make sure to update tests as appropriate.