# Game Submission Guide

Submit one game folder to this repo with a pull request. The folder needs a lowercase name, `index.html` at the top, `thumbnail.png` and `meta.json`, and the game must run with no internet. Do the five steps in order. If you built your game with Claude, read [Built with Claude](#built-with-claude-or-another-ai-tool) in Step 1 and skip the other tools.

**Contents:** [What you hand in](#what-you-hand-in) · [Rules](#rules-every-game-must-follow) · [Step 1: Export](#step-1-export-your-game) · [Step 2: Thumbnail](#step-2-make-thumbnailpng) · [Step 3: meta.json](#step-3-write-metajson) · [Step 4: Test](#step-4-test-it-in-the-arcade) · [Step 5: Submit](#step-5-submit-with-a-pull-request) · [Checklist](#final-checklist) · [Troubleshooting](#troubleshooting)

## What you hand in

One folder, named `lastname-game-title`, with your game's start page called `index.html` sitting directly inside it.

```
okafor-astro-dodge/          <- your folder (this exact naming pattern)
  index.html                 <- REQUIRED: opening this starts the game
  thumbnail.png              <- REQUIRED: 1280x720 screenshot (Step 2)
  meta.json                  <- REQUIRED: title, name, controls (Step 3)
  ...everything else your game needs (js/, assets/, Build/, audio/...)
```

Folder name rules:

- Lowercase letters, numbers and hyphens only. No spaces, capitals, apostrophes or emoji.
- Pattern: your last name, a hyphen, then the game title. `Maya Okafor` + `Astro Dodge!` becomes `okafor-astro-dodge`.
- The three required files are spelled exactly as shown, all lowercase. `Index.html` or `Thumbnail.PNG` will break on the iPad.
- `index.html` must be at the top of your folder, not inside `build/`, `dist/` or `export/`. If your tool exports into a subfolder, move that subfolder's contents up.

Hand in only the exported, playable game. Leave out your project files (Unity project, `.godot` folder, `.psd`/`.fig` files, source art).

## Rules every game must follow

The arcade runs on a laptop and an iPad with no Wi-Fi, inside a frame with an Exit bar on top. Your game must work under those conditions.

1. **No internet, at all.** No `https://` links to scripts, fonts, images, sounds, APIs, leaderboards or logins. Every file your game loads lives inside your folder.
2. **Relative paths only.** Write `assets/ship.png`, never `/assets/ship.png`, `C:\Users\...` or `https://...`. Match capitalization exactly: `Ship.png` and `ship.png` are different files on the iPad.
3. **Fit any window.** The game fills whatever space it gets (about 1280×720 to 2400×1500). Scale or letterbox to the window; don't hard-code a 1920×1080 canvas.
4. **Don't use the Escape key.** The arcade uses Esc to quit back to the menu. Use P or Tab for pause.
5. **Start sound after the first click, tap or key press.** Browsers block audio that starts on its own. A "Click to start" title screen solves this.
6. **Say how it's played.** List every input your game needs: keyboard, mouse, touch or gamepad. Games that work with touch can run on the iPad station; keyboard-only games run on the laptop. List the devices your game supports in meta.json.
7. **No pop-ups or new tabs.** Don't use `alert()`, `window.open()` or links that leave the game.
8. **Keep it under 100 MB, with no single file over 100 MB** (GitHub rejects larger files). Compress large audio and video files.

## Step 1: Export your game

Find your tool below and follow only that section. Each one ends with the same result: a folder with `index.html` at the top.

### Built with Claude (or another AI tool)

Most games built with Claude are HTML and JavaScript, so they fit the arcade well. First work out which of these you have, because one of them doesn't run on its own.

| What you have | How to tell | What to do |
| --- | --- | --- |
| HTML artifact (claude.ai) | The code starts with `<!DOCTYPE html>` or `<html>` | Run the prompt below, then save Claude's new version as `index.html` in your game folder |
| React artifact (claude.ai) | The code starts with `import` and has `export default`. A download ends in `.jsx` | A `.jsx` file can't run by itself. Run the prompt below to turn it into a playable `index.html` |
| Claude Code project, plain files | Your project folder has an `index.html` and no `package.json` | Run the prompt below in Claude Code, in your project folder. It can fix the files directly |
| Claude Code project with a build | Your project folder has a `package.json` | Run the prompt in Claude Code, then follow the build steps under the prompt |

**Prompt to paste into the same Claude conversation as your game.** Paste it word for word:

```
Make this game ready for an offline arcade kiosk.

Requirements:
1. Prefer ONE self-contained index.html with all the HTML, CSS and JavaScript inside it. Use plain JavaScript; if this is React, rewrite it without React if you can.
2. No internet at all: no CDN scripts, no Google Fonts, no APIs, no window.claude or window.storage. If the game truly needs a library file (like three.js or p5.js), reference it as lib/<filename>, and tell me the exact URL to download it from and where to save it.
3. Relative file paths only (assets/ship.png, never /assets/ship.png). Match capitalization exactly.
4. The game resizes to fill any window from 1280x720 to 2400x1500, with no scrollbars.
5. Audio starts only after the player's first click, tap or key press.
6. Don't use the Escape key for anything. Use P for pause.
7. No alert(), confirm(), prompt() or window.open().
8. If the game saves progress or high scores, use localStorage.
9. Also write a meta.json file in exactly this format, filling in the title, controls, devices the one device it plays best on (designedFor) and whether it needs a landscape or portrait screen (orientation) for this game (leave "student" for me to fill in):
{
  "title": "",
  "student": "YOUR NAME",
  "tag": "Arcade",
  "input": ["keyboard", "mouse", "touch"],
  "devices": ["desktop", "tablet"],
  "designedFor": "desktop",
  "orientation": "landscape",
  "instructions": "Line one.\nLine two."
}
10. Give me every final file in full, and list where each one goes in the folder.
```

**Claude Code projects (Vite or React):**

1. Open `vite.config.js` and add `base: './',` inside `defineConfig({ ... })`. Without it, the game loads files from `/assets/`, which breaks inside the arcade.
2. In Terminal, in your project folder, run `npm run build`.
3. Your game is the contents of the new `dist/` folder. Copy them into your game folder; `index.html` should be at the top.

Claude sometimes misses an internet link or gets a path's capitalization wrong. The checker in Step 4 finds these and gives you the file and line number. If you get stuck, paste the checker's message into the same Claude conversation and ask it to fix that problem. Then go to Step 2.

### Hand-coded web games (p5.js, Phaser, Three.js, Kaboom, plain JavaScript, CodePen, AI-generated pages)

1. **Get the files onto your computer.**
    - p5.js Web Editor: File → Download. Unzip it.
    - CodePen: Export → Export .zip. Unzip it and use the contents of the `dist` folder.
    - Replit or Glitch: download the project as a zip and unzip it.
    - A single HTML file from Claude, ChatGPT or similar: save it as `index.html`.
2. **Rename your start page to `index.html`** and put it at the top of your folder.
3. **Find every internet link.** Open each `.html` and `.css` file in a text editor and search for `http`. Typical hits:
    - `<script src="https://cdn.jsdelivr.net/npm/p5@1.11.1/lib/p5.min.js">`
    - `<link href="https://fonts.googleapis.com/...">`
    - `<script src="https://cdn.tailwindcss.com">` or React, Phaser or Three.js from a CDN
4. **Download each one into your folder.** Paste the `https://...` address into your browser, then use File → Save Page As to save it into a `lib/` folder. Keep the same version number that was in the link.
5. **Point to the local copy.** Change the link to the saved file, e.g. `<script src="lib/p5.min.js"></script>`. If you use `p5.sound`, download `p5.sound.min.js` the same way.
6. **Fonts:** download the font files (`.woff2` or `.ttf`) into `fonts/` and load them with `@font-face` in your CSS instead of the Google Fonts link.
7. **Make it fill the window.**
    - p5.js: `createCanvas(windowWidth, windowHeight)`, plus a `windowResized()` function that calls `resizeCanvas(windowWidth, windowHeight)`.
    - Phaser: set `scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH }` in your game config.
    - Plain canvas: size the canvas to `window.innerWidth` and `window.innerHeight` and update it on the `resize` event.
8. Search for `http` once more. The only results should be in comments, or none at all.

### Unity (2022 LTS or Unity 6)

The one setting that matters is **Compression Format: Disabled**. A compressed build gets stuck on the loading bar in the arcade.

1. Install the Web build module if you haven't: Unity Hub → Installs → your version → ⚙ → Add modules → **WebGL Build Support**.
2. Open the build window:
    - Unity 6: File → Build Profiles → select **Web** → Switch Platform.
    - Unity 2022: File → Build Settings → select **WebGL** → Switch Platform.
3. Open Edit → Project Settings → Player → Web tab (the HTML5 icon) → expand **Publishing Settings**.
4. Set **Compression Format** to **Disabled**.
5. In **Resolution and Presentation**, keep the **Default** WebGL template.
6. Back in the build window, make sure **Development Build** is unticked.
7. Click **Build**, and choose a new empty folder named after your game (e.g. `okafor-astro-dodge`).
8. Check the result. Your folder should contain `index.html`, a `Build/` folder and a `TemplateData/` folder.

### Godot (4.3 or newer)

The one setting that matters is **Thread Support: off**. With it on, the game needs special server settings the arcade doesn't have, and shows a SharedArrayBuffer or cross-origin isolation error.

1. Godot 4.0–4.2 can't turn threads off. Update to 4.3 or newer first. (Godot 3.x is fine as is; skip step 4.)
2. Editor → Manage Export Templates → **Download and Install**. This needs internet once.
3. Project → Export → Add… → **Web**.
4. Untick **Thread Support** (under Variant).
5. Set **Export Path** to `index.html` inside a new empty folder named after your game.
6. Click **Export Project** and untick **Export With Debug**.
7. Make it fill the window: Project → Project Settings → Display → Window → Stretch → Mode = `canvas_items`, Aspect = `keep` or `expand`.
8. If sound crackles in the browser, set your AudioStreamPlayer nodes' **Playback Type** to **Sample** and export again.
9. Check the result. Your folder should contain `index.html`, `index.js`, `index.wasm` and `index.pck`, plus a few image files.

### Construct 3

1. Project Properties → Display → **Fullscreen mode** = **Letterbox scale** (or Scale outer).
2. Menu → Project → **Export** → **Web (HTML5)** → Next. Keep the default options and export.
3. Unzip the download. Rename the unzipped folder to your game's folder name. `index.html` should already be at the top.
4. If Export is locked on your plan, tell your instructor.

### GDevelop 5

1. Make it fit: Game settings → Properties → Resolution and rendering → turn on **Update resolution during the game to fit the screen or window size**.
2. File → **Export**. Choose the manual **Web (HTML5)** build that saves to a **local folder**, not the one-click publish to gd.games.
3. Export into a new empty folder named after your game. `index.html` will be at the top.

### GameMaker

1. In the target picker at the top right, choose **HTML5**, not GX.games or Opera GX.
2. Build → **Create Executable**, and save it as a zip.
3. Unzip it into a folder named after your game. You should see `index.html` and a `html5game/` folder.
4. If HTML5 is missing from the target list, tell your instructor. Don't submit a GX.games link; it needs internet.

### Twine 2

1. In the Story Library, open your story, then Build → **Publish to File**.
2. Save the file into your game folder and rename it `index.html`.
3. If your passages show images or play sound, copy those files into the folder and link them with relative paths like `img/map.png`.

### Bitsy

1. Click the **download** button in the editor.
2. Put the downloaded `.html` file in your game folder and rename it `index.html`.

### PICO-8

1. In the PICO-8 console, type `export index.html` and press Return.
2. Copy the resulting `index.html` and `index.js` into your game folder. The web player adds on-screen buttons for touch screens.

### Scratch

1. In Scratch, File → **Save to your computer** to get a `.sb3` file.
2. Open the TurboWarp Packager at packager.turbowarp.org (internet needed for this step only) and load your `.sb3`.
3. Under Environment, choose **Plain HTML** and click **Package**.
4. Put the downloaded `.html` file in your game folder and rename it `index.html`.

### Games built for one device

Web games made for one kind of device are welcome, such as a touch-only game for the iPad or a keyboard game for the laptop. List the devices in `meta.json` (Step 3), and the arcade shows your game only on those devices. Test it on the device you list. The arcade stations are a laptop and an iPad, so check with your instructor before listing phone only.

### What can't go in the arcade

The arcade runs games in a web browser, offline. These can't run that way, so talk to your instructor about an alternative.

- App files: `.apk` and `.ipa` (phone), `.exe` and `.app` (desktop). Unity, Godot, GameMaker and Construct can all export a web version instead; see your tool's section above.
- Figma or ProtoPie prototypes, and anything else that only plays inside its own app or website
- Unreal Engine, Roblox and Minecraft builds
- Online multiplayer, accounts, or anything that calls an AI or other web API

## Step 2: Make thumbnail.png

One PNG, exactly 1280×720 pixels (16:9), under 1 MB, named `thumbnail.png`. It's the picture on your card in the arcade menu.

1. Play your game and take a screenshot of an exciting moment of gameplay, not the title screen.
    - Mac: Cmd+Shift+4, then drag over the game.
    - Windows: Win+Shift+S, then drag over the game.
2. In Figma, make a **1280×720** frame. Drop the screenshot in and set it to fill the frame.
3. Skip the game title and your name; the card already shows both. Avoid small text near the edges.
4. Export the frame as **PNG at 1x**, name it `thumbnail.png`, and put it at the top of your game folder.

## Step 3: Write meta.json

This small text file tells the arcade your game's title, your name and how to play. Copy the template into a plain-text editor (VS Code, TextEdit in plain-text mode, Notepad), change the values, and save it as `meta.json` at the top of your game folder.

```json
{
  "title": "Astro Dodge",
  "student": "Maya Okafor",
  "tag": "Arcade",
  "input": ["keyboard"],
  "devices": ["desktop"],
  "designedFor": "desktop",
  "instructions": "Arrow keys or A / D to steer.\nSpace to fire.\nSurvive as long as you can."
}
```

| Field | What to write | Limit |
| --- | --- | --- |
| `title` | Your game's name as it should appear | 30 characters |
| `student` | Your name as you want it credited | One person or team name |
| `tag` | One genre word: Arcade, Puzzle, Narrative, Rhythm, Platformer, Strategy, Experimental | 1 word |
| `input` | Every input the game needs, from: `"keyboard"`, `"mouse"`, `"touch"`, `"gamepad"` | List all that apply |
| `devices` | The devices your game is built for, from: `"desktop"` (laptop), `"tablet"` (iPad), `"phone"`. If it works on all of them, list all three | List all that apply |
| `designedFor` | The ONE device your game plays best on: `"desktop"`, `"tablet"` or `"phone"`. It shows on your card as a Desktop, Tablet or Mobile tag. Optional | One value |
| `orientation` | `"landscape"` (wide) or `"portrait"` (tall), if your game only works one way. Phones and tablets held the wrong way get a "turn your device" message. Optional | One value |
| `instructions` | The controls and the goal, shown in the arcade's How to Play box. `\n` starts a new line | 3 short lines |

Keep the double quotes and commas exactly as in the template, with no comma after the last line. If you used the "Built with Claude" prompt, Claude has already written this file; just add your name. The checker in Step 4 tells you if there's a typo.

## Step 4: Test it in the arcade

Test your game inside the real arcade on your own laptop. The arcade is this repo, and you'll submit through it in Step 5. If your game passes the checker and plays in the arcade with Wi-Fi off, it will work on visit day. Double-clicking your `index.html` is not a valid test.

### Set up (once)

1. At the top of this repo's page, click **Fork**, then **Create fork**.
2. Clone your fork and make a branch for your game. Use your own GitHub username and folder name:

    ```
    git clone https://github.com/YOUR-USERNAME/studio-arcade.git
    cd studio-arcade
    git checkout -b add-lastname-game-title
    ```

3. Inside are the arcade (`index.html`), the checker (`check_games.py`) and a `games/` folder holding your classmates' games.
4. Make sure Python is installed (do this with Wi-Fi on):
    - Mac: run `python3 --version` in Terminal. If a window offers to install developer tools, click Install and wait for it to finish.
    - Windows: run `py --version`. If Python isn't found, install it from python.org and tick **Add python.exe to PATH**.

### Run the checker

1. Copy your game folder into `studio-arcade/games/`, next to your classmates' folders. If you're unsure what your folder should look like, open one of theirs (for example `walsh-the-catch`) and compare.
2. In your terminal, make sure you're in the `studio-arcade` folder. You already are if you just cloned it.
3. Run `python3 check_games.py --write` (Windows: `py check_games.py --write`).
4. Read the result for your folder:
    - **FAIL**: the game won't work in the arcade. Fix it.
    - **WARN**: possibly a problem. Read it and decide.
    - **OK**: passed.
5. Fix each FAIL and run the checker again until your folder has none. If you're stuck, paste the checker's message into the Claude conversation where you made the game and ask it to fix that problem.

### Play it in the arcade

1. Turn Wi-Fi off.
2. Run `python3 -m http.server 8080` (Windows: `py -m http.server 8080`). Leave this window open while you test.
3. Open Chrome and go to `http://localhost:8080`. Your card should show your thumbnail, title and name. Click it.
4. Check each of these:
    - The How to Play box shows your instructions.
    - The game fills the screen below the Exit bar.
    - You can play for 3 minutes, with sound.
    - Both the Esc key and the **Exit to Arcade** button return you to the menu.
5. Open the developer console (Cmd+Option+J on Mac, Ctrl+Shift+J on Windows) while your game is running. There should be no red errors.
6. If you listed `"tablet"` in meta.json, go to `http://localhost:8080/?device=tablet` and check that your game is listed.
7. When you're done, click the Terminal window and press Ctrl+C to stop the arcade.

Running `--write` changed the arcade's `index.html` so you could test. Step 5 shows how to leave that change out of your submission.

## Step 5: Submit with a pull request

Your pull request adds exactly one thing to the class repo: your game folder inside `games/`. GitHub checks it automatically, and your instructor merges it into the arcade.

1. Undo the test change to `index.html`, then commit only your folder. Use your own folder name:

    ```
    git checkout -- index.html
    git add games/okafor-astro-dodge
    git commit -m "Add Astro Dodge by Maya Okafor"
    git push -u origin add-lastname-game-title
    ```

2. On your fork's GitHub page, click **Compare & pull request**. Title it `Add <game title> by <your name>` and click **Create pull request**.
3. Wait about a minute for the **Arcade check** at the bottom of the pull request:
    - **Green check:** ready. Your instructor will review and merge it.
    - **Red X:** click **Details** and read the report. Fix the problems, commit, and push again. The check reruns automatically.
4. If the check says it's waiting for approval, that's normal for a first pull request. Your instructor will start it.

Common mistakes:

- **The check says files outside games/ changed.** You committed `index.html` or another arcade file. Run `git checkout main -- index.html`, then commit and push.
- **`git add .` picked up other files.** Only add your own folder: `git add games/<your-folder>`.
- **The check says more than one game folder changed, or that you added back the sample game.** Your pull request may only touch your own folder. Remove the rest with `git rm -r games/<other-folder>` (or `git checkout main -- games/<other-folder>` if it's a classmate's), then commit and push. Don't restore folders that disappear when you sync your fork; they were removed on purpose.
- **Push was rejected for a large file.** A file is over 100 MB. Compress it, then commit again.

## Final checklist

Tick every box before you open your pull request.

- [ ] Folder name is lowercase with hyphens: `lastname-game-title`
- [ ] `index.html`, `thumbnail.png` and `meta.json` are at the top of the folder
- [ ] `meta.json` has your name, your controls (`input`) and your `devices`
- [ ] The checker shows no FAIL for your folder
- [ ] Played it in the arcade with Wi-Fi off, for 3 minutes, with sound
- [ ] Game fills the screen below the Exit bar
- [ ] Esc and the Exit button both return to the menu
- [ ] No red errors in the console while playing
- [ ] Pull request changes only your folder, and the Arcade check is green
- [ ] Only the exported game is included, no project or source files

## Troubleshooting

| What you see | Likely cause | Fix |
| --- | --- | --- |
| A list of files instead of your game | `index.html` is missing, misnamed or in a subfolder | Rename your start page to `index.html` and move it to the top of the folder |
| Blank or black screen; console shows 404 or "Failed to load" | A path has the wrong capitalization, a leading `/`, or points outside the folder | Make the path relative and match the file name's capitalization exactly |
| Works with Wi-Fi on, breaks with it off | A script, font or image still loads from `https://` | Download it into the folder (Step 1) and change the link |
| Unity stuck on the loading bar, or an error about `.gz` / `.br` files | Compression is on | Set Compression Format to Disabled and rebuild |
| Godot error mentioning SharedArrayBuffer or cross-origin isolation | Thread Support is on | Untick Thread Support and export again |
| Error mentioning CORS or `file://` | You double-clicked `index.html` | Test through a local server (Step 4) |
| No sound | Audio starts before the player interacts | Start audio on the first click, tap or key press |
| Game is tiny, cut off, or has scrollbars | The canvas has a fixed size | Scale to the window (see your tool's section in Step 1) |
| Pressing Esc quits to the arcade menu instead of pausing | The arcade uses Esc to exit | Move pause to P or Tab |
| The browser shows your code as text, or the download is a .jsx file | It's a React artifact, which needs to be converted before it can run | Paste the prompt from "Built with Claude" into the same conversation |
| Saves, high scores or AI features stopped working | The game used window.storage or window.claude, which only exist on claude.ai | Switch saves to localStorage; remove live AI features |

## Sources

- [Unity Manual: Deploy a Web application](https://docs.unity3d.com/Manual/webgl-deploying.html) (Compression Format, Decompression Fallback)
- [Godot: Web export in 4.3](https://godotengine.org/article/progress-report-web-export-in-4-3/) (single-threaded builds, Sample playback for audio)
