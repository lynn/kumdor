# The Sword of Kumdor

Tools and scripts for translating PC-98 game "The Sword of Kumdor" into English.

![image](https://user-images.githubusercontent.com/16232127/205412881-681a7126-2d11-433f-a680-b4c623e60bfd.png)


## Files

* `The Sword of Kumdor.HDM` is the original disk image.
* `patch.py` makes a bunch of checks against it, and dumps and reinserts text.
* `corrupt.py` isn't really anything. It can create slightly-corrupted versions of the ROM. I used it to reverse-engineer the tutorial line data format.
* `tutorial.py` is a Tkinter app for editing the handwritten tutorial. It uses the `tutorial/tut*.json` files to remember translations for each page. Use the mouse or pen to draw lines.
  * Press `Z` to undo, `C` to copy a page from the original ROM, `J` to go to the next page, `1` for cyan pen, `2` for green pen.
  * After the final page, a patched ROM is written to `tutorial/output.hdm` and you can close the app.
