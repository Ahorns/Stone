# SimAgents — WOSAC Research Plan V2

## 更新
1. 更新了Phase1的代码
2. 更新了一下PPT,加了一页有关Phase1-step2的结果,你可以和老师说,你现在就正在做这一步,学习waymo官方给的tutorial.

## Suggestions:

### Stpe1
整个架构先看docs/plan.md(包括appendix1.md),里面有比较详细地介绍整个竞赛是在做什么,你需要看什么文献如果开始做(这次开会都没必要看),你应该如何入手.
>(**在vscode里面按ctrl+shift+v开阅读md文件视图**)
### Step2 
之后看slide_guide.md,这个是整个汇报的推荐思路,可以结合着PPT文件一起看,PPT在slides/dist/WOSAC_Research_Plan.pptx.

### Step3
你可以想想你自己现在做到哪一步了, 根据那个ppt里面的phase分布,我可以给你update到的基本上是Phase2初步,但是我更建议是给老师说你在做phase1a, 也就是你可以说还在学习waymax tutorial, 之后我会把所有我有的文件update到github里面.

### Step4
个人感觉此次开会主要就是两点,第一点是给老师和介绍整个项目是大概做什么的,第二点是问老师有没有什么建议,建议可以是比如有什么推荐算法什么的(大概率没有),还有一个比较重要的帮助老师可以给的是,能不能给服务器权限,如果她有的话.因为你是做大模型的,硬件要求很高,然后存储空间至少需要80G,所以看看老师能不能给你找服务器.


Research plan and slide deck for the **Waymo Open Sim Agents Challenge (WOSAC)**, framed as a UCL Bartlett supervisor meeting.

## Folder structure

```
SimAgents/
├── docs/                  Written research notes (Markdown)
│   ├── plan.md            Research plan
│   ├── slide-guide.md     Slide-by-slide content guide (source of truth for the deck)
│   └── appendix-1.md      Glossary + key reading list
│
├── slides/                Everything needed to build the presentation
│   ├── build.js           pptxgenjs build script — generates the .pptx
│   ├── package.json       Node dependencies (pptxgenjs)
│   ├── assets/            Source media
│   │   ├── demonstrate.gif                Multi-agent rollout animation (Slide 4)
│   │   ├── factorization.webp             ADV/world conditional-independence figure (Slide 6)
│   │   ├── home-anim-transparent.webm     Waymo homepage animation (optional)
│   │   ├── waymo-logo.svg                 Waymo Open Dataset wordmark
│   │   └── processed/                     PNG / recoloured versions ready for PowerPoint
│   ├── dist/              Build outputs
│   │   ├── WOSAC_Research_Plan.pptx
│   │   └── WOSAC_Research_Plan.pdf
│   └── qa/                Slide thumbnails (slide-01.jpg … slide-16.jpg) for visual review
│
├── .agents/skills/pptx/   Anthropic pptx skill (auto-loaded by Claude Code in this folder)
├── Phase1_showcase/       主要说了一下Phase1需要做什么,这是一个已经完成了的版本,你之后可以自己做一版.
└── skills-lock.json       Skill version pin

```

## How to get the slides

### Just open the file

```
slides/dist/WOSAC_Research_Plan.pptx
```

Open in PowerPoint or Keynote. The `demonstrate.gif` on Slide 4 animates during slideshow mode.

### Rebuild from source

After editing `slides/build.js`:

```bash
cd slides
node build.js
```

Output is overwritten at `slides/dist/WOSAC_Research_Plan.pptx`.

### Render PDF + thumbnails (for QA)

```bash
cd slides
python3 ../.agents/skills/pptx/scripts/office/soffice.py \
    --headless --convert-to pdf --outdir dist dist/WOSAC_Research_Plan.pptx
pdftoppm -jpeg -r 110 dist/WOSAC_Research_Plan.pdf qa/slide
```

Produces `slides/dist/WOSAC_Research_Plan.pdf` and `slides/qa/slide-XX.jpg` per slide.

## Editing flow

1. Edit content in `docs/slide-guide.md` (the design / content source).
2. Mirror the changes in `slides/build.js`.
3. Run `node build.js` from `slides/`.
4. Re-render thumbnails and visually check.

## Dependencies

- Node ≥ 18 with `pptxgenjs` (installed via `npm install` in `slides/`)
- LibreOffice (`soffice`) — for PPTX → PDF conversion
- Poppler (`pdftoppm`) — for PDF → JPG conversion
- Python 3 + Pillow — used by helper scripts

## Deck overview (16 slides)

| # | Title |
|---|---|
| 1 | Title / Meeting Objective |
| 2 | Motivation |
| 3 | Background — why realistic simulation matters |
| 4 | Task definition (with rollout GIF) |
| 5 | Framing — competition vs research |
| 6 | Benchmark platform (with factorization figure) |
| 7 | Evaluation — distribution matching |
| 8 | Candidate optimisation directions (A / B / C / D) |
| 9 | Initial focus — closed-loop, interaction-aware |
| 10 | Roadmap (3 phases × 10-week timeline) |
| 11 | Phase 1A — Steps 1–2: data + tutorial |
| 12 | Phase 1B — Steps 3–4: baselines + first learned model |
| 13 | Phase 2 — single-agent → joint multi-agent simulation |
| 14 | Phase 3 — evaluate the design |
| 15 | Discussion questions |
| 16 | References |
