# Style playbook: what makes "interesting" short-form motion videos

From studying two reference videos the user liked (Nov 2026). Both were ~1–2 min TikToks
promoting a "Claude motion graphics" skill. Take the TECHNIQUES, not their branding/characters.

## What the references do

**Ref A (2:04, narrated explainer):** animation played on a laptop screen, filmed in a
warm, dim room. Recurring mascot characters (a pixel/voxel detective in a hat and a small
orange blob creature) live in 3D voxel rooms. Kinetic words land in sync with the voiceover.
"Video inside a video" recursion. A persistent overlay the whole time: series label
("Tutorial 1"), topic, and a CTA pill ("Skill in my bio 🔗").

**Ref B (0:56, narrated):** the animation plays on a monitor on a desk with a keyboard, with
orange backlight stripes behind. The screen's colour lights the room (orange screen = orange
desk). One-word captions sit on the keyboard, low centre. Persistent top banner:
`COMMENT "CLAUDE" FOR FULL GUIDE` (comment-to-DM funnel). Screen content: glowing kinetic
type, a dot travelling an arc with a trail, UI cards stacking in 3D perspective, counters
(2H → 16H), a "15 SECONDS" payoff, squash/stretch text, 3D extruded text, and a push-in
until the screen fills the frame.

## Techniques to reuse (and how to do them here)

| Technique | Why it works | How (this skill) |
|---|---|---|
| **Screen-in-scene**: animation shown on a real laptop/monitor/phone | Feels made-by-a-person, not an ad; adds depth | User films ONE 10s static shot (or photo) of their desk/laptop. Composite the render onto the screen with CSS `matrix3d` / ffmpeg `perspective`. Add a glow in the screen's colour on the desk. Optional slow push-in. |
| **Persistent series overlay** ("Tutorial 1", "Day 3 of 30") | Series = binge + follows; frames every second as on-brand | Fixed `<div>` above all scenes, not inside one. |
| **Persistent CTA banner** ("Comment PLAN for the guide") | Comments boost reach and give a DM funnel; better than "link in bio" alone | Fixed top banner. The keyword must match a DM automation the user has (ManyChat etc.). Ask first. |
| **One-word captions** synced to the VO | Readable at a glance; rhythm | Per-word timings: generate the VO phrase by phrase (vo_marks.json), spread the words across each phrase. |
| **Recurring mascot** | Recognisable across many videos; carries a story | An SVG or three.js character reused in every video (designed once, saved in assets). |
| **Real 3D**: product, extruded text, rooms | Production value; stops the scroll | `templates/3d-product.html` (three.js). Extruded text: three.js TextGeometry, or layered CSS text-shadow for 2.5D. |
| **Motion paths with trails** (arc, bounce) | Shows "journey / transformation" (day 1 → day 30) | SVG path + dot position from `getPointAtLength(p*len)`, trail = previous positions faded. |
| **Counters / timers** | Concrete numbers = credibility | `data-count`. |
| **UI cards stacking in perspective** | "System / workflow" feel | CSS `perspective` + `rotateX` on a stack, staggered `up` entrances. |
| **Squash & stretch, glitch, RGB split** | Energy on key words | scale X/Y by t; duplicated text with red/cyan offsets, ≤0.3s. |
| **Push-in to fill the frame / match cuts** | Hides cuts and keeps continuity | Animate the scale of the whole stage; end scene A on a shape that scene B starts from. |
| **Video-in-video recursion** | Curiosity loop, rewatches | Render clip A, place it as `<video>`/frames inside a screen in clip B. |

## Pacing benchmarks (both refs)
- Visual change every 1–2s; almost no hard cuts (morphs, push-ins, continuous camera).
- Voice carries the story; the screen illustrates each phrase as it's spoken.
- 1–2 minutes is fine **when it teaches** (explainer / tutorial / story). Ads that sell stay 20–40s.
- The hook names the payoff and the viewer in the first line.

## Long videos (60s+)
Build as chapters: one HTML file per 10–20s chapter, rendered separately, then joined
with ffmpeg concat. Re-renders stay fast and one chapter can change without touching the others.
Keep a fixed series overlay and the CTA banner in every chapter (copy the same markup).
