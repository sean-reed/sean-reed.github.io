Title: SimTalk Syntax Highlighting for the Web
Date: 2024-08-22 20:20
Category: Plant Simulation
Tags: simtalk, plant simulation, programming, python, pelican
Slug: simtalk-syntax-highlights-with-pygments
Authors: Sean Reed
Summary: A new SimTalk syntax highlighting plugin for the Pygments Python library.

When implementing simulation models of complex systems there is always the need to include some, and often a lot, of code to program the logic that gives the simulation entities the desired behavior. For users of the Siemens Tecnomatix Plant Simulation tool, that primarily means writing code in the SimTalk language. I say primarily because Version 2404 released this year added the capability for Python scripts to be added to models. One of my plans for this blog is to write about simulation modelling in Plant Simulation and, as part of that, I want to share SimTalk code samples. However, I couldn't find any tool available for syntax highlighting of SimTalk code on the web, something that I consider necessary for good readability. As a niche language with a small user base (to my knowledge it used only within the Plant Simulation tool), this maybe isn't surprising.

The static site generator that this blog is built with, [Pelican](https://getpelican.com/), is packaged with a Python-based library called [Pygments](https://pygments.org/) to provide syntax highlighting. This library, used by thousands of websites including some big ones like Wikipedia, supports hundreds of programming languages, none of which are SimTalk. Fortunately, it is possible to add support for another language by writing a custom lexer. A lexer is a program that converts code (or, more generally, text) into meaningful lexical tokens like keywords, comments, declarations, and operators. So after a few hours of [consulting the Pygments docs](https://pygments.org/docs/lexerdevelopment/), writing regular expressions, debugging, and testing I had syntax highlighting working for SimTalk.

I have packaged it as a plugin so all you need to do is install it with pip (or whichever Python package manager you use) and it will be detected automatically by Pygments and made available alongside all the languages it already supports. You can find the installation instructions and source code in the [GitHub repository](https://github.com/sean-reed/pygments-simtalk/) here.

And finally, here are some examples of SimTalk code highlighted with this Pygments SimTalk plugin:

#### Example 1

    :::simtalk
    param width:length, height:length, depth:length
    /* Method that adds a cuboid to the "deco" graphic group 
    with dimensions (height, width, length) and the color of wood. */

    var cube := _3D.getGraphic("deco").createCuboid([height, width, depth])
    cube.MaterialActive := true
    cube.MaterialDiffuseColor :=  makeRGBValue(222, 184, 135)  // Wood color.

#### Example 2

    :::simtalk
    /* Release the circuit board from the source only
    once the buffer has less than 3 items */
    waituntil Buffer.NumMU < 3
    -- Enter the circuit board into the table.
    var row: integer
    row := CircuitBoards.getColumnYDim(1) + 1
    CircuitBoards["circuitBoard", row] := @
    CircuitBoards["location", row] := ?
    CircuitBoards["entered", row] := EventController.SimTime
    @.move -- Move the board onto successor.

Now we just need Siemens to add a dark mode to the Plant Simulation code editor ([related forum post](https://community.sw.siemens.com/s/question/0D54O00006FL6bgSAD/er-9907151-dark-mode-theme-for-the-simtalk-editor))!