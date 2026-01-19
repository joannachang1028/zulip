# AI Usage

## What I used

I used **GitHub Copilot** (Claude Opus 4.5 via VS Code) for most of this assignment. Also used **Groq's Llama 3.3** for the actual features in the app.

## How it helped

Copilot was really useful for:
- Figuring out Zulip's codebase — it's huge and I had no idea where to start. Copilot helped me find the right files to look at
- Writing boilerplate — Django views, TypeScript modules, tests. A lot of the code follows patterns that already exist in Zulip, so Copilot was good at copying those patterns
- Debugging — when things broke (which happened a lot), Copilot could usually figure out what went wrong from the error messages

The best part was not having to constantly look stuff up. Instead of reading docs for every Zulip internal API, I could just ask and get a working example.

## What was frustrating

- **Vagrant environment issues**: Copilot can't actually run commands in my VM, so when stuff broke at the system level (like the venv getting corrupted), I had to debug it myself mostly. We went back and forth a lot on this.
- **Zulip-specific stuff**: Sometimes Copilot would suggest code that looked right but used wrong function names or wrong decorator patterns. Had to double-check everything.
- **Frontend was harder than backend**: Getting the TypeScript/Handlebars stuff to work took more iteration. The backend was pretty smooth.

## Overall thoughts

Honestly saved a lot of time. The assignment would've taken way longer without it — probably 3x as long? The main value was in not getting stuck. When something broke, I could usually get unstuck quickly instead of spending hours googling.

But I still had to understand what the code was doing. Copilot would generate stuff and sometimes it was wrong, so I had to actually read it and test it.
