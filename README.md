```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

class Person:
    def __init__(self, name: str, pronouns: list, occupation: str, languages_spoken: list):
        self.name = name
        self.pronouns = pronouns
        self.occupation = occupation
        self.languages_spoken = languages_spoken
        
    def greet(self):
        print(f"Hello, I'm {self.name}! Thanks for dropping by, hope you find some of my work useful.")

me = Person(
    name="Richard Mwewa",
    pronouns=["He", "Him", "His"],
    occupation="Computer Programmer",
    languages_spoken=["English", "iciBemba", "chiNyanja"]
)

me.greet()
```
