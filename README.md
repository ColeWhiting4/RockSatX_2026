# Virginia Tech RockSat-X 2026 Project.

---
# Key Points
- STICK TO USER MANUAL

# Etiquette.

- [_**Don't track junk files.**_](#dont-track-junk-files)
- [_**Don't track chunky files.**_](#dont-track-chunky-files)
- _**Think about usability when designing.**_

---
# Action Items
#### Design Stage
- [ ] Aluminium/Plywood Mock-Up of Deck Plate and Expierement.
- [ ] Design for Easy Access Remove Before Flight (RBF) Pins.
- [ ] Design for Function Indicatiors for Power Functions.
- [ ] Main Material List (One System of Measurement).
- [ ] Full 3D Printed Payload.
- [ ] Desgin Mechanial Test Beds for Each Main Actuation.
- [ ] Finite Element Analysis.

#### Build Stage
- [ ] Integation of Function Indicators (Lights/Buzzers).
- [ ] Instal RBF Inhibits and Tags.
- [ ] Build Test Beds and Run Actuation Testing.

#### End of Project Testing
- [ ] Full Sequence Test.
- [ ] Full Walk Around Inspection.
- [ ] Summer Testing Personel Breifing.
- [ ] Locktight/Hotglue/Secure Fasteners.
- [ ] Vibration Test.
- [ ] Create Inventory Sheet for Expierement Shipping Container.
- [ ] Summer Testing Procedures Checksheets.

---

## Don't Track Junk Files.

When you add files for Git to track,
it will mean that other people will have access to those files when you push your work to GitHub,

_**BUT NOT ALL FILES SHOULD BE TREATED EQUAL**_.

This means you _SHOULD NOT BE PUSHING FILES OF THE FOLLOWING_:
  - ❌ Backup files.
  - ❌ Cache files.
  - ❌ Auto-generated temporary files.
  - ❌ Build artifacts.
  - ❌ Debug info.
  - ❌ Personal settings/configurations.
  - ❌ Any binary data that you do not understand.

Some examples of things that might be _OK_ to track through version control:

- ✅ Source code.
- ✅ CAD parts, assemblies, materials, and such.
- ✅ 3D models like STEP, STL, etc.

Remember,
Kind engineers are the most productive engineers.
Take some time to look at the files you are going to be pushing to GitHub.

> [!TIP]
> Let's say you opened SolidWorks and started to make a thingmajig.
> After you feel like you have reached a good checkpoint,
> you decide to save your progress so far with the GitHub Desktop GUI.
> The GUI lists all the files that it sees that aren't currently being tracked;
> things like `my_new_part.sldprt`, `my_new_thing.sldasm`, `.workspace_settings`.
>
> The first two files are obviously the thing you've been working on,
> so you should be tracking those with version control,
> but what about `.workspace_settings`?
> You opened the file in NotePad and see that it seems to keep track of stuff like your window layout and what theme you're currently using.
> Should this file be tracked with version control?
> 
> **NO!**
> This file is an example of a _user configuration_ file.
> This file is so that
> when you reopen SolidWorks again,
> it looks exactly like where you left it.
> But other people shouldn't have to care about how you like your windows and panels to be laid out in SolidWorks!
>
> The bare minimum that is needed for other people to contribute to your SolidWorks part/assembly should just be the necessary ones;
> nothing more, nothing less.

> [!IMPORTANT]
> If you're unsure whether or not something should be tracked through Git or not,
> just ask!
> 
> In the event that a junk file is accidentally added to the repository,
> this can always be cleaned up later on.
> If a file was mistaken for junk but was actually critical,
> the file can always be added later on.
>
> Remember,
> the point of this etiquette is so that we can be kind to each other and not clutter the project repository,
> very much like you wouldn't want to clutter up a guest's house.

## Don't Track Chunky Files.

When you track a file with Git,
be wary of its file size.
This doesn't really matter for certain things like source code,
where even if there were a hundred thousand lines of code in this whole project,
this would only roughly amount to `100,000 * 100 bytes = 10 megabytes` of space, assuming 100 bytes per line.
However, for things like 3D models,
especially uncompressed formats like STEP and STL,
a complicated model might be on the order of 50 megabytes or larger.
If this is the case,
see if there's a way to trim down the fat
(e.g., reducing the complexity of the STEP model by opening your favorite CAD program and hide components and then re-export).

Why?
Because you should be kind to the other people here.
When you upload chunky files,
this means when they perform a fetch on the repository,
they'll be forced to download all your chunky files.
Don't waste their time and storage if you can.
