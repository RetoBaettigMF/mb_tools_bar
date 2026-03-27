# Document Formatter

## Overview
This is a command line tool that takes a text (plain text or markdown) and fills it into a pre-existing Microsoft Word Template.
It uses AI to analyze the Word Template and the input text and then fills in the Template as good as it can by using the existing structure and chapters and adding if needed

## AI Model
- Use the specified openrouter model and key from the .env file in the parent directory as AI model.

## Additional requirements
- Add it to the git repo in the parent dir, commit and push regularly
- Test the solution
- Add a Readme.md

## Interface

Command line options:
- Template file name
- Output file name (or generate one)
- Input file name and/or input on the command line

Console output
- Give good information about what you did, what files you used, if everything was fine or also descriptive error information

## Test
- use "Protokoll.dotx"
- Use this text input:
```
ERFA CRA 19.3.26 - Protokoll
Donnerstag, 19. März 2026
 
Teilnehmer
Hans Meier
Marcel Müller
REto Bättig
 
 
Protokoll
•	Neue Teilnehmer stellen sich kurz vor:
o	Daniel Sandner, asdf AG, KMU mit 70 Personen in Gossau, Entwickeln Heissfolienprägemaschinen, B&R Steuerungen, Linux HMI. Dani ist verantwortlich für Automatisierung mit 2 SW-Entwicklern und 2 Elektroplanern. Thema völlig neu, 0 Berührungspunkte bis jetzt. Ist auch im Praxiszirkel von NextIndustries dabei
o	Daniel Huber, Minimax AG, 2000MA, Maschinenbau für Druckweiterverarbeitung, vor allem Bücher. Produktionslinien bis smart Factories, letztes Jahr noch Firma Hunkeler übernommen. Viele Steuerungsgenerationen. Interessiert an Austausch, Learnings austauschen, sich gegenseitig inspirieren. Ist auch am Praxiszirkel von NextIndustries dabei. Daniel ist für Automatisierungsplattform, Vernetzung, Kundenportal und OT Security verantwortlich.
 
 
Diskussion Prioritäten
•	Daniel Sandner hätte gerne die Risikoanalyse höher klassifiziert
•	Emmanuel Hauser hat gestern gelernt, dass auch Rollendefinition zu Klassifizierung gehören würde
•	Oliver Lang: Klassifizierung ist aus seiner Sicht klar, aber er kann das nicht "legally binding" angeben gegenüber Upper Management. Wenn es höher wäre, müsste es extern deklariert werden.
•	Wer wäre nicht in der Default-Kategorie?
o	Nach eigenen Einschätzungen niemand, aber wie können wir sicher sein?
o	Wie viel Dokumentation muss ich für die Selbstdeklaration machen?
o	Bei Ramon ist es "erledigt", aber er hat kein Dokument dazu. Es ist ein "Gefühl", auch bei Felix Kramer und Daniel Rüeffer.
o	Allgemeine Frage: Wie viel Dokumentation braucht es? Reto könnte Caroline Gaul versuchen, dazu einzuladen und sie um ein Feedback z.B. zu einer von uns erarbeiteten Vorlage zu geben. Am besten, wenn wir schon konkrete Beispiele und Fragen dazu haben, z.B. "Reicht diese Vorlage aus oder braucht es mehr", "Was mache ich, wenn meine GL fragt, was sie machen müssen für eine "Legally Binding Aussage""
•	Ev. könnte man auch die Rollenverteilung zusammen mit der Meldepflicht in ein ERFA nehmen?
 
Idee Emmanuel
•	Jeder bereitet sich vor zum Thema Klassifizierung und Rollenverteilung (soweit es geht)
•	Dann "sharen" an Meeting, austauschen, diskutieren
•	Daniel Sandner fände die Idee auch gut
•	Ist im Sinne des ERFA gemäss Reto. Konkrete Dokumente, Konkret: "Wie habe ich es gemacht", konkreter Austausch.
 
Jörn hätte noch ein anderes Thema:
•	Wie können wir aus dem "Pain" auch Profit schlagen und etwas herausholen?
•	Gute Idee, wird unterwegs angeschaut und nebenbei
 
Nächtes Meeting: 1.4. 9:00-10:00
 

Fabian bringt noch den Hinweis, dass PR-EN Norm (ISO 21434) herausgekommen ist , diese ist sehr nahe an Automobilindustrie. Man könnte dann davon auch lernen und Vorlagen übernehmen. Stichtag war Juli 2024. => Allgemein gute Idee, von anderen Normen zu lernen bzw. zu kopieren.
 
Weitere Idee Emanuel
•	Teilnahmebestätigung machen an ERFA für alle Firmen
•	Zeigt auch ein Puzzlestein auf, dass Firma das Thema seriös angegangen ist
•	Cudos kann das machen!
 

```
