# slidegen

As the name may partially imply, **slidegen** generates song slides as images - out of a plain text input file - intended for use with [OBS]() to livestream a typical (contemporary) sunday church service.

This program is also intended to be used in conjuction with [ssync](https://github.com/noahvogt/ssync), which is basically a wrapper script that automatically syncs a local copy with the remote slide repository, removes the old obs slides and lets the user interactively choose the new slides with a smart fuzzy finder.

Standalone use of **slidegen** is possible and can sure fit other use cases.

## Why this program exists

To add song slides to OBS or similar software as input sources, there exist the following obvious options:

- generating song slides via a text or presentation documents, exported in printable form and converted to images afterwards
- generating images through image manipulation or designing software and export to images

Both of these processes have *major downsides*: They are hard to automate, take a long time to create the slides, have very limited to support for bulk operations on the song repository (like wanting to change the theme and layout of all slides or changing the metadata shared by a lot of songs) and maintaing is a lot harder because of bad portability and complex source files.

The only upside they have is that can be more intuitive for unexperienced computer users, but changing a text file template and uploading to a remote storage should not be too hard to manage and worth it as it has *none* of the above mentioned downsides.

## Usage

### Commandline Interface
As mentionened above, this program is not made to be executed directly. Therefore the commandline interface is not yet fully stable. Generally, the syntax is as follows

    ./slidegen.py SRC_PATH DEST_DIR PROMPT_INPUT

with `SRC_PATH` beeing the path to the song plain text file, `DEST_DIR` the output directory where the slide image file output is placed and `PROMPT_INPUT`

Here a short example:

    ./slidegen.py "../songrepo/Stille Nacht.txt" "~/Documents/Song Slides 1"

### Source File Layout

The file is divided into two parts that are divided with at least one `\n` character and an arbitrary amount of empty lines:
- the metadata header (top of the file)
- the text body (bottom of the file)

#### Metadata Header

As the top of the file are these five metadata entries. We call them *metadata strings*:
- title
- book
- text
- melody
- structure

Their value and semantics can be pretty much whatever you want, except for an empty string.

Example:


#### Text Body

### Configuration

As of now, all Configuration is handled via constants in `slidegen.py`, which will change in the future. See the roadmap below.

## Roadmap

These are some issues that will be addressed by future development:

- prevent all crashes:
    - safe `PROMPT_INPUT` parsing
    - handle possibly incorrect or insensible configurations
- prevent long and many lines from cutting off text in the slide
- integrating [ssync](https://github.com/noahvogt/ssync) into this (and hence a single) repo
- provide ssync with the song structure, display it to the user and prevent him from entering a prompt that would crash slidegen
- better packaging and modularisation
- add more optional metadata strings

## Licensing

**slidegen** is free (as in “free speech” and also as in “free beer”) Software. It is distributed under the GNU General Public License v3 (or any later version) - see the accompanying LICENSE file for more details.
