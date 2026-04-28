# SimAgents — WOSAC Research Plan V2

## 更新
1. 更新了Phase1的代码
2. 更新了一下PPT,加了一页有关Phase1-step2的结果,你可以和老师说,你现在就正在做这一步,学习waymo官方给的tutorial，当然也可以不说，那就用第一版。

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
├── docs/                  一开始读这个文档先
│   ├── plan.md            Research plan  这个是整个项目的简单介绍
│   ├── slide-guide.md     Slide-by-slide content guide (source of truth for the deck)  这个是ppt的架构介绍，也是我给claude的提示词
│   └── appendix-1.md      Glossary + key reading list 和plan一起看
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
│   ├── dist/              Build outputs PPT在这里！
│   │   ├── WOSAC_Research_Plan.pptx
│   │   ├── WOSAC_Research_Plan2.pptx
│   │   └── WOSAC_Research_Plan.pdf
│   └── qa/                Slide thumbnails (slide-01.jpg … slide-16.jpg) for visual review
│
├── .agents/skills/pptx/   Anthropic pptx skill (auto-loaded by Claude Code in this folder) 这个就是skill的包
├── Phase1_showcase/       主要说了一下Phase1需要做什么,这是一个已经完成了的版本,你之后可以自己做一版.
└── skills-lock.json       Skill version pin

```

## How to get the slides
就很简单 我把这个pptx的skill都放进来了，你让claude直接读，他就知道怎么生成ppt。
### Just open the file
这个是ppt的位置
```
slides/dist/WOSAC_Research_Plan.pptx（现在有第二版，主要就是多了一页显示phase1，step2的结果）
```

## Deck overview (16 slides)
PPT的架构
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
