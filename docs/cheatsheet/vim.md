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
