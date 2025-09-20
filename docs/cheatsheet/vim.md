# Vim cheatsheet

## Save Gaining root
If you forgot to sudo:
```
:w !sudo tee %
```

## Disable selection by mouse (to copy)
```
:set mouse-=a
```

## Multiselection & replace
```
Ctrl^V
select (hjkl)
c - delete and insert (d to delete, I to insert)
ESC or Ctrl^[
```

## Useful shortcuts
Navigation:  
- `w` - jump to next word
- `b` - jump to previous word
- `e` - jump to the end of the current word
- `gg` - go to first line
- `G` - go to last line
- `0` - go to start of the line
- `$` - go to end of line
- `3w` - jump 3 words

Deletion:  
- `dd` - delete line
- `dw` - delete the word
- `x` - delete single character
- `D` - delete to end of line

Copy / Paste:
- `yy` - copy line
- `p` - paste below
- `P` - paste above

Edit:
- `o` - open a new line below
- `O` - open a new line above
- `u` - undo
- `Ctrl+r` - redo

Search:
- `/`, text, `Enter` - search forward
- `?`, text, `Enter` - search backward
- `n` - next occurence
- `N` - previous occurence

See [VIM Master](https://github.com/renzorlive/vimmaster)
