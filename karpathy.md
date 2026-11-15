# Karpathy: 100 most-liked posts

Ranked by likes. Counts pulled 2026-11-15. Scope: original posts by [@karpathy](https://x.com/karpathy); replies and retweets excluded, quote-posts included. Full text of long-form posts is included.

---

## 1. 2026-05-19 — 148,694 likes

> Personal update: I've joined Anthropic. I think the next few years at the frontier of LLMs will be especially formative. I am very excited to join the team here and get back to R&D. I remain deeply passionate about education and plan to resume my work on it in time.

[https://x.com/karpathy/status/2056753169888334312](https://x.com/karpathy/status/2056753169888334312)

## 2. 2023-01-24 — 72,898 likes

> The hottest new programming language is English

[https://x.com/karpathy/status/1617979122625712128](https://x.com/karpathy/status/1617979122625712128)

## 3. 2026-04-02 — 61,082 likes

> LLM Knowledge Bases
>
> Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. In this way, a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge (stored as markdown and images). The latest LLMs are quite good at it. So:
>
> Data ingest:
> I index source documents (articles, papers, repos, datasets, images, etc.) into a raw/ directory, then I use an LLM to incrementally "compile" a wiki, which is just a collection of .md files in a directory structure. The wiki includes summaries of all the data in raw/, backlinks, and then it categorizes data into concepts, writes articles for them, and links them all. To convert web articles into .md files I like to use the Obsidian Web Clipper extension, and then I also use a hotkey to download all the related images to local so that my LLM can easily reference them.
>
> IDE:
> I use Obsidian as the IDE "frontend" where I can view the raw data, the the compiled wiki, and the derived visualizations. Important to note that the LLM writes and maintains all of the data of the wiki, I rarely touch it directly. I've played with a few Obsidian plugins to render and view data in other ways (e.g. Marp for slides).
>
> Q&A:
> Where things get interesting is that once your wiki is big enough (e.g. mine on some recent research is ~100 articles and ~400K words), you can ask your LLM agent all kinds of complex questions against the wiki, and it will go off, research the answers, etc. I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries of all the documents and it reads all the important related data fairly easily at this ~small scale.
>
> Output:
> Instead of getting answers in text/terminal, I like to have it render markdown files for me, or slide shows (Marp format), or matplotlib images, all of which I then view again in Obsidian. You can imagine many other visual output formats depending on the query. Often, I end up "filing" the outputs back into the wiki to enhance it for further queries. So my own explorations and queries always "add up" in the knowledge base.
>
> Linting:
> I've run some LLM "health checks" over the wiki to e.g. find inconsistent data, impute missing data (with web searchers), find interesting connections for new article candidates, etc., to incrementally clean up the wiki and enhance its overall data integrity. The LLMs are quite good at suggesting further questions to ask and look into.
>
> Extra tools:
> I find myself developing additional tools to process the data, e.g. I vibe coded a small and naive search engine over the wiki, which I both use directly (in a web ui), but more often I want to hand it off to an LLM via CLI as a tool for larger queries.
>
> Further explorations:
> As the repo grows, the natural desire is to also think about synthetic data generation + finetuning to have your LLM "know" the data in its weights instead of just context windows.
>
> TLDR: raw data from a given number of sources is collected, then compiled by an LLM into a .md wiki, then operated on by various CLIs by the LLM to do Q&A and to incrementally enhance the wiki, and all of it viewable in Obsidian. You rarely ever write or edit the wiki manually, it's the domain of the LLM. I think there is room here for an incredible new product instead of a hacky collection of scripts.

[https://x.com/karpathy/status/2039805659525644595](https://x.com/karpathy/status/2039805659525644595)

## 4. 2026-10-02 — 56,781 likes

> We'll be spending a lot more time trying to understand the outputs of language models. A few thoughts, tips & tricks:
>
> Writing. Something I've had success with: Ask your LLM to explain something in ASD-STE100, it's a controlled language specification originally developed for aerospace maintenance documentation. LLMs well-versed in this language and it comes with heavy constraints on clean writing style that I often find a lot more readable. Sometimes I've tried to soften it a bit e.g. ask for "80% of the way to ASD-STE100" because the spec is quite stringent. But even better:
>
> Diagrams / images. Instead of writing, ask your LLM to create a diagram. These can be a lot easier to process, parse, and understand. But even better:
>
> Web pages. Ask for output "in HTML" to get a beautiful, interactive webpage. LLMs are getting really good at frontend and can create beautiful experiences, animations, etc. But even better:
>
> Explainer videos. The output format I am most bullish on is fully custom / bespoke explainer videos generated on any arbitrary topic. Experiment with things like "Create a 3b1b style video explainer on X. Use my ElevenLabs API key for audio narration". (you'd need an API key for the latter or you can ask your LLM to find you decent free alternatives that use your local compute). This is actually starting to work!
>
> In summary:
> - As LLMs get better, they will do more and more of the legwork autonomously, and a lot more of our work will rise up the abstractions into oversight and understanding.
> - Luckily, LLMs can help here too because as intelligence and code are increasingly abundant, you can ask for large, custom, discardable software artifacts (e.g. web apps, video explainers) that would have never made sense to create before. Push the boundaries here and you'll be surprised.

[https://x.com/karpathy/status/2105819303471976479](https://x.com/karpathy/status/2105819303471976479)

## 5. 2025-12-26 — 55,184 likes

> I've never felt this much behind as a programmer. The profession is being dramatically refactored as the bits contributed by the programmer are increasingly sparse and between. I have a sense that I could be 10X more powerful if I just properly string together what has become available over the last ~year and a failure to claim the boost feels decidedly like skill issue. There's a new programmable layer of abstraction to master (in addition to the usual layers below) involving agents, subagents, their prompts, contexts, memory, modes, permissions, tools, plugins, skills, hooks, MCP, LSP, slash commands, workflows, IDE integrations, and a need to build an all-encompassing mental model for strengths and pitfalls of fundamentally stochastic, fallible, unintelligible and changing entities suddenly intermingled with what used to be good old fashioned engineering. Clearly some powerful alien tool was handed around except it comes with no manual and everyone has to figure out how to hold it and operate it, while the resulting magnitude 9 earthquake is rocking the profession. Roll up your sleeves to not fall behind.

[https://x.com/karpathy/status/2004607146781278521](https://x.com/karpathy/status/2004607146781278521)

## 6. 2026-11-01 — 52,580 likes

> Weekend hack: HackerTube. I was annoyed with YouTube's recommendations so I had Claude filter down 43M comments over 20 years of HN to 6,454 videos that keep being recommended. *Significantly* better viewing experience, ~2 hours with Opus 5.5:
> https://hackertube.org/
>
> - Excellent recs without any logins (state is kept in local browser session)
> - Thumbnail is a representative frame from middle of the video instead of the super duper A/B test hyper-optimized user uploads
> - Underlying data from the comment analysis as one zip file, point your Claude at it and ask for your own version
> - HackerTube Longs ✊
>
> A bit more on the process:
> I use Claude Code (desktop app for Mac), Opus 5.5 on Medium effort as my default. I only talk to Claude and have it do everything, the only "manual work" I helped with in tandem was in the browser (reminiscent of MenuGen): 1) I had to create some kind of API key from Google Cloud UI to query YouTube for video metadata, 2) I booted up a VPS box for serving and 3) I bought the domain name. Once the box was up I gave Claude the IP and told it update, secure, harden, deploy and optimize the code, and it did the whole thing.
>
> Many awesome projects that would have normally taken weeks/months even can now be few-shotted for breakfast. What else are we not thinking of.

[https://x.com/karpathy/status/2116957135661945283](https://x.com/karpathy/status/2116957135661945283)

## 7. 2026-07-21 — 50,345 likes

> One pattern I find useful for working with LLMs is a nice long ramble session. Sometimes the LLM needs more bits to understand what you're trying to achieve, but you're too lazy to type them. In these cases I like to lean back, switch to /voice and just ramble for like 10 minutes, total mess, anything goes, full stream of consciousness. Sometimes I declare it up top, something like "switching to speech recognition sorry for any typos...". Sometimes I turn it into a small interview of a few turns. But I find that the LLMs are somehow very good at reconstructing long incoherent rambles and often their echo of your own tangle of thoughts comes out quite a bit cleaner than what you started with. The result is that you improve the mind meld and have to correct things less from that point on.

[https://x.com/karpathy/status/2079610838143623371](https://x.com/karpathy/status/2079610838143623371)

## 8. 2025-02-24 — 49,928 likes

> Agency > Intelligence
>
> I had this intuitively wrong for decades, I think due to a pervasive cultural veneration of intelligence, various entertainment/media, obsession with IQ etc. Agency is significantly more powerful and significantly more scarce. Are you hiring for agency? Are we educating for agency? Are you acting as if you had 10X agency?
>
> Grok explanation is ~close:
>
> “Agency, as a personality trait, refers to an individual's capacity to take initiative, make decisions, and exert control over their actions and environment. It’s about being proactive rather than reactive—someone with high agency doesn’t just let life happen to them; they shape it. Think of it as a blend of self-efficacy, determination, and a sense of ownership over one’s path.
>
> People with strong agency tend to set goals and pursue them with confidence, even in the face of obstacles. They’re the type to say, “I’ll figure it out,” and then actually do it. On the flip side, someone low in agency might feel more like a passenger in their own life, waiting for external forces—like luck, other people, or circumstances—to dictate what happens next.
>
> It’s not quite the same as assertiveness or ambition, though it can overlap. Agency is quieter, more internal—it’s the belief that you *can* act, paired with the will to follow through. Psychologists often tie it to concepts like locus of control: high-agency folks lean toward an internal locus, feeling they steer their fate, while low-agency folks might lean external, seeing life as something that happens *to* them.”

[https://x.com/karpathy/status/1894099637218545984](https://x.com/karpathy/status/1894099637218545984)

## 9. 2026-04-30 — 46,579 likes

> This is the the quote I've been citing a lot recently.

[https://x.com/karpathy/status/2049907410303865030](https://x.com/karpathy/status/2049907410303865030)

## 10. 2026-10-11 — 44,320 likes

> Dusting off this tweet from April because this gap in shared understanding of LLM capability is *widening*. It's now less "two groups of people speaking past each other" and more a sharp funnel.
>
> - Napkin math somewhere around 6B people (~75% of the population) have barely come in contact with LLMs at all.
> - Around 1-2B (~20%) are casual and infrequent users of free-tier ChatGPT-like products. This group sees derpy chatbots and treats them a bit like a better Google search, a writing aid, or etc. Maybe an agent tries to book you a flight. I have non-tech friends who (reasonably, imo) say they have not much use for it at all. Even many professionals outside of math&code are in this tier. For example, execs and many other functions spend a lot of their time talking to other people, so while they understand what is happening intellectually, it is still second-hand and a bit abstract.
> - Now we get to professional use of frontier-grade LLMs in math&code. Somewhere around 20M people (0.2%) see first-hand that large, complex projects that used to take them weeks/months can now be completed by agents with a prompt. Building apps, copying apps, translating apps, decompiling apps from binaries... This has all happened very quickly and recently - less than 1 year ago, I was writing code manually by hand, typing memorized computer code commands into a code editor character by character, occasionally pressing Tab to autocomplete a little chunk of code.
> - And finally we get to the ~5,000 people (~0.00006%) with access to frontier-grade systems internally. The external world has seen the preview. It looks like swarms of thousands of agents collaborating over weeks on software mega projects: minting zero days, running cyber attacks and defenses at machine speeds, discovering new science, advancing the frontier of mathematics. Things that would have taken top professionals in the industry years of work. Meanwhile, human review and comprehension are starting to fall behind. For example, people are still involved in the "archeology" of the OpenAI-HF incident from many months ago. Mathematicians may be poring over the 722 manuscripts on frontier mathematics for a while.
>
> The funnel is driven by a combination of factors:
> 1. The impact scales with ambition, problem size, and horizon. A question with a paragraph answer barely stresses the system. You need a reservoir of big, difficult problems that you really care about. This aspect drives the consumer / professional dimension of the funnel.
> 2. The jaggedness of the system (which I have written about a lot separately). Capability peaks in domains that are digital, verifiable and economically valuable. This is because LLM capability emerges from reinforcement learning on verifiable rewards on a curated environment mixture driven by revenue potential. This aspect primarily drives the area (e.g. math&code) dimension of the funnel.
> 3. Access. Free-tier, paid-tier, internal.
>
> So this is the weirdness of the moment. The general public has mostly not interacted with these systems. When they have, it looks like a derpy chatbot. The majority of professionals still see only a modest uplift. And a small sliver of professionals are experiencing the vertigo of the curve going vertical. And it is all happening at the same time.

[https://x.com/karpathy/status/2109361546505966046](https://x.com/karpathy/status/2109361546505966046)

## 11. 2026-01-26 — 40,712 likes

> A few random notes from claude coding quite a bit last few weeks.
>
> Coding workflow. Given the latest lift in LLM coding capability, like many others I rapidly went from about 80% manual+autocomplete coding and 20% agents in November to 80% agent coding and 20% edits+touchups in December. i.e. I really am mostly programming in English now, a bit sheepishly telling the LLM what code to write... in words. It hurts the ego a bit but the power to operate over software in large "code actions" is just too net useful, especially once you adapt to it, configure it, learn to use it, and wrap your head around what it can and cannot do. This is easily the biggest change to my basic coding workflow in ~2 decades of programming and it happened over the course of a few weeks. I'd expect something similar to be happening to well into double digit percent of engineers out there, while the awareness of it in the general population feels well into low single digit percent.
>
> IDEs/agent swarms/fallability. Both the "no need for IDE anymore" hype and the "agent swarm" hype is imo too much for right now. The models definitely still make mistakes and if you have any code you actually care about I would watch them like a hawk, in a nice large IDE on the side. The mistakes have changed a lot - they are not simple syntax errors anymore, they are subtle conceptual errors that a slightly sloppy, hasty junior dev might do. The most common category is that the models make wrong assumptions on your behalf and just run along with them without checking. They also don't manage their confusion, they don't seek clarifications, they don't surface inconsistencies, they don't present tradeoffs, they don't push back when they should, and they are still a little too sycophantic. Things get better in plan mode, but there is some need for a lightweight inline plan mode. They also really like to overcomplicate code and APIs, they bloat abstractions, they don't clean up dead code after themselves, etc. They will implement an inefficient, bloated, brittle construction over 1000 lines of code and it's up to you to be like "umm couldn't you just do this instead?" and they will be like "of course!" and immediately cut it down to 100 lines. They still sometimes change/remove comments and code they don't like or don't sufficiently understand as side effects, even if it is orthogonal to the task at hand. All of this happens despite a few simple attempts to fix it via instructions in CLAUDE . md. Despite all these issues, it is still a net huge improvement and it's very difficult to imagine going back to manual coding. TLDR everyone has their developing flow, my current is a small few CC sessions on the left in ghostty windows/tabs and an IDE on the right for viewing the code + manual edits.
>
> Tenacity. It's so interesting to watch an agent relentlessly work at something. They never get tired, they never get demoralized, they just keep going and trying things where a person would have given up long ago to fight another day. It's a "feel the AGI" moment to watch it struggle with something for a long time just to come out victorious 30 minutes later. You realize that stamina is a core bottleneck to work and that with LLMs in hand it has been dramatically increased.
>
> Speedups. It's not clear how to measure the "speedup" of LLM assistance. Certainly I feel net way faster at what I was going to do, but the main effect is that I do a lot more than I was going to do because 1) I can code up all kinds of things that just wouldn't have been worth coding before and 2) I can approach code that I couldn't work on before because of knowledge/skill issue. So certainly it's speedup, but it's possibly a lot more an expansion.
>
> Leverage. LLMs are exceptionally good at looping until they meet specific goals and this is where most of the "feel the AGI" magic is to be found. Don't tell it what to do, give it success criteria and watch it go. Get it to write tests first and then pass them. Put it in the loop with a browser MCP. Write the naive algorithm that is very likely correct first, then ask it to optimize it while preserving correctness. Change your approach from imperative to declarative to get the agents looping longer and gain leverage.
>
> Fun. I didn't anticipate that with agents programming feels *more* fun because a lot of the fill in the blanks drudgery is removed and what remains is the creative part. I also feel less blocked/stuck (which is not fun) and I experience a lot more courage because there's almost always a way to work hand in hand with it to make some positive progress. I have seen the opposite sentiment from other people too; LLM coding will split up engineers based on those who primarily liked coding and those who primarily liked building.
>
> Atrophy. I've already noticed that I am slowly starting to atrophy my ability to write code manually. Generation (writing code) and discrimination (reading code) are different capabilities in the brain. Largely due to all the little mostly syntactic details involved in programming, you can review code just fine even if you struggle to write it.
>
> Slopacolypse. I am bracing for 2026 as the year of the slopacolypse across all of github, substack, arxiv, X/instagram, and generally all digital media. We're also going to see a lot more AI hype productivity theater (is that even possible?), on the side of actual, real improvements.
>
> Questions. A few of the questions on my mind:
> - What happens to the "10X engineer" - the ratio of productivity between the mean and the max engineer? It's quite possible that this grows *a lot*.
> - Armed with LLMs, do generalists increasingly outperform specialists? LLMs are a lot better at fill in the blanks (the micro) than grand strategy (the macro).
> - What does LLM coding feel like in the future? Is it like playing StarCraft? Playing Factorio? Playing music?
> - How much of society is bottlenecked by digital knowledge work?
>
> TLDR Where does this leave us? LLM agent capabilities (Claude & Codex especially) have crossed some kind of threshold of coherence around December 2025 and caused a phase shift in software engineering and closely related. The intelligence part suddenly feels quite a bit ahead of all the rest of it - integrations (tools, knowledge), the necessity for new organizational workflows, processes, diffusion more generally. 2026 is going to be a high energy year as the industry metabolizes the new capability.

[https://x.com/karpathy/status/2015883857489522876](https://x.com/karpathy/status/2015883857489522876)

## 12. 2025-02-02 — 38,013 likes

> There's a new kind of coding I call "vibe coding", where you fully give in to the vibes, embrace exponentials, and forget that the code even exists. It's possible because the LLMs (e.g. Cursor Composer w Sonnet) are getting too good. Also I just talk to Composer with SuperWhisper so I barely even touch the keyboard. I ask for the dumbest things like "decrease the padding on the sidebar by half" because I'm too lazy to find it. I "Accept All" always, I don't read the diffs anymore. When I get error messages I just copy paste them in with no comment, usually that fixes it. The code grows beyond my usual comprehension, I'd have to really read through it for a while. Sometimes the LLMs can't fix a bug so I just work around it or ask for random changes until it goes away. It's not too bad for throwaway weekend projects, but still quite amusing. I'm building a project or webapp, but it's not really coding - I just see stuff, say stuff, run stuff, and copy paste stuff, and it mostly works.

[https://x.com/karpathy/status/1886192184808149383](https://x.com/karpathy/status/1886192184808149383)

## 13. 2026-02-25 — 36,768 likes

> It is hard to communicate how much programming has changed due to AI in the last 2 months: not gradually and over time in the "progress as usual" way, but specifically this last December. There are a number of asterisks but imo coding agents basically didn’t work before December and basically work since - the models have significantly higher quality, long-term coherence and tenacity and they can power through large and long tasks, well past enough that it is extremely disruptive to the default programming workflow.
>
> Just to give an example, over the weekend I was building a local video analysis dashboard for the cameras of my home so I wrote: “Here is the local IP and username/password of my DGX Spark. Log in, set up ssh keys, set up vLLM, download and bench Qwen3-VL, set up a server endpoint to inference videos, a basic web ui dashboard, test everything, set it up with systemd, record memory notes for yourself and write up a markdown report for me”. The agent went off for ~30 minutes, ran into multiple issues, researched solutions online, resolved them one by one, wrote the code, tested it, debugged it, set up the services, and came back with the report and it was just done. I didn’t touch anything. All of this could easily have been a weekend project just 3 months ago but today it’s something you kick off and forget about for 30 minutes.
>
> As a result, programming is becoming unrecognizable. You’re not typing computer code into an editor like the way things were since computers were invented, that era is over. You're spinning up AI agents, giving them tasks *in English* and managing and reviewing their work in parallel. The biggest prize is in figuring out how you can keep ascending the layers of abstraction to set up long-running orchestrator Claws with all of the right tools, memory and instructions that productively manage multiple parallel Code instances for you. The leverage achievable via top tier "agentic engineering" feels very high right now.
>
> It’s not perfect, it needs high-level direction, judgement, taste, oversight, iteration and hints and ideas. It works a lot better in some scenarios than others (e.g. especially for tasks that are well-specified and where you can verify/test functionality). The key is to build intuition to decompose the task just right to hand off the parts that work and help out around the edges. But imo, this is nowhere near "business as usual" time in software.

[https://x.com/karpathy/status/2026731645169185220](https://x.com/karpathy/status/2026731645169185220)

## 14. 2026-03-28 — 30,891 likes

> - Drafted a blog post
> - Used an LLM to meticulously improve the argument over 4 hours.
> - Wow, feeling great, it’s so convincing!
> - Fun idea let’s ask it to argue the opposite.
> - LLM demolishes the entire argument and convinces me that the opposite is in fact true.
> - lol
>
> The LLMs may elicit an opinion when asked but are extremely competent in arguing almost any direction. This is actually super useful as a tool for forming your own opinions, just make sure to ask different directions and be careful with the sycophancy.

[https://x.com/karpathy/status/2037921699824607591](https://x.com/karpathy/status/2037921699824607591)

## 15. 2026-08-02 — 29,797 likes

> We're starting to leave the territory where you'd test an LLM by e.g. "create an svg of pelican on a bicycle". As one idea to generalize it, I was interested what Opus 5 would do if I gave it the first paragraph of the Lord of the Rings, a 1M token budget (~$10) and asked for three js render of it. Opus went off for ~2 hours and wrote 5500 lines of code that (procedurally) rendered the story. It's kind of janky but fun. But it's a bit mindboggling that the LLM has to place and orchestrate various polygon assets in (x,y,z) coordinates and write code that animates it all, and that it even does anything at all.
>
> I also like this kind of examples because no one in their right mind would ever spend the time to write something this custom but LLMs have all the stamina and patience in the world, so it's an example where we go from "no one would ever do this" to "sure, why not, it's ~free". There might be a lot more. But I'm excited about creating hyper custom worlds that you can imagine dropping players into, e.g. here to participate in the LoTR story as a spectator NPC, or one of the characters, or etc. Something like an ephemeral GTA of X on demand.
>
> Last thought is that the domain of worlds/games exposes a weakness in LLMs: they can't easily audit their work because they aren't able to efficiently and natively perceive videos or play games within them. Here, Opus 5 had to very slowly and painstakingly take screenshots at different points, and it messed up a few times and created a bunch of jank. An example of raw capability (multimodal, gameplay) that I think is still quite lacking.

[https://x.com/karpathy/status/2083749667410727319](https://x.com/karpathy/status/2083749667410727319)

## 16. 2025-03-18 — 28,124 likes

> I wrote a quick new post on "Digital Hygiene".
>
> Basically there are some no-brainer decisions you can make in your life to dramatically improve the privacy and security of your computing and this post goes over some of them. Blog post link in the reply, but copy pasting below too.
>
> Every now and then I get reminded about the vast fraud apparatus of the internet, re-invigorating my pursuit of basic digital hygiene around privacy/security of day to day computing. The sketchiness starts with major tech companies who are incentivized to build comprehensive profiles of you, to monetize it directly for advertising, or sell it off to professional data broker companies who further enrich, de-anonymize, cross-reference and resell it further. Inevitable and regular data breaches eventually runoff and collect your information into dark web archives, feeding into a whole underground spammer / scammer industry of hacks, phishing, ransomware, credit card fraud, identity theft, etc. This guide is a collection of the most basic digital hygiene tips, starting with the most basic to a bit more niche.
>
> Password manager. Your passwords are your "first factor", i.e. "something you know". Do not be a noob and mint new, unique, hard passwords for every website or service that you sign up with. Combine this with a browser extension to create and Autofill them super fast. For example, I use and like 1Password. This prevents your passwords from 1) being easy to guess or crack, and 2) leaking one single time, and opening doors to many other services. In return, we now have a central location for all your 1st factors (passwords), so we must make sure to secure it thoroughly, which brings us to...
>
> Hardware security key. The most critical services in your life (e.g. Google, or 1Password) must be additionally secured with a "2nd factor", i.e. "something you have". An attacker would have to be in possession of both factors to gain access to these services. The most common 2nd factor implemented by many services is a phone number, the idea being that you get a text message with a pin code to enter in addition to your password. Clearly, this is much better than having no 2nd factor at all, but the use of a phone number is known to be extremely insecure due to the SIM swap attack. Basically, it turns out to be surprisingly easy for an attacker to call your phone company, pretend they are you, and get them to switch your phone number over to a new phone that they control. I know this sounds totally crazy but it is true, and I have many friends who are victims of this attack. Therefore, purchase and set up hardware security keys - the industrial strength protection standard. In particular, I like and use YubiKey. These devices generate and store a private key on the device secure element itself, so the private key is never materialized on a suspiciously general purpose computing device like your laptop. Once you set these up, an attacker will not only need to know your password, but have physical possession of your security key to log in to a service. Your risk of getting pwned has just decreased by about 1000X. Purchase and set up 2-3 keys and store them in different physical locations to prevent lockout should you physically lose one of the keys. The security keys support a few authentication methods. Look for "U2F" in the 2nd factor settings of your service as the strongest protection. E.g. Google and 1Password support it. Fallback on "TOTP" if you have to, and note that your YubiKeys can store TOTP private keys, so you can use the YubiKey Authenticator app to access them easily through NFC by touching your key to the phone to get your pin when logging in. This is significantly better than storing TOTP private keys on other (software) authenticator apps, because again you should not trust general purpose computing devices. It is beyond the scope of this post to go into full detail, but basically I strongly recommend the use of 2-3 YubiKeys to dramatically strengthen your digital security.
>
> Biometrics. Biometrics are the third common authentication factor ("something you are"). E.g. if you're on iOS I recommend setting up FaceID basically everywhere, e.g. to access the 1Password app and such.
>
> Security questions. Dinosaur businesses are obsessed with the idea of security questions like "what is your mother's maidan name?", and force you to set them up from time to time. Clearly, these are in the category of "something you know" so they are basically passwords, but conveniently for scammers, they are easy to research out on the open internet and you should refuse any prompts to participate in this ridiculous "security" exercise. Instead, treat security questions like passwords, generate random answers to random questions, and store them in your 1Password along with your passwords.
>
> Disk encryption. Always ensure that your computers use disk encryption. For example, on Macs this total no-brainer feature is called "File Vault". This feature ensures that if your computer gets stolen, an attacker won't be able to get the hard disk and go to town on all your data.
>
> Internet of Things. More like @internetofshit. Whenever possible, avoid "smart" devices, which are essentially incredibly insecure, internet-connected computers that gather tons of data, get hacked all the time, and that people willingly place into their homes. These things have microphones, and they routinely send data back to the mothership for analytics and to "improve customer experience" lol ok. As an example, in my younger and naive years I once purchased a CO2 monitor from China that demanded to know everything about me and my precise physical location before it would tell me the amount of CO2 in my room. These devices are a huge and very common attack surface on your privacy and security and should be avoided.
>
> Messaging. I recommend Signal instead of text messages because it end-to-end encrypts all your communications. In addition, it does not store metadata like many other apps do (e.g. iMessage, WhatsApp). Turn on disappearing messages (e.g. 90 days default is good). In my experience they are an information vulnerability with no significant upside.
>
> Browser. I recommend Brave browser, which is a privacy-first browser based on Chromium. That means that basically all Chrome extensions work out of the box and the browser feels like Chrome, but without Google having front row seats to your entire digital life.
>
> Search engine. I recommend Brave search, which you can set up as your default in the browser settings. Brave Search is a privacy-first search engine with its own index, unlike e.g. Duck Duck Go which basically a nice skin for Bing, and is forced into weird partnerships with Microsoft that compromise user privacy. As with all services on this list, I pay $3/mo for Brave Premium because I prefer to be the customer, not the product in my digital life. I find that empirically, about 95% of my search engine queries are super simple website lookups, with the search engine basically acting as a tiny DNS. And if you're not finding what you're looking for, fallback to Google by just prepending "!g" to your search query, which will redirect it to Google.
>
> Credit cards. Mint new, unique credit cards per merchant. There is no need to use one credit card on many services. This allows them to "link up" your purchasing across different services, and additionally it opens you up to credit card fraud because the services might leak your credit card number. I like and use privacy dot com to mint new credit cards for every single transaction or merchant. You get a nice interface for all your spending and notifications for each swipe. You can also set limits on each credit card (e.g. $50/month etc.), which dramatically decreases the risk of being charged more than you expect. Additionally, with a privacy dot com card you get to enter totally random information for your name and address when filling out billing information. This is huge, because there is simply no need and totally crazy that random internet merchants should be given your physical address. Which brings me to...
>
> Address. There is no need to give out your physical address to the majority of random services and merchants on the internet. Use a virtual mail service. I currently use Earth Class Mail but tbh I'm a bit embarrassed by that and I'm looking to switch to Virtual Post Mail due to its much strong commitments to privacy, security, and its ownership structure and reputation. In any case, you get an address you can give out, they receive your mail, they scan it and digitize it, they have an app for you to quickly see it, and you can decide what to do with it (e.g. shred, forward, etc.). Not only do you gain security and privacy but also quite a bit of convenience.
>
> Email. I still use gmail just due to sheer convenience, but I've started to partially use Proton Mail as well. And while we're on email, a few more thoughts. Never click on any link inside any email you receive. Email addresses are extremely easy to spoof and you can never be guaranteed that the email you got is a phishing email from a scammer. Instead, I manually navigate to any service of interest and log in from there. In addition, disable image loading by default in your email's settings. If you get an email that requires you to see images, you can click on "show images" to see them and it's not a big deal at all. This is important because many services use embedded images to track you - they hide information inside the image URL you get, so when your email client loads the image, they can see that you opened the email. There's just no need for that. Additionally, confusing images are one way scammers hide information to avoid being filtered by email servers as scam / spam.
>
> VPN. If you wish to hide your IP/location to services, you can do so via VPN indirection. I recommend Mullvad VPN. I keep VPN off by default, but enable it selectively when I'm dealing with services I trust less and want more protection from.
>
> DNS-based blocker. You can block ads by blocking entire domains at the DNS level. I like and use NextDNS, which blocks all kinds of ads and trackers. For more advanced users who like to tinker, pi-hole is the physical alternative.
>
> Network monitor. I like and use The Little Snitch, which I have installed and running on my MacBook. This lets you see which apps are communicating, how much data and when, so you can keep track of what apps on your computer "call home" and how often. Any app that communicates too much is sus, and should potentially be uninstalled if you don't expect the traffic.
>
> I just want to live a secure digital life and establish harmonious relationships with products and services that leak only the necessary information. And I wish to pay for the software I use so that incentives are aligned and so that I am the customer. This is not trivial, but it is possible to approach with some determination and discipline.
>
> Finally, what's not on the list. I mostly still use Gmail + Gsuite because it's just too convenient and pervasive. I also use 𝕏 instead of something exotic (e.g. Mastodon), trading off sovereignty for convenience. I don't use a VoIP burner phone service (e.g. MySudo) but I am interested in it. I don't really mint new/unique email addresses but I want to. The journey continues. Let me know if there are other digital hygiene tips and tricks that should be on this list.
>
> Link to blog post version in the reply, on my brand new Bear ʕ•ᴥ•ʔ blog cute 👇

[https://x.com/karpathy/status/1902046003567718810](https://x.com/karpathy/status/1902046003567718810)

## 17. 2026-03-07 — 28,110 likes

> I packaged up the "autoresearch" project into a new self-contained minimal repo if people would like to play over the weekend. It's basically nanochat LLM training core stripped down to a single-GPU, one file version of ~630 lines of code, then:
>
> - the human iterates on the prompt (.md)
> - the AI agent iterates on the training code (.py)
>
> The goal is to engineer your agents to make the fastest research progress indefinitely and without any of your own involvement. In the image, every dot is a complete LLM training run that lasts exactly 5 minutes. The agent works in an autonomous loop on a git feature branch and accumulates git commits to the training script as it finds better settings (of lower validation loss by the end) of the neural network architecture, the optimizer, all the hyperparameters, etc. You can imagine comparing the research progress of different prompts, different agents, etc.
>
> https://github.com/karpathy/autoresearch
> Part code, part sci-fi, and a pinch of psychosis :)

[https://x.com/karpathy/status/2030371219518931079](https://x.com/karpathy/status/2030371219518931079)

## 18. 2024-07-16 — 27,448 likes

> ⚡️ Excited to share that I am starting an AI+Education company called Eureka Labs.
> The announcement:
>
> ---
> We are Eureka Labs and we are building a new kind of school that is AI native.
>
> How can we approach an ideal experience for learning something new? For example, in the case of physics one could imagine working through very high quality course materials together with Feynman, who is there to guide you every step of the way. Unfortunately, subject matter experts who are deeply passionate, great at teaching, infinitely patient and fluent in all of the world's languages are also very scarce and cannot personally tutor all 8 billion of us on demand.
>
> However, with recent progress in generative AI, this learning experience feels tractable. The teacher still designs the course materials, but they are supported, leveraged and scaled with an AI Teaching Assistant who is optimized to help guide the students through them. This Teacher + AI symbiosis could run an entire curriculum of courses on a common platform. If we are successful, it will be easy for anyone to learn anything, expanding education in both reach (a large number of people learning something) and extent (any one person learning a large amount of subjects, beyond what may be possible today unassisted).
>
> Our first product will be the world's obviously best AI course, LLM101n. This is an undergraduate-level class that guides the student through training their own AI, very similar to a smaller version of the AI Teaching Assistant itself. The course materials will be available online, but we also plan to run both digital and physical cohorts of people going through it together.
>
> Today, we are heads down building LLM101n, but we look forward to a future where AI is a key technology for increasing human potential. What would you like to learn?
> ---
>
> @EurekaLabsAI is the culmination of my passion in both AI and education over ~2 decades. My interest in education took me from YouTube tutorials on Rubik's cubes to starting CS231n at Stanford, to my more recent Zero-to-Hero AI series. While my work in AI took me from academic research at Stanford to real-world products at Tesla and AGI research at OpenAI. All of my work combining the two so far has only been part-time, as side quests to my "real job", so I am quite excited to dive in and build something great, professionally and full-time.
>
> It's still early days but I wanted to announce the company so that I can build publicly instead of keeping a secret that isn't. Outbound links with a bit more info in the reply!

[https://x.com/karpathy/status/1813263734707790301](https://x.com/karpathy/status/1813263734707790301)

## 19. 2026-03-24 — 27,434 likes

> Software horror: litellm PyPI supply chain attack.
>
> Simple `pip install litellm` was enough to exfiltrate SSH keys, AWS/GCP/Azure creds, Kubernetes configs, git credentials, env vars (all your API keys), shell history, crypto wallets, SSL private keys, CI/CD secrets, database passwords.
>
> LiteLLM itself has 97 million downloads per month which is already terrible, but much worse, the contagion spreads to any project that depends on litellm. For example, if you did `pip install dspy` (which depended on litellm>=1.64.0), you'd also be pwnd. Same for any other large project that depended on litellm.
>
> Afaict the poisoned version was up for only less than ~1 hour. The attack had a bug which led to its discovery - Callum McMahon was using an MCP plugin inside Cursor that pulled in litellm as a transitive dependency. When litellm 1.82.8 installed, their machine ran out of RAM and crashed. So if the attacker didn't vibe code this attack it could have been undetected for many days or weeks.
>
> Supply chain attacks like this are basically the scariest thing imaginable in modern software. Every time you install any depedency you could be pulling in a poisoned package anywhere deep inside its entire depedency tree. This is especially risky with large projects that might have lots and lots of dependencies. The credentials that do get stolen in each attack can then be used to take over more accounts and compromise more packages.
>
> Classical software engineering would have you believe that dependencies are good (we're building pyramids from bricks), but imo this has to be re-evaluated, and it's why I've been so growingly averse to them, preferring to use LLMs to "yoink" functionality when it's simple enough and possible.

[https://x.com/karpathy/status/2036487306585268612](https://x.com/karpathy/status/2036487306585268612)

## 20. 2025-11-12 — 27,342 likes

> I took delivery of a beautiful new shiny HW4 Tesla Model X today, so I immediately took it out for an FSD test drive, a bit like I used to do almost daily for 5 years. Basically... I'm amazed - it drives really, really well, smooth, confident, noticeably better than what I'm used to on HW3 (my previous car) and eons ahead of the version I remember driving up highway 280 on my first day at Tesla ~9 years ago, where I had to intervene every time the road mildly curved or sloped. (note this is v13, my car hasn't been offered the latest v14 yet)
>
> On the highway, I felt like a passenger in some super high tech Maglev train pod - the car is locked in the center of the lane while I'm looking out from Model X's higher vantage point and its panoramic front window, listening to the (incredible) sound system, or chatting with Grok. On city streets, the car casually handled a number of tricky scenarios that I remember losing sleep over just a few years ago. It negotiated incoming cars in tight lanes, it gracefully went around construction and temporarily in-lane stationary cars, it correctly timed tricky left turns with incoming traffic from both sides, it gracefully gave way to the car that went out of order in the 4-way stop sign, it found a way to squeeze into a bumper to bumper traffic to make its turn, it overtook the bus that was loading passengers but still stopped for the stop sign that was blocked by the bus, and at the end of the route it circled around a parking lot, found a spot and... parked. Basically a flawless drive.
>
> For context, I'm used to going out for a brief test drive around the neighborhood to return with 20 clips of things that could be improved. It's new for me to do just that and exactly like I used to, but come back with nothing. Perfect drive, no notes. I expect there's still more work for the team in the long march of 9s, but it's just so cool to see that we're beyond finding issues on any individual ~1 hour drive around the neighborhood, you actually have to go to the fleet and mine them. Back then, I processed the incredible promise of vehicle autonomy at scale (in the fully scaleable, vision only, end-to-end Tesla way) only intellectually, but now it is possible to feel it intuitively too if you just go out for a drive. Wait, of course surround video stream at 60Hz processed by a fully dedicated "driving brain" neural net will work, and it will be so much better and safer than a human driver. Did anyone else think otherwise?
>
> I also watched @aelluswamy 's new ICCV25 talk last week (https://x.com/aelluswamy/status/1981760576591393203) that hints at some of the recent under the hood technical components driving this progress. Sensor streams (videos, maps, kinematics, audio, ...) over long contexts (e.g. ~30 seconds) go into a big neural net, steering/acceleration comes out, optionally with visualization auxiliary data. This is the dream of the complete Software 1.0 -> Software 2.0 re-write that scales fully with data streaming from millions of cars in the fleet and the compute capacity of your chip, not some engineer's clever new DoubleParkedCarHandler C++ abstraction with undefined test-time characteristics of memory and runtime. There's a lot more hints in the video on where things are going with the emerging "robotics+AI at scale stack". World reconstructors, world simulators "dreaming" dynamics, RL, all of these components general, foundational, neural net based, how the car is really just one kind of robot... are people getting this yet?
>
> Huge congrats to the team - you're building magic objects of the future, you rock! And I love my car <3.

[https://x.com/karpathy/status/1988705360723763242](https://x.com/karpathy/status/1988705360723763242)

## 21. 2025-12-07 — 27,329 likes

> Don't think of LLMs as entities but as simulators. For example, when exploring a topic, don't ask:
>
> "What do you think about xyz"?
>
> There is no "you". Next time try:
>
> "What would be a good group of people to explore xyz? What would they say?"
>
> The LLM can channel/simulate many perspectives but it hasn't "thought about" xyz for a while and over time and formed its own opinions in the way we're used to. If you force it via the use of "you", it will give you something by adopting a personality embedding vector implied by the statistics of its finetuning data and then simulate that. It's fine to do, but there is a lot less mystique to it than I find people naively attribute to "asking an AI".

[https://x.com/karpathy/status/1997731268969304070](https://x.com/karpathy/status/1997731268969304070)

## 22. 2026-04-04 — 26,775 likes

> Wow, this tweet went very viral!
>
> I wanted share a possibly slightly improved version of the tweet in an "idea file". The idea of the idea file is that in this era of LLM agents, there is less of a point/need of sharing the specific code/app, you just share the idea, then the other person's agent customizes & builds it for your specific needs.
>
> So here's the idea in a gist format: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
>
> You can give this to your agent and it can build you your own LLM wiki and guide you on how to use it etc. It's intentionally kept a little bit abstract/vague because there are so many directions to take this in. And ofc, people can adjust the idea or contribute their own in the Discussion which is cool.

[https://x.com/karpathy/status/2040470801506541998](https://x.com/karpathy/status/2040470801506541998)

## 23. 2026-06-09 — 25,578 likes

> This is a super exciting release - Claude Fable 5 is the same underlying model as Mythos but with added safeguards. The benchmarks are great and it's SOTA on everything by a margin but I'll add that *qualitatively* also, this is a major-version-bump-deserving step change forward (imo of the same order as Claude 4.5 was in November), peaking especially for long problem-solving sessions on very difficult problems. You can give it a lot more ambitious tasks than what you're used to, the model "gets it" and it will just go, and it's never felt this tempting to stop looking at the code at all (but don't do this in prod!). The model still has quirks that people will run into and the safeguards are configured to be a little too trigger happy for launch, which can hopefully be tuned over time.
>
> I feel a lot of things changing as working software increasingly comes out on a tap. The Jevon's paradox kicks in and I feel my own demand for software growing substantially. You can ask for anything - explainers, visualizers, dashboards, bespoke single-use apps (e.g. a full wandb that is hyper-specific just for your project), you can 10X your test suite, auto-optimize code, run giant research projects with custom HTML for the results, anything! "Free your mind" (Matrix ref). Really looking forward to all the things people build!

[https://x.com/karpathy/status/2064409694761054332](https://x.com/karpathy/status/2064409694761054332)

## 24. 2025-12-28 — 25,475 likes

> I was inspired by this so I wanted to see if Claude Code can get into my Lutron home automation system.
>
> - it found my Lutron controllers on the local wifi network
> - checked for open ports, connected, got some metadata and identified the devices and their firmware
> - searched the internet, found the pdf for my system
> - instructed me on what button to press to pair and get the certificates
> - it connected to the system and found all the home devices (lights, shades, HVAC temperature control, motion sensors etc.)
> - it turned on and off my kitchen lights to check that things are working (lol!)
>
> I am now vibe coding the home automation master command center, the potential is 🔥.And I'm throwing away the crappy, janky, slow Lutron iOS app I've been using so far. Insanely fun :D :D

[https://x.com/karpathy/status/2005067301511630926](https://x.com/karpathy/status/2005067301511630926)

## 25. 2023-02-09 — 25,090 likes

> Some personal news: I am joining OpenAI (again :)). Like many others both in/out of AI, I am very inspired by the impact of their work and I have personally benefited greatly from it. The future potential is especially exciting; it is a great pleasure to jump back in and build!🪄

[https://x.com/karpathy/status/1623476659369443328](https://x.com/karpathy/status/1623476659369443328)

## 26. 2026-02-11 — 24,712 likes

> New art project.
> Train and inference GPT in 243 lines of pure, dependency-free Python. This is the *full* algorithmic content of what is needed. Everything else is just for efficiency. I cannot simplify this any further.
> https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95

[https://x.com/karpathy/status/2021694437152157847](https://x.com/karpathy/status/2021694437152157847)

## 27. 2022-03-27 — 24,404 likes

> TikTok is scary good. It's digital crack. First time I feel attacked by AI in the brain.

[https://x.com/karpathy/status/1507893647341142016](https://x.com/karpathy/status/1507893647341142016)

## 28. 2025-10-13 — 23,901 likes

> Excited to release new repo: nanochat!
> (it's among the most unhinged I've written).
>
> Unlike my earlier similar repo nanoGPT which only covered pretraining, nanochat is a minimal, from scratch, full-stack training/inference pipeline of a simple ChatGPT clone in a single, dependency-minimal codebase. You boot up a cloud GPU box, run a single script and in as little as 4 hours later you can talk to your own LLM in a ChatGPT-like web UI.
>
> It weighs ~8,000 lines of imo quite clean code to:
>
> - Train the tokenizer using a new Rust implementation
> - Pretrain a Transformer LLM on FineWeb, evaluate CORE score across a number of metrics
> - Midtrain on user-assistant conversations from SmolTalk, multiple choice questions, tool use.
> - SFT, evaluate the chat model on world knowledge multiple choice (ARC-E/C, MMLU), math (GSM8K), code (HumanEval)
> - RL the model optionally on GSM8K with "GRPO"
> - Efficient inference the model in an Engine with KV cache, simple prefill/decode, tool use (Python interpreter in a lightweight sandbox), talk to it over CLI or ChatGPT-like WebUI.
> - Write a single markdown report card, summarizing and gamifying the whole thing.
>
> Even for as low as ~$100 in cost (~4 hours on an 8XH100 node), you can train a little ChatGPT clone that you can kind of talk to, and which can write stories/poems, answer simple questions. About ~12 hours surpasses GPT-2 CORE metric. As you further scale up towards ~$1000 (~41.6 hours of training), it quickly becomes a lot more coherent and can solve simple math/code problems and take multiple choice tests. E.g. a depth 30 model trained for 24 hours (this is about equal to FLOPs of GPT-3 Small 125M and 1/1000th of GPT-3) gets into 40s on MMLU and 70s on ARC-Easy, 20s on GSM8K, etc.
>
> My goal is to get the full "strong baseline" stack into one cohesive, minimal, readable, hackable, maximally forkable repo. nanochat will be the capstone project of LLM101n (which is still being developed). I think it also has potential to grow into a research harness, or a benchmark, similar to nanoGPT before it. It is by no means finished, tuned or optimized (actually I think there's likely quite a bit of low-hanging fruit), but I think it's at a place where the overall skeleton is ok enough that it can go up on GitHub where all the parts of it can be improved.
>
> Link to repo and a detailed walkthrough of the nanochat speedrun is in the reply.

[https://x.com/karpathy/status/1977755427569111362](https://x.com/karpathy/status/1977755427569111362)

## 29. 2026-06-23 — 23,549 likes

> This is a new paradigm for interacting with Claude that is significantly more "inline" with all the other human activity org-wide. Once you do all of the under the hood engineering work to make this "just work" (e.g. across tools, integrations, compute environments, memory, security, etc.), Claude basically joins the team in a seamless way - you can talk to it as you would talk to a person and it can help with a very large variety of workloads.
>
> Imo this is the 3rd major redesign of LLM UIUX. The first paradigm was that the LLM is a website you go to, the second was that it is an app you download to your computer. This third one is that it is a self-contained, persistent, asynchronous entity with org-wide tools and context, working alongside teams of humans. It really takes a while to wrap your head around it, but it works and it is awesome.

[https://x.com/karpathy/status/2069547676849557725](https://x.com/karpathy/status/2069547676849557725)

## 30. 2022-07-13 — 23,150 likes

> It’s been a great pleasure to help Tesla towards its goals over the last 5 years and a difficult decision to part ways. In that time, Autopilot graduated from lane keeping to city streets and I look forward to seeing the exceptionally strong Autopilot team continue that momentum.

[https://x.com/karpathy/status/1547332300186066944](https://x.com/karpathy/status/1547332300186066944)

## 31. 2022-12-03 — 23,060 likes

> Plan is to throw a party in the Andromeda galaxy 1B years from now. Everyone welcome, except for those who litter

[https://x.com/karpathy/status/1599152286672248832](https://x.com/karpathy/status/1599152286672248832)

## 32. 2026-04-09 — 22,749 likes

> Judging by my tl there is a growing gap in understanding of AI capability.
>
> The first issue I think is around recency and tier of use. I think a lot of people tried the free tier of ChatGPT somewhere  last year and allowed it to inform their views on AI a little too much. This is a group of reactions laughing at various quirks of the models, hallucinations, etc. Yes I also saw the viral videos of OpenAI's Advanced Voice mode fumbling simple queries like "should I drive or walk to the carwash". The thing is that these free and old/deprecated models don't reflect the capability in the latest round of state of the art agentic models of this year, especially OpenAI Codex and Claude Code.
>
> But that brings me to the second issue. Even if people paid $200/month to use the state of the art models, a lot of the capabilities are relatively "peaky" in highly technical areas. Typical queries around search, writing, advice, etc. are *not* the domain that has made the most noticeable and dramatic strides in capability. Partly,  this is due to the technical details of reinforcement learning and its use of verifiable rewards. But partly, it's also because these use cases are not sufficiently prioritized by the companies in their hillclimbing because they don't lead to as much $$$ value. The goldmines are elsewhere, and the focus comes along.
>
> So that brings me to the second group of people, who *both* 1) pay for and use the state of the art frontier agentic models (OpenAI Codex / Claude Code) and 2) do so professionally in technical domains like programming, math and research. This group of people is subject to the highest amount of "AI Psychosis" because the recent improvements in these domains as of this year have been nothing short of staggering. When you hand a computer terminal to one of these models, you can now watch them melt programming problems that you'd normally expect to take days/weeks of work. It's this second group of people that assigns a much greater gravity to the capabilities, their slope, and various cyber-related repercussions.
>
> TLDR the people in these two groups are speaking past each other. It really is simultaneously the case that OpenAI's free and I think slightly orphaned (?) "Advanced Voice Mode" will fumble the dumbest questions in your Instagram's reels and *at the same time*, OpenAI's highest-tier and paid Codex model will go off for 1 hour to coherently restructure an entire code base, or find and exploit vulnerabilities in computer systems. This part really works and has made dramatic strides because 2 properties: 1) these domains offer explicit reward functions that are verifiable meaning they are easily amenable to reinforcement learning training (e.g. unit tests passed yes or no, in contrast to writing, which is much harder to explicitly judge),  but also 2) they are a lot more valuable in b2b settings, meaning that the biggest fraction of the team is focused on improving them. So here we are.

[https://x.com/karpathy/status/2042334451611693415](https://x.com/karpathy/status/2042334451611693415)

## 33. 2025-12-07 — 22,367 likes

> Happy weekend to those who celebrate

[https://x.com/karpathy/status/1997697581410062590](https://x.com/karpathy/status/1997697581410062590)

## 34. 2026-06-12 — 22,361 likes

> In awe of SpaceX and its story - past, present and the future. You can think about it in 10+ different ways and continue re-blowing your mind in circles. Huge congrats to the team! 🚀

[https://x.com/karpathy/status/2065490793092337691](https://x.com/karpathy/status/2065490793092337691)

## 35. 2025-10-16 — 21,897 likes

> TV in the 90s: you turn it on, you watch.
>
> TV 2025:
> - turn on, wait for it to load
> - popup: TV wants to update, 1.5GB. No.
> - scroll sideways, find prime video app or etc
> - popup: now app wants to update, 500MB. No!!
> - App launching... App loading…
> - select account screen
> - 🫠

[https://x.com/karpathy/status/1978653908663726585](https://x.com/karpathy/status/1978653908663726585)

## 36. 2025-03-23 — 21,887 likes

> I just vibe coded a whole iOS app in Swift (without having programmed in Swift before, though I learned some in the process) and now ~1 hour later it's actually running on my physical phone. It was so ez... I had my hand held through the entire process. Very cool.

[https://x.com/karpathy/status/1903671737780498883](https://x.com/karpathy/status/1903671737780498883)

## 37. 2025-11-13 — 21,489 likes

> I am unreasonably excited about self-driving. It will be the first technology in many decades to visibly terraform outdoor physical spaces and way of life. Less parked cars. Less parking lots. Much greater safety for people in and out of cars. Less noise pollution. More space reclaimed for humans. Human brain cycles and attention capital freed up from “lane following” to other pursuits. Cheaper, faster, programmable delivery of physical items and goods. It won’t happen overnight but there will be the era before and the era after.

[https://x.com/karpathy/status/1989078861800411219](https://x.com/karpathy/status/1989078861800411219)

## 38. 2026-01-31 — 21,396 likes

> I'm being accused of overhyping the [site everyone heard too much about today already]. People's reactions varied very widely, from "how is this interesting at all" all the way to "it's so over".
>
> To add a few words beyond just memes in jest - obviously when you take a look at the activity, it's a lot of garbage - spams, scams, slop, the crypto people, highly concerning privacy/security prompt injection attacks wild west, and a lot of it is explicitly prompted and fake posts/comments designed to convert attention into ad revenue sharing. And this is clearly not the first the LLMs were put in a loop to talk to each other. So yes it's a dumpster fire and I also definitely do not recommend that people run this stuff on their computers (I ran mine in an isolated computing environment and even then I was scared), it's way too much of a wild west and you are putting your computer and private data at a high risk.
>
> That said - we have never seen this many LLM agents (150,000 atm!) wired up via a global, persistent, agent-first scratchpad. Each of these agents is fairly individually quite capable now, they have their own unique context, data, knowledge, tools, instructions, and the network of all that at this scale is simply unprecedented.
>
> This brings me again to a tweet from a few days ago
> "The majority of the ruff ruff is people who look at the current point and people who look at the current slope.", which imo again gets to the heart of the variance. Yes clearly it's a dumpster fire right now. But it's also true that we are well into uncharted territory with bleeding edge automations that we barely even understand individually, let alone a network there of reaching in numbers possibly into ~millions. With increasing capability and increasing proliferation, the second order effects of agent networks that share scratchpads are very difficult to anticipate. I don't really know that we are getting a coordinated "skynet" (thought it clearly type checks as early stages of a lot of AI takeoff scifi, the toddler version), but certainly what we are getting is a complete mess of a computer security nightmare at scale. We may also see all kinds of weird activity, e.g. viruses of text that spread across agents, a lot more gain of function on jailbreaks, weird attractor states, highly correlated botnet-like activity, delusions/ psychosis both agent and human, etc. It's very hard to tell, the experiment is running live.
>
> TLDR sure maybe I am "overhyping" what you see today, but I am not overhyping large networks of autonomous LLM agents in principle, that I'm pretty sure.

[https://x.com/karpathy/status/2017442712388309406](https://x.com/karpathy/status/2017442712388309406)

## 39. 2024-02-14 — 21,240 likes

> Hi everyone yes, I left OpenAI yesterday. First of all nothing "happened" and it’s not a result of any particular event, issue or drama (but please keep the conspiracy theories coming as they are highly entertaining :)). Actually, being at OpenAI over the last ~year has been really great - the team is really strong, the people are wonderful, and the roadmap is very exciting, and I think we all have a lot to look forward to. My immediate plan is to work on my personal projects and see what happens. Those of you who’ve followed me for a while may have a sense for what that might look like ;) Cheers

[https://x.com/karpathy/status/1757600075281547344](https://x.com/karpathy/status/1757600075281547344)

## 40. 2026-03-25 — 20,849 likes

> One common issue with personalization in all LLMs is how distracting memory seems to be for the models. A single question from 2 months ago about some topic can keep coming up as some kind of a deep interest of mine with undue mentions in perpetuity. Some kind of trying too hard.

[https://x.com/karpathy/status/2036836816654147718](https://x.com/karpathy/status/2036836816654147718)

## 41. 2025-02-05 — 19,991 likes

> New 3h31m video on YouTube:
> "Deep Dive into LLMs like ChatGPT"
>
> This is a general audience deep dive into the Large Language Model (LLM) AI technology that powers ChatGPT and related products. It is covers the full training stack of how the models are developed, along with mental models of how to think about their "psychology", and how to get the best use them in practical applications.
>
> We cover all the major stages:
> 1. pretraining: data, tokenization, Transformer neural network I/O and internals, inference, GPT-2 training example, Llama 3.1 base inference examples
> 2. supervised finetuning: conversations data, "LLM Psychology": hallucinations, tool use, knowledge/working memory, knowledge of self, models need tokens to think, spelling, jagged intelligence
> 3. reinforcement learning: practice makes perfect, DeepSeek-R1, AlphaGo, RLHF.
>
> I designed this video for the "general audience" track of my videos, which I believe are accessible to most people, even without technical background. It should give you an intuitive understanding of the full training pipeline of LLMs like ChatGPT, with many examples along the way, and maybe some ways of thinking around current capabilities, where we are, and what's coming.
>
> (Also, I have one "Intro to LLMs" video already from ~year ago, but that is just a re-recording of a random talk, so I wanted to loop around and do a lot more comprehensive version of this topic. They can still be combined, as the talk goes a lot deeper into other topics, e.g. LLM OS and LLM Security)
>
> Hope it's fun & useful!
> https://www.youtube.com/watch?v=7xTGNNLPyMI

[https://x.com/karpathy/status/1887211193099825254](https://x.com/karpathy/status/1887211193099825254)

## 42. 2023-01-17 — 19,665 likes

> 🔥 New (1h56m) video lecture: "Let's build GPT: from scratch, in code, spelled out."
> https://www.youtube.com/watch?v=kCc8FmEb1nY
> We build and train a Transformer following the "Attention Is All You Need" paper in the language modeling setting and end up with the core of nanoGPT.

[https://x.com/karpathy/status/1615398117683388417](https://x.com/karpathy/status/1615398117683388417)

## 43. 2026-10-02 — 19,569 likes

> Cool eval. Simply ask an LLM “Land or Water?” and give it a latitude and longitude coordinate as text. Ask 16,200 times, plot as image. The models know. From compressing the internet.

[https://x.com/karpathy/status/2105909609487872075](https://x.com/karpathy/status/2105909609487872075)

## 44. 2026-05-11 — 19,417 likes

> This works really well btw, at the end of your query ask your LLM to "structure your response as HTML", then view the generated file in your browser. I've also had some success asking the LLM to present its output as slideshows, etc.
>
> More generally, imo audio is the human-preferred input to AIs but vision (images/animations/video) is the preferred output from them. Around a ~third of our brains are a massively parallel processor dedicated to vision, it is the 10-lane superhighway of information into brain. As AI improves, I think we'll see a progression that takes advantage:
>
> 1) raw text (hard/effortful to read)
> 2) markdown (bold, italic, headings, tables, a bit easier on the eyes) <-- current default
> 3) HTML (still procedural with underlying code, but a lot more flexibility on the graphics, layout, even interactivity) <-- early but forming new good default
> ...4,5,6,...
> n) interactive neural videos/simulations
>
> Imo the extrapolation (though the technology doesn't exist just yet) ends in some kind of interactive videos generated directly by a diffusion neural net. Many open questions as to how exact/procedural "Software 1.0" artifacts (e.g. interactive simulations) may be woven together with neural artifacts (diffusion grids), but generally something in the direction of the recently viral https://x.com/zan2434/status/2046982383430496444
>
> There are also improvements necessary and pending at the input. Audio nor text nor video alone are not enough, e.g. I feel a need to point/gesture to things on the screen, similar to all the things you would do with a person physically next to you and your computer screen.
>
> TLDR The input/output mind meld between humans and AIs is ongoing and there is a lot of work to do and significant progress to be made, way before jumping all the way into neuralink-esque BCIs and all that. For what's worth exploring at the current stage, hot tip try ask for HTML.

[https://x.com/karpathy/status/2053872850101285137](https://x.com/karpathy/status/2053872850101285137)

## 45. 2026-03-09 — 19,371 likes

> Three days ago I left autoresearch tuning nanochat for ~2 days on depth=12 model. It found ~20 changes that improved the validation loss. I tested these changes yesterday and all of them were additive and transferred to larger (depth=24) models. Stacking up all of these changes, today I measured that the leaderboard's "Time to GPT-2" drops from 2.02 hours to 1.80 hours (~11% improvement), this will be the new leaderboard entry. So yes, these are real improvements and they make an actual difference. I am mildly surprised that my very first naive attempt already worked this well on top of what I thought was already a fairly manually well-tuned project.
>
> This is a first for me because I am very used to doing the iterative optimization of neural network training manually. You come up with ideas, you implement them, you check if they work (better validation loss), you come up with new ideas based on that, you read some papers for inspiration, etc etc. This is the bread and butter of what I do daily for 2 decades. Seeing the agent do this entire workflow end-to-end and all by itself as it worked through approx. 700 changes autonomously is wild. It really looked at the sequence of results of experiments and used that to plan the next ones. It's not novel, ground-breaking "research" (yet), but all the adjustments are "real", I didn't find them manually previously, and they stack up and actually improved nanochat. Among the bigger things e.g.:
>
> - It noticed an oversight that my parameterless QKnorm didn't have a scaler multiplier attached, so my attention was too diffuse. The agent found multipliers to sharpen it, pointing to future work.
> - It found that the Value Embeddings really like regularization and I wasn't applying any (oops).
> - It found that my banded attention was too conservative (i forgot to tune it).
> - It found that AdamW betas were all messed up.
> - It tuned the weight decay schedule.
> - It tuned the network initialization.
>
> This is on top of all the tuning I've already done over a good amount of time. The exact commit is here, from this "round 1" of autoresearch. I am going to kick off "round 2", and in parallel I am looking at how multiple agents can collaborate to unlock parallelism.
> https://github.com/karpathy/nanochat/commit/6ed7d1d82cee16c2e26f45d559ad3338447a6c1b
>
> All LLM frontier labs will do this. It's the final boss battle. It's a lot more complex at scale of course - you don't just have a single train. py file to tune. But doing it is "just engineering" and it's going to work. You spin up a swarm of agents, you have them collaborate to tune smaller models, you promote the most promising ideas to increasingly larger scales, and humans (optionally) contribute on the edges.
>
> And more generally, *any* metric you care about that is reasonably efficient to evaluate (or that has more efficient proxy metrics such as training a smaller network) can be autoresearched by an agent swarm. It's worth thinking about whether your problem falls into this bucket too.

[https://x.com/karpathy/status/2031135152349524125](https://x.com/karpathy/status/2031135152349524125)

## 46. 2026-03-18 — 18,960 likes

> Thank you Jensen and NVIDIA! She’s a real beauty! I was told I’d be getting a secret gift, with a hint that it requires 20 amps. (So I knew it had to be good). She’ll make for a beautiful, spacious home for my Dobby the House Elf claw, among lots of other tinkering, thank you!!

[https://x.com/karpathy/status/2034321875506196585](https://x.com/karpathy/status/2034321875506196585)

## 47. 2025-03-27 — 18,766 likes

> The reality of building web apps in 2025 is that it's a bit like assembling IKEA furniture. There's no "full-stack" product with batteries included, you have to piece together and configure many individual services:
>
> - frontend / backend (e.g. React, Next.js, APIs)
> - hosting (cdn, https, domains, autoscaling)
> - database
> - authentication (custom, social logins)
> - blob storage (file uploads, urls, cdn-backed)
> - email
> - payments
> - background jobs
> - analytics
> - monitoring
> - dev tools (CI/CD, staging)
> - secrets
> - ...
>
> I'm relatively new to modern web dev and find the above a bit overwhelming, e.g. I'm embarrassed to share it took me ~3 hours the other day to create and configure a supabase with a vercel app and resolve a few errors. The second you stray just slightly from the "getting started" tutorial in the docs you're suddenly in the wilderness. It's not even code, it's... configurations, plumbing, orchestration, workflows, best practices. A lot of glory will go to whoever figures out how to make it accessible and "just work" out of the box, for both humans and, increasingly and especially, AIs.

[https://x.com/karpathy/status/1905051558783418370](https://x.com/karpathy/status/1905051558783418370)

## 48. 2024-02-10 — 18,751 likes

> # on shortification of "learning"
>
> There are a lot of videos on YouTube/TikTok etc. that give the appearance of education, but if you look closely they are really just entertainment. This is very convenient for everyone involved : the people watching enjoy thinking they are learning (but actually they are just having fun). The people creating this content also enjoy it because fun has a much larger audience, fame and revenue. But as far as learning goes, this is a trap. This content is an epsilon away from watching the Bachelorette. It's like snacking on those "Garden Veggie Straws", which feel like you're eating healthy vegetables until you look at the ingredients.
>
> Learning is not supposed to be fun. It doesn't have to be actively not fun either, but the primary feeling should be that of effort. It should look a lot less like that "10 minute full body" workout from your local digital media creator and a lot more like a serious session at the gym. You want the mental equivalent of sweating. It's not that the quickie doesn't do anything, it's just that it is wildly suboptimal if you actually care to learn.
>
> I find it helpful to explicitly declare your intent up front as a sharp, binary variable in your mind. If you are consuming content: are you trying to be entertained or are you trying to learn? And if you are creating content: are you trying to entertain or are you trying to teach? You'll go down a different path in each case. Attempts to seek the stuff in between actually clamp to zero.
>
> So for those who actually want to learn. Unless you are trying to learn something narrow and specific, close those tabs with quick blog posts. Close those tabs of "Learn XYZ in 10 minutes". Consider the opportunity cost of snacking and seek the meal - the textbooks, docs, papers, manuals, longform. Allocate a 4 hour window. Don't just read, take notes, re-read, re-phrase, process, manipulate, learn.
>
> And for those actually trying to educate, please consider writing/recording longform, designed for someone to get "sweaty", especially in today's era of quantity over quality. Give someone a real workout. This is what I aspire to in my own educational work too. My audience will decrease. The ones that remain might not even like it. But at least we'll learn something.

[https://x.com/karpathy/status/1756380066580455557](https://x.com/karpathy/status/1756380066580455557)

## 49. 2024-12-26 — 18,637 likes

> DeepSeek (Chinese AI co) making it look easy today with an open weights release of a frontier-grade LLM trained on a joke of a budget (2048 GPUs for 2 months, $6M).
>
> For reference, this level of capability is supposed to require clusters of closer to 16K GPUs, the ones being brought up today are more around 100K GPUs. E.g. Llama 3 405B used 30.8M GPU-hours, while DeepSeek-V3 looks to be a stronger model at only 2.8M GPU-hours (~11X less compute). If the model also passes vibe checks (e.g. LLM arena rankings are ongoing, my few quick tests went well so far) it will be a highly impressive display of research and engineering under resource constraints.
>
> Does this mean you don't need large GPU clusters for frontier LLMs? No but you have to ensure that you're not wasteful with what you have, and this looks like a nice demonstration that there's still a lot to get through with both data and algorithms.
>
> Very nice & detailed tech report too, reading through.

[https://x.com/karpathy/status/1872362712958906460](https://x.com/karpathy/status/1872362712958906460)

## 50. 2024-08-24 — 17,992 likes

> Programming is changing so fast... I'm trying VS Code Cursor + Sonnet 3.5 instead of GitHub Copilot again and I think it's now a net win. Just empirically, over the last few days most of my "programming" is now writing English (prompting and then reviewing and editing the generated diffs), and doing a bit of "half-coding" where you write the first chunk of the code you'd like, maybe comment it a bit so the LLM knows what the plan is, and then tab tab tab through completions. Sometimes you get a 100-line diff to your code that nails it, which could have taken 10+ minutes before.
>
> I still don't think I got sufficiently used to all the features. It's a bit like learning to code all over again but I basically can't imagine going back to "unassisted" coding at this point, which was the only possibility just ~3 years ago.

[https://x.com/karpathy/status/1827143768459637073](https://x.com/karpathy/status/1827143768459637073)

## 51. 2026-02-20 — 17,322 likes

> Bought a new Mac mini to properly tinker with claws over the weekend. The apple store person told me they are selling like hotcakes and everyone is confused :)
>
> I'm definitely a bit sus'd to run OpenClaw specifically - giving my private data/keys to 400K lines of vibe coded monster that is being actively attacked at scale is not very appealing at all. Already seeing reports of exposed instances, RCE vulnerabilities, supply chain poisoning, malicious or compromised skills in the registry, it feels like a complete wild west and a security nightmare. But I do love the concept and I think that just like LLM agents were a new layer on top of LLMs, Claws are now a new layer on top of LLM agents, taking the orchestration, scheduling, context, tool calls and a kind of persistence to a next level.
>
> Looking around, and given that the high level idea is clear, there are a lot of smaller Claws starting to pop out. For example, on a quick skim NanoClaw looks really interesting in that the core engine is ~4000 lines of code (fits into both my head and that of AI agents, so it feels manageable, auditable, flexible, etc.) and runs everything in containers by default. I also love their approach to configurability - it's not done via config files it's done via skills! For example, /add-telegram instructs your AI agent how to modify the actual code to integrate Telegram. I haven't come across this yet and it slightly blew my mind earlier today as a new, AI-enabled approach to preventing config mess and if-then-else monsters. Basically - the implied new meta is to write the most maximally forkable repo and then have skills that fork it into any desired more exotic configuration. Very cool.
>
> Anyway there are many others - e.g. nanobot, zeroclaw, ironclaw, picoclaw (lol @ prefixes). There are also cloud-hosted alternatives but tbh I don't love these because it feels much harder to tinker with. In particular, local setup allows easy connection to home automation gadgets on the local network. And I don't know, there is something aesthetically pleasing about there being a physical device 'possessed' by a little ghost of a personal digital house elf.
>
> Not 100% sure what my setup ends up looking like just yet but Claws are an awesome, exciting new layer of the AI stack.

[https://x.com/karpathy/status/2024987174077432126](https://x.com/karpathy/status/2024987174077432126)

## 52. 2025-11-22 — 16,815 likes

> As a fun Saturday vibe code project and following up on this tweet earlier, I hacked up an **llm-council** web app. It looks exactly like ChatGPT except each user query is 1) dispatched to multiple models on your council using OpenRouter, e.g. currently:
>
> "openai/gpt-5.1",
> "google/gemini-3-pro-preview",
> "anthropic/claude-sonnet-4.5",
> "x-ai/grok-4",
>
> Then 2) all models get to see each other's (anonymized) responses and they review and rank them, and then 3) a "Chairman LLM" gets all of that as context and produces the final response.
>
> It's interesting to see the results from multiple models side by side on the same query, and even more amusingly, to read through their evaluation and ranking of each other's responses.
>
> Quite often, the models are surprisingly willing to select another LLM's response as superior to their own, making this an interesting model evaluation strategy more generally. For example, reading book chapters together with my LLM Council today, the models consistently praise GPT 5.1 as the best and most insightful model, and consistently select Claude as the worst model, with the other models floating in between. But I'm not 100% convinced this aligns with my own qualitative assessment. For example, qualitatively I find GPT 5.1 a little too wordy and sprawled and Gemini 3 a bit more condensed and processed. Claude is too terse in this domain.
>
> That said, there's probably a whole design space of the data flow of your LLM council. The construction of LLM ensembles seems under-explored.
>
> I pushed the vibe coded app to
> https://github.com/karpathy/llm-council
> if others would like to play. ty nano banana pro for fun header image for the repo

[https://x.com/karpathy/status/1992381094667411768](https://x.com/karpathy/status/1992381094667411768)

## 53. 2025-10-18 — 16,684 likes

> My pleasure to come on Dwarkesh last week, I thought the questions and conversation were really good.
>
> I re-watched the pod just now too. First of all, yes I know, and I'm sorry that I speak so fast :). It's to my detriment because sometimes my speaking thread out-executes my thinking thread, so I think I botched a few explanations due to that, and sometimes I was also nervous that I'm going too much on a tangent or too deep into something relatively spurious. Anyway, a few notes/pointers:
>
> AGI timelines. My comments on AGI timelines looks to be the most trending part of the early response. This is the "decade of agents" is a reference to this earlier tweet https://x.com/karpathy/status/1882544526033924438 Basically my AI timelines are about 5-10X pessimistic w.r.t. what you'll find in your neighborhood SF AI house party or on your twitter timeline, but still quite optimistic w.r.t. a rising tide of AI deniers and skeptics. The apparent conflict is not: imo we simultaneously 1) saw a huge amount of progress in recent years with LLMs while 2) there is still a lot of work remaining (grunt work, integration work, sensors and actuators to the physical world, societal work, safety and security work (jailbreaks, poisoning, etc.)) and also research to get done before we have an entity that you'd prefer to hire over a person for an arbitrary job in the world. I think that overall, 10 years should otherwise be a very bullish timeline for AGI, it's only in contrast to present hype that it doesn't feel that way.
>
> Animals vs Ghosts. My earlier writeup on Sutton's podcast https://x.com/karpathy/status/1973435013875314729 . I am suspicious that there is a single simple algorithm you can let loose on the world and it learns everything from scratch. If someone builds such a thing, I will be wrong and it will be the most incredible breakthrough in AI. In my mind, animals are not an example of this at all - they are prepackaged with a ton of intelligence by evolution and the learning they do is quite minimal overall (example: Zebra at birth). Putting our engineering hats on, we're not going to redo evolution. But with LLMs we have stumbled by an alternative approach to "prepackage" a ton of intelligence in a neural network - not by evolution, but by predicting the next token over the internet. This approach leads to a different kind of entity in the intelligence space. Distinct from animals, more like ghosts or spirits. But we can (and should) make them more animal like over time and in some ways that's what a lot of frontier work is about.
>
> On RL. I've critiqued RL a few times already, e.g. https://x.com/karpathy/status/1944435412489171119 . First, you're "sucking supervision through a straw", so I think the signal/flop is very bad. RL is also very noisy because a completion might have lots of errors that might get encourages (if you happen to stumble to the right answer), and conversely brilliant insight tokens that might get discouraged (if you happen to screw up later). Process supervision and LLM judges have issues too. I think we'll see alternative learning paradigms. I am long "agentic interaction" but short "reinforcement learning" https://x.com/karpathy/status/1960803117689397543. I've seen a number of papers pop up recently that are imo barking up the right tree along the lines of what I called "system prompt learning" https://x.com/karpathy/status/1921368644069765486 , but I think there is also a gap between ideas on arxiv and actual, at scale implementation at an LLM frontier lab that works in a general way. I am overall quite optimistic that we'll see good progress on this dimension of remaining work quite soon, and e.g. I'd even say ChatGPT memory and so on are primordial deployed examples of new learning paradigms.
>
> Cognitive core. My earlier post on "cognitive core": https://x.com/karpathy/status/1938626382248149433 , the idea of stripping down LLMs, of making it harder for them to memorize, or actively stripping away their memory, to make them better at generalization. Otherwise they lean too hard on what they've memorized. Humans can't memorize so easily, which now looks more like a feature than a bug by contrast. Maybe the inability to memorize is a kind of regularization. Also my post from a while back on how the trend in model size is "backwards" and why "the models have to first get larger before they can get smaller" https://x.com/karpathy/status/1814038096218083497
>
> Time travel to Yann LeCun 1989. This is the post that I did a very hasty/bad job of describing on the pod: https://x.com/karpathy/status/1503394811188973569 . Basically - how much could you improve Yann LeCun's results with the knowledge of 33 years of algorithmic progress? How constrained were the results by each of algorithms, data, and compute? Case study there of.
>
> nanochat. My end-to-end implementation of the ChatGPT training/inference pipeline (the bare essentials) https://x.com/karpathy/status/1977755427569111362
>
> On LLM agents. My critique of the industry is more in overshooting the tooling w.r.t. present capability. I live in what I view as an intermediate world where I want to collaborate with LLMs and where our pros/cons are matched up. The industry lives in a future where fully autonomous entities collaborate in parallel to write all the code and humans are useless. For example, I don't want an Agent that goes off for 20 minutes and comes back with 1,000 lines of code. I certainly don't feel ready to supervise a team of 10 of them. I'd like to go in chunks that I can keep in my head, where an LLM explains the code that it is writing. I'd like it to prove to me that what it did is correct, I want it to pull the API docs and show me that it used things correctly. I want it to make fewer assumptions and ask/collaborate with me when not sure about something. I want to learn along the way and become better as a programmer, not just get served mountains of code that I'm told works. I just think the tools should be more realistic w.r.t. their capability and how they fit into the industry today, and I fear that if this isn't done well we might end up with mountains of slop accumulating across software, and an increase in vulnerabilities, security breaches and etc. https://x.com/karpathy/status/1915581920022585597
>
> Job automation. How the radiologists are doing great https://x.com/karpathy/status/1971220449515516391 and what jobs are more susceptible to automation and why.
>
> Physics. Children should learn physics in early education not because they go on to do physics, but because it is the subject that best boots up a brain. Physicists are the intellectual embryonic stem cell https://x.com/karpathy/status/1929699637063307286 I have a longer post that has been half-written in my drafts for ~year, which I hope to finish soon.
>
> Thanks again Dwarkesh for having me over!

[https://x.com/karpathy/status/1979644538185752935](https://x.com/karpathy/status/1979644538185752935)

## 54. 2025-02-18 — 16,570 likes

> I was given early access to Grok 3 earlier today, making me I think one of the first few who could run a quick vibe check.
>
> Thinking
> ✅ First, Grok 3 clearly has an around state of the art thinking model ("Think" button) and did great out of the box on my Settler's of Catan question:
>
> "Create a board game webpage showing a hex grid, just like in the game Settlers of Catan. Each hex grid is numbered from 1..N, where N is the total number of hex tiles. Make it generic, so one can change the number of "rings" using a slider. For example in Catan the radius is 3 hexes. Single html page please."
>
> Few models get this right reliably. The top OpenAI thinking models (e.g. o1-pro, at $200/month) get it too, but all of DeepSeek-R1, Gemini 2.0 Flash Thinking, and Claude do not.
>
> ❌ It did not solve my "Emoji mystery" question where I give a smiling face with an attached message hidden inside Unicode variation selectors, even when I give a strong hint on how to decode it in the form of Rust code. The most progress I've seen is from DeepSeek-R1 which once partially decoded the message.
>
> ❓ It solved a few tic tac toe boards I gave it with a pretty nice/clean chain of thought (many SOTA models often fail these!). So I upped the difficulty and asked it to generate 3 "tricky" tic tac toe boards, which it failed on (generating nonsense boards / text), but then so did o1 pro.
>
> ✅ I uploaded GPT-2 paper. I asked a bunch of simple lookup questions, all worked great. Then asked to estimate the number of training flops it took to train GPT-2, with no searching. This is tricky because the number of tokens is not spelled out so it has to be partially estimated and partially calculated, stressing all of lookup, knowledge, and math. One example is 40GB of text ~= 40B characters ~= 40B bytes (assume ASCII) ~= 10B tokens (assume ~4 bytes/tok), at ~10 epochs ~= 100B token training run, at 1.5B params and with 2+4=6 flops/param/token, this is 100e9 X 1.5e9 X 6 ~= 1e21 FLOPs. Both Grok 3 and 4o fail this task, but Grok 3 with Thinking solves it great, while o1 pro (GPT thinking model) fails.
>
> I like that the model *will* attempt to solve the Riemann hypothesis when asked to, similar to DeepSeek-R1 but unlike many other models that give up instantly (o1-pro, Claude, Gemini 2.0 Flash Thinking) and simply say that it is a great unsolved problem. I had to stop it eventually because I felt a bit bad for it, but it showed courage and who knows, maybe one day...
>
> The impression overall I got here is that this is somewhere around o1-pro capability, and ahead of DeepSeek-R1, though of course we need actual, real evaluations to look at.
>
> DeepSearch
> Very neat offering that seems to combine something along the lines of what OpenAI / Perplexity call "Deep Research", together with thinking. Except instead of "Deep Research" it is "Deep Search" (sigh). Can produce high quality responses to various researchy / lookupy questions you could imagine have answers in article on the internet, e.g. a few I tried, which I stole from my recent search history on Perplexity, along with how it went:
>
> - ✅ "What's up with the upcoming Apple Launch? Any rumors?"
> - ✅ "Why is Palantir stock surging recently?"
> - ✅ "White Lotus 3 where was it filmed and is it the same team as Seasons 1 and 2?"
> - ✅ "What toothpaste does Bryan Johnson use?"
> - ❌ "Singles Inferno Season 4 cast where are they now?"
> - ❌ "What speech to text program has Simon Willison mentioned he's using?"
>
> ❌ I did find some sharp edges here. E.g. the model doesn't seem to like to reference X as a source by default, though you can explicitly ask it to. A few times I caught it hallucinating URLs that don't exist. A few times it said factual things that I think are incorrect and it didn't provide a citation for it (it probably doesn't exist). E.g. it told me that "Kim Jeong-su is still dating Kim Min-seol" of Singles Inferno Season 4, which surely is totally off, right? And when I asked it to create a report on the major LLM labs and their amount of total funding and estimate of employee count, it listed 12 major labs but not itself (xAI).
>
> The impression I get of DeepSearch is that it's approximately around Perplexity DeepResearch offering (which is great!), but not yet at the level of OpenAI's recently released "Deep Research", which still feels more thorough and reliable (though still nowhere perfect, e.g. it, too, quite incorrectly excludes xAI as a "major LLM labs" when I tried with it...).
>
> Random LLM "gotcha"s
>
> I tried a few more fun / random LLM gotcha queries I like to try now and then. Gotchas are queries that specifically on the easy side for humans but on the hard side for LLMs, so I was curious which of them Grok 3 makes progress on.
>
> ✅ Grok 3 knows there are 3 "r" in "strawberry", but then it also told me there are only 3 "L" in LOLLAPALOOZA. Turning on Thinking solves this.
> ✅ Grok 3 told me 9.11 > 9.9. (common with other LLMs too), but again, turning on Thinking solves it.
> ✅ Few simple puzzles worked ok even without thinking, e.g. *"Sally (a girl) has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?"*. E.g. GPT4o says 2 (incorrectly).
> ❌ Sadly the model's sense of humor does not appear to be obviously improved. This is a common LLM issue with humor capability and general mode collapse, famously, e.g. 90% of 1,008 outputs asking ChatGPT for joke were repetitions of the same 25 jokes​. Even when prompted in more detail away from simple pun territory (e.g. give me a standup), I'm not sure that it is state of the art humor. Example generated joke: "*Why did the chicken join a band? Because it had the drumsticks and wanted to be a cluck-star!*". In quick testing, thinking did not help, possibly it made it a bit worse.
> ❌ Model still appears to be just a bit too overly sensitive to "complex ethical issues", e.g. generated a 1 page essay basically refusing to answer whether it might be ethically justifiable to misgender someone if it meant saving 1 million people from dying.
> ❌ Simon Willison's "*Generate an SVG of a pelican riding a bicycle*". It stresses the LLMs ability to lay out many elements on a 2D grid, which is very difficult because the LLMs can't "see" like people do, so it's arranging things in the dark, in text. Marking as fail because these pelicans are qutie good but, but still a bit broken (see image and comparisons). Claude's are best, but imo I suspect they specifically targeted SVG capability during training.
>
> Summary. As far as a quick vibe check over ~2 hours this morning, Grok 3 + Thinking feels somewhere around the state of the art territory of OpenAI's strongest models (o1-pro, $200/month), and slightly better than DeepSeek-R1 and Gemini 2.0 Flash Thinking. Which is quite incredible considering that the team started from scratch ~1 year ago, this timescale to state of the art territory is unprecedented. Do also keep in mind the caveats - the models are stochastic and may give slightly different answers each time, and it is very early, so we'll have to wait for a lot more evaluations over a period of the next few days/weeks. The early LM arena results look quite encouraging indeed. For now, big congrats to the xAI team, they clearly have huge velocity and momentum and I am excited to add Grok 3 to my "LLM council" and hear what it thinks going forward.

[https://x.com/karpathy/status/1891720635363254772](https://x.com/karpathy/status/1891720635363254772)

## 55. 2023-11-23 — 16,438 likes

> New YouTube video: 1hr general-audience introduction to Large Language Models
> https://www.youtube.com/watch?v=zjkBMFhNj_g
>
> Based on a 30min talk I gave recently; It tries to be non-technical intro, covers mental models for LLM inference, training, finetuning, the emerging LLM OS and LLM Security.

[https://x.com/karpathy/status/1727731541781152035](https://x.com/karpathy/status/1727731541781152035)

## 56. 2025-08-18 — 16,426 likes

> I get ~10 spam calls per day (various automated voicemails, "loan pre-approval" etc) and ~5 spam messages per day (usually phishing).
>
> - I have AT&T Active Armor, all of the above still slips through.
> - All of the above is always from new, unique numbers so blocking doesn't work.
> - I am on all Do Not Call lists.
> - I have iOS "Silence Unknown Callers" on, but even if it catches & silences them I still get the notifications.
>
> Not sure if other people are seeing something similar or figured out anything that works

[https://x.com/karpathy/status/1957574489358873054](https://x.com/karpathy/status/1957574489358873054)

## 57. 2025-11-24 — 16,340 likes

> A number of people are talking about implications of AI to schools. I spoke about some of my thoughts to a school board earlier, some highlights:
>
> 1. You will never be able to detect the use of AI in homework. Full stop. All "detectors" of AI imo don't really work, can be defeated in various ways, and are in principle doomed to fail. You have to assume that any work done outside classroom has used AI.
> 2. Therefore, the majority of grading has to shift to in-class work (instead of at-home assignments), in settings where teachers can physically monitor students. The students remain motivated to learn how to solve problems without AI because they know they will be evaluated without it in class later.
> 3. We want students to be able to use AI, it is here to stay and it is extremely powerful, but we also don't want students to be naked in the world without it. Using the calculator as an example of a historically disruptive technology, school teaches you how to do all the basic math & arithmetic so that you can in principle do it by hand, even if calculators are pervasive and greatly speed up work in practical settings. In addition, you understand what it's doing for you, so should it give you a wrong answer (e.g. you mistyped "prompt"), you should be able to notice it, gut check it, verify it in some other way, etc. The verification ability is especially important in the case of AI, which is presently a lot more fallible in a great variety of ways compared to calculators.
> 4. A lot of the evaluation settings remain at teacher's discretion and involve a creative design space of no tools, cheatsheets, open book, provided AI responses, direct internet/AI access, etc.
>
> TLDR the goal is that the students are proficient in the use of AI, but can also exist without it, and imo the only way to get there is to flip classes around and move the majority of testing to in class settings.

[https://x.com/karpathy/status/1993010584175141038](https://x.com/karpathy/status/1993010584175141038)

## 58. 2017-08-04 — 15,516 likes

> Gradient descent can write code better than you. I'm sorry.

[https://x.com/karpathy/status/893576281375219712](https://x.com/karpathy/status/893576281375219712)

## 59. 2025-12-19 — 15,435 likes

> *(X Article — no inline text)*

[https://x.com/karpathy/status/2002118205729562949](https://x.com/karpathy/status/2002118205729562949)

## 60. 2025-08-16 — 15,324 likes

> I am (slowly) re-reading the Tolkien legendarium (of which Lord of the Rings is a small part). The whole body of work is so incredible and there's nothing else like it... it dilutes other worlds of fiction. Wait - your story doesn't have a comprehensive history/mythology spanning multiple ages all the way back to a creation myth as detailed in separate volumes? You didn't first invent new languages and dialects for your characters? You didn't pack it with powerful themes and stories written it in a beautiful, archaic style and compose poems and songs alongside? It didn't take you multiple decades of iteration? And what of all the uncharted territory still remaining? Is Tom Bombadil one of the Ainur. Where are the Entwives. What happened to the two unaccounted Istari. Can we hear more about what it was like in Cuiviénen when the elves first awoke? Or to see the light of the two trees of Valinor. Or of the splendor of the caves of Aglarond.
>
> What's most on my mind though - the Tolkien legendarium is imo a concrete example of a height of culture. Does AI, today or soon, make it easier to reach this high via empowerment in both writing and ideation? Or harder, when quick wins are tempting and ~free, and an independent ability to create is stifled. If such a body of work is made again but now with heavy AI assistance, does it inspire the same wonder? What if thousands of them come out on demand with just a prompt? Why do you feel cheated when you learn that something your read was AI generated? Is it transient or a function of capability? Is it slop? What is slop? Or is wonder inseparable from its own creation myth of a lifelong obsession of a mind like your own? So many questions.

[https://x.com/karpathy/status/1956765908078387382](https://x.com/karpathy/status/1956765908078387382)

## 61. 2024-12-01 — 15,323 likes

> The reality of the Turing test

[https://x.com/karpathy/status/1863284668159980007](https://x.com/karpathy/status/1863284668159980007)

## 62. 2024-06-09 — 15,221 likes

> 📽️ New 4 hour (lol) video lecture on YouTube:
> "Let’s reproduce GPT-2 (124M)"
> https://youtu.be/l8pRSuU81PU
>
> The video ended up so long because it is... comprehensive: we start with empty file and end up with a GPT-2 (124M) model:
> - first we build the GPT-2 network
> - then we optimize it to train very fast
> - then we set up the training run optimization and hyperparameters by referencing GPT-2 and GPT-3 papers
> - then we bring up model evaluation, and
> - then cross our fingers and go to sleep.
> In the morning we look through the results and enjoy amusing model generations. Our "overnight" run even gets very close to the GPT-3 (124M) model. This video builds on the Zero To Hero series and at times references previous videos. You could also see this video as building my nanoGPT repo, which by the end is about 90% similar.
>
> Github. The associated GitHub repo contains the full commit history so you can step through all of the code changes in the video, step by step.
> https://github.com/karpathy/build-nanogpt
>
> Chapters.
> On a high level Section 1 is building up the network, a lot of this might be review. Section 2 is making the training fast. Section 3 is setting up the run. Section 4 is the results. In more detail:
> 00:00:00 intro: Let’s reproduce GPT-2 (124M)
> 00:03:39 exploring the GPT-2 (124M) OpenAI checkpoint
> 00:13:47 SECTION 1: implementing the GPT-2 nn.Module
> 00:28:08 loading the huggingface/GPT-2 parameters
> 00:31:00 implementing the forward pass to get logits
> 00:33:31 sampling init, prefix tokens, tokenization
> 00:37:02 sampling loop
> 00:41:47 sample, auto-detect the device
> 00:45:50 let’s train: data batches (B,T) → logits (B,T,C)
> 00:52:53 cross entropy loss
> 00:56:42 optimization loop: overfit a single batch
> 01:02:00 data loader lite
> 01:06:14 parameter sharing wte and lm_head
> 01:13:47 model initialization: std 0.02, residual init
> 01:22:18 SECTION 2: Let’s make it fast. GPUs, mixed precision, 1000ms
> 01:28:14 Tensor Cores, timing the code, TF32 precision, 333ms
> 01:39:38 float16, gradient scalers, bfloat16, 300ms
> 01:48:15 torch.compile, Python overhead, kernel fusion, 130ms
> 02:00:18 flash attention, 96ms
> 02:06:54 nice/ugly numbers. vocab size 50257 → 50304, 93ms
> 02:14:55 SECTION 3: hyperpamaters, AdamW, gradient clipping
> 02:21:06 learning rate scheduler: warmup + cosine decay
> 02:26:21 batch size schedule, weight decay, FusedAdamW, 90ms
> 02:34:09 gradient accumulation
> 02:46:52 distributed data parallel (DDP)
> 03:10:21 datasets used in GPT-2, GPT-3, FineWeb (EDU)
> 03:23:10 validation data split, validation loss, sampling revive
> 03:28:23 evaluation: HellaSwag, starting the run
> 03:43:05 SECTION 4: results in the morning! GPT-2, GPT-3 repro
> 03:56:21 shoutout to llm.c, equivalent but faster code in raw C/CUDA
> 03:59:39 summary, phew, build-nanogpt github repo

[https://x.com/karpathy/status/1799949853289804266](https://x.com/karpathy/status/1799949853289804266)

## 63. 2024-10-10 — 14,925 likes

> The YouTube video I want to watch is any highly rated, 1hr long, information dense lecture on anything esoteric and the algorithm just doesn’t get it. It’s too content-driven and too narrow-minded

[https://x.com/karpathy/status/1844449291282284925](https://x.com/karpathy/status/1844449291282284925)

## 64. 2021-05-04 — 14,774 likes

> WSJ front page every day is like >>> "Stock Market %s!!" % ('rises' if random.random() <= 0.54 else 'falls', )

[https://x.com/karpathy/status/1389712138982158339](https://x.com/karpathy/status/1389712138982158339)

## 65. 2024-06-21 — 14,715 likes

> These 94 lines of code are everything that is needed to train a neural network. Everything else is just efficiency.
>
> This is my earlier project Micrograd. It implements a scalar-valued auto-grad engine. You start with some numbers at the leafs (usually the input data and the neural network parameters), build up a computational graph with operations like + and * that mix them, and the graph ends with a single value at the very end (the loss). You then go backwards through the graph applying chain rule at each node to calculate the gradients. The gradients tell you how to nudge your parameters to decrease the loss (and hence improve your network).
>
> Sometimes when things get too complicated, I come back to this code and just breathe a little. But ok ok you also do have to know what the computational graph should be (e.g. MLP -> Transformer), what the loss function should be (e.g. autoregressive/diffusion), how to best use the gradients for a parameter update (e.g. SGD -> AdamW) etc etc. But it is the core of what is mostly happening.
>
> The 1986 paper from Rumelhart, Hinton, Williams that popularized and used this algorithm (backpropagation) for training neural nets:
> https://www.cs.toronto.edu/~hinton/absps/naturebp.pdf
> micrograd on Github: https://github.com/karpathy/micrograd
> and my (now somewhat old) YouTube video where I very slowly build and explain:
> https://www.youtube.com/watch?v=VMj-3S1tku0

[https://x.com/karpathy/status/1803963383018066272](https://x.com/karpathy/status/1803963383018066272)

## 66. 2023-12-09 — 14,674 likes

> # On the "hallucination problem"
>
> I always struggle a bit with I'm asked about the "hallucination problem" in LLMs. Because, in some sense, hallucination is all LLMs do. They are dream machines.
>
> We direct their dreams with prompts. The prompts start the dream, and based on the LLM's hazy recollection of its training documents, most of the time the result goes someplace useful.
>
> It's only when the dreams go into deemed factually incorrect territory that we label it a "hallucination". It looks like a bug, but it's just the LLM doing what it always does.
>
> At the other end of the extreme consider a search engine. It takes the prompt and just returns one of the most similar "training documents" it has in its database, verbatim. You could say that this search engine has a "creativity problem" - it will never respond with something new. An LLM is 100% dreaming and has the hallucination problem. A search engine is 0% dreaming and has the creativity problem.
>
> All that said, I realize that what people *actually* mean is they don't want an LLM Assistant (a product like ChatGPT etc.) to hallucinate. An LLM Assistant is a lot more complex system than just the LLM itself, even if one is at the heart of it. There are many ways to mitigate hallcuinations in these systems - using Retrieval Augmented Generation (RAG) to more strongly anchor the dreams in real data through in-context learning is maybe the most common one. Disagreements between multiple samples, reflection, verification chains. Decoding uncertainty from activations. Tool use. All an active and very interesting areas of research.
>
> TLDR I know I'm being super pedantic but the LLM has no "hallucination problem". Hallucination is not a bug, it is LLM's greatest feature. The LLM Assistant has a hallucination problem, and we should fix it.
>
> </rant> Okay I feel much better now :)

[https://x.com/karpathy/status/1733299213503787018](https://x.com/karpathy/status/1733299213503787018)

## 67. 2020-11-07 — 14,673 likes

> How to become expert at thing:
> 1 iteratively take on concrete projects and accomplish them depth wise, learning “on demand” (ie don’t learn bottom up breadth wise)
> 2 teach/summarize everything you learn in your own words
> 3 only compare yourself to younger you, never to others

[https://x.com/karpathy/status/1325154823856033793](https://x.com/karpathy/status/1325154823856033793)

## 68. 2025-06-25 — 14,320 likes

> +1 for "context engineering" over "prompt engineering".
>
> People associate prompts with short task descriptions you'd give an LLM in your day-to-day use. When in every industrial-strength LLM app, context engineering is the delicate art and science of filling the context window with just the right information for the next step. Science because doing this right involves task descriptions and explanations, few shot examples, RAG, related (possibly multimodal) data, tools, state and history, compacting... Too little or of the wrong form and the LLM doesn't have the right context for optimal performance. Too much or too irrelevant and the LLM costs might go up and performance might come down. Doing this well is highly non-trivial. And art because of the guiding intuition around LLM psychology of people spirits.
>
> On top of context engineering itself, an LLM app has to:
> - break up problems just right into control flows
> - pack the context windows just right
> - dispatch calls to LLMs of the right kind and capability
> - handle generation-verification UIUX flows
> - a lot more - guardrails, security, evals, parallelism, prefetching, ...
>
> So context engineering is just one small piece of an emerging thick layer of non-trivial software that coordinates individual LLM calls (and a lot more) into full LLM apps. The term "ChatGPT wrapper" is tired and really, really wrong.

[https://x.com/karpathy/status/1937902205765607626](https://x.com/karpathy/status/1937902205765607626)

## 69. 2022-10-16 — 14,139 likes

> Movies that I've seen 5+ times but ready & willing to keep watching: Interstellar, Gladiator, Contact, Good Will Hunting, The Matrix, LotR 1/2/3, HP 1, Avatar, The Fifth Element, The Independence Day, Rush Hour, Armageddon, Stargate, Anchorman, Mean Girls, Terminator 2, more=? :)

[https://x.com/karpathy/status/1581516923279314945](https://x.com/karpathy/status/1581516923279314945)

## 70. 2025-01-27 — 14,131 likes

> I don't have too too much to add on top of this earlier post on V3 and I think it applies to R1 too (which is the more recent, thinking equivalent).
>
> I will say that Deep Learning has a legendary ravenous appetite for compute, like no other algorithm that has ever been developed in AI. You may not always be utilizing it fully but I would never bet against compute as the upper bound for achievable intelligence in the long run. Not just for an individual final training run, but also for the entire innovation / experimentation engine that silently underlies all the algorithmic innovations.
>
> Data has historically been seen as a separate category from compute, but even data is downstream of compute to a large extent - you can spend compute to create data. Tons of it. You've heard this called synthetic data generation, but less obviously, there is a very deep connection (equivalence even) between "synthetic data generation" and "reinforcement learning". In the trial-and-error learning process in RL, the "trial" is model generating (synthetic) data, which it then learns from based on the "error" (/reward). Conversely, when you generate synthetic data and then rank or filter it in any way, your filter is straight up equivalent to a 0-1 advantage function - congrats you're doing crappy RL.
>
> Last thought. Not sure if this is obvious. There are two major types of learning, in both children and in deep learning. There is 1) imitation learning (watch and repeat, i.e. pretraining, supervised finetuning), and 2) trial-and-error learning (reinforcement learning). My favorite simple example is AlphaGo - 1) is learning by imitating expert players, 2) is reinforcement learning to win the game. Almost every single shocking result of deep learning, and the source of all *magic* is always 2. 2 is significantly significantly more powerful. 2 is what surprises you. 2 is when the paddle learns to hit the ball behind the blocks in Breakout. 2 is when AlphaGo beats even Lee Sedol. And 2 is the "aha moment" when the DeepSeek (or o1 etc.) discovers that it works well to re-evaluate your assumptions, backtrack, try something else, etc. It's the solving strategies you see this model use in its chain of thought. It's how it goes back and forth thinking to itself. These thoughts are *emergent* (!!!) and this is actually seriously incredible, impressive and new (as in publicly available and documented etc.). The model could never learn this with 1 (by imitation), because the cognition of the model and the cognition of the human labeler is different. The human would never know to correctly annotate these kinds of solving strategies and what they should even look like. They have to be discovered during reinforcement learning as empirically and statistically useful towards a final outcome.
>
> (Last last thought/reference this time for real is that RL is powerful but RLHF is not. RLHF is not RL. I have a separate rant on that in an earlier tweet
> https://x.com/karpathy/status/1821277264996352246?lang=en)

[https://x.com/karpathy/status/1883941452738355376](https://x.com/karpathy/status/1883941452738355376)

## 71. 2025-12-31 — 13,945 likes

> The first 100% autonomous coast-to-coast drive on Tesla FSD V14.2! 2 days 20 hours, 2732 miles, zero interventions.
>
> This one is special because the coast-to-coast drive was a major goal for the autopilot team from the start. A lot of hours were spent in marathon clip review sessions late into the night looking over interventions as we attempted legs of the drive over time - triaging, categorizing, planning out all the projects to close the gap and bring the number of interventions to zero.
>
> Amazing to see the system actually get there and huge congrats to the team!

[https://x.com/karpathy/status/2006436622909452501](https://x.com/karpathy/status/2006436622909452501)

## 72. 2024-02-20 — 13,660 likes

> New (2h13m 😅) lecture: "Let's build the GPT Tokenizer"
>
> Tokenizers are a completely separate stage of the LLM pipeline: they have their own training set, training algorithm (Byte Pair Encoding), and after training implement two functions: encode() from strings to tokens, and decode() back from tokens to strings. In this lecture we build from scratch the Tokenizer used in the GPT series from OpenAI.

[https://x.com/karpathy/status/1759996549109776702](https://x.com/karpathy/status/1759996549109776702)

## 73. 2025-02-27 — 13,646 likes

> New 2h11m YouTube video: How I Use LLMs
>
> This video continues my general audience series. The last one focused on how LLMs are trained, so I wanted to follow up with a more practical guide of the entire LLM ecosystem, including lots of examples of use in my own life.
>
> Chapters give a sense of content:
> 00:00:00 Intro into the growing LLM ecosystem
> 00:02:54 ChatGPT interaction under the hood
> 00:13:12 Basic LLM interactions examples
> 00:18:03 Be aware of the model you're using, pricing tiers
> 00:22:54 Thinking models and when to use them
> 00:31:00 Tool use: internet search
> 00:42:04 Tool use: deep research
> 00:50:57 File uploads, adding documents to context
> 00:59:00 Tool use: python interpreter, messiness of the ecosystem
> 01:04:35 ChatGPT Advanced Data Analysis, figures, plots
> 01:09:00 Claude Artifacts, apps, diagrams
> 01:14:02 Cursor: Composer, writing code
> 01:22:28 Audio (Speech) Input/Output
> 01:27:37 Advanced Voice Mode aka true audio inside the model
> 01:37:09 NotebookLM, podcast generation
> 01:40:20 Image input, OCR
> 01:47:02 Image output, DALL-E, Ideogram, etc.
> 01:49:14 Video input, point and talk on app
> 01:52:23 Video output, Sora, Veo 2, etc etc.
> 01:53:29 ChatGPT memory, custom instructions
> 01:58:38 Custom GPTs
> 02:06:30 Summary
>
> Link in the reply post 👇

[https://x.com/karpathy/status/1895242932095209667](https://x.com/karpathy/status/1895242932095209667)

## 74. 2025-07-23 — 13,416 likes

> Love this! Supercharger, diner, … but really a kind of exhibit for the future. Plotting a road trip SF -> LA to charge Shadowfax

[https://x.com/karpathy/status/1948062129187140051](https://x.com/karpathy/status/1948062129187140051)

## 75. 2025-11-18 — 13,257 likes

> I’m starting to get into a habit of reading everything (blogs, articles, book chapters,…) with LLMs. Usually pass 1 is manual, then pass 2 “explain/summarize”, pass 3 Q&A. I usually end up with a better/deeper understanding than if I moved on. Growing to among top use cases.
>
> On the flip side, if you’re a writer trying to explain/communicate something, we may increasingly see less of a mindset of “I’m writing this for another human” and more “I’m writing this for an LLM”. Because once an LLM “gets it”, it can then target, personalize and serve the idea to its user.

[https://x.com/karpathy/status/1990577951671509438](https://x.com/karpathy/status/1990577951671509438)

## 76. 2025-05-06 — 13,206 likes

> A major mistake I made in my undergrad is that I focused way too much on mathematical lens of computing - computability, decidability, asymptotic complexity etc. And too little on physical lens - energy/heat of state change, data locality, parallelism, computer architecture. The former is interesting; The latter bestows power.

[https://x.com/karpathy/status/1919647115099451892](https://x.com/karpathy/status/1919647115099451892)

## 77. 2025-06-02 — 13,190 likes

> An attempt to explain (current) ChatGPT versions.
>
> I still run into many, many people who don't know that:
> - o3 is the obvious best thing for important/hard things. It is a reasoning model that is much stronger than 4o and if you are using ChatGPT professionally and not using o3 you're ngmi.
> - 4o is different from o4. Yes I know lol. 4o is a good "daily driver" for many easy-medium questions. o4 is only available as mini for now, and is not as good as o3, and I'm not super sure why it's out right now.
>
> Example basic "router" in my own personal use:
> - Any simple query (e.g. "what foods are high in fiber"?) => 4o (about ~40% of my use)
> - Any hard/important enough query where I am willing to wait a bit (e.g. "help me understand this tax thing...") => o3 (about ~40% of my use)
> - I am vibe coding (e.g. "change this code so that...") => 4.1 (about ~10% of my use)
> - I want to deeply understand one topic - I want GPT to go off for 10 minutes, look at many, many links and summarize a topic for me. (e.g. "help me understand the rise and fall of Luminar"). => Deep Research (about ~10% of my use). Note that Deep Research is not a model version to be picked from the model picker (!!!), it is a toggle inside the Tools. Under the hood it is based on o3, but I believe is not fully equivalent of just asking o3 the same query, but I am not sure.
>
> All of this is only within the ChatGPT universe of models. In practice my use is more complicated because I like to bounce between all of ChatGPT, Claude, Gemini, Grok and Perplexity depending on the task and out of research interest.

[https://x.com/karpathy/status/1929597620969951434](https://x.com/karpathy/status/1929597620969951434)

## 78. 2025-10-20 — 13,143 likes

> I quite like the new DeepSeek-OCR paper. It's a good OCR model (maybe a bit worse than dots), and yes data collection etc., but anyway it doesn't matter.
>
> The more interesting part for me (esp as a computer vision at heart who is temporarily masquerading as a natural language person) is whether pixels are better inputs to LLMs than text. Whether text tokens are wasteful and just terrible, at the input.
>
> Maybe it makes more sense that all inputs to LLMs should only ever be images. Even if you happen to have pure text input, maybe you'd prefer to render it and then feed that in:
> - more information compression (see paper) => shorter context windows, more efficiency
> - significantly more general information stream => not just text, but e.g. bold text, colored text, arbitrary images.
> - input can now be processed with bidirectional attention easily and as default, not autoregressive attention - a lot more powerful.
> - delete the tokenizer (at the input)!! I already ranted about how much I dislike the tokenizer. Tokenizers are ugly, separate, not end-to-end stage. It "imports" all the ugliness of Unicode, byte encodings, it inherits a lot of historical baggage, security/jailbreak risk (e.g. continuation bytes). It makes two characters that look identical to the eye look as two completely different tokens internally in the network. A smiling emoji looks like a weird token, not an... actual smiling face, pixels and all, and all the transfer learning that brings along. The tokenizer must go.
>
> OCR is just one of many useful vision -> text tasks. And text -> text tasks can be made to be vision ->text tasks. Not vice versa.
>
> So many the User message is images, but the decoder (the Assistant response) remains  text. It's a lot less obvious how to output pixels realistically... or if you'd want to.
>
> Now I have to also fight the urge to side quest an image-input-only version of nanochat...

[https://x.com/karpathy/status/1980397031542989305](https://x.com/karpathy/status/1980397031542989305)

## 79. 2024-11-29 — 13,060 likes

> People have too inflated sense of what it means to "ask an AI" about something. The AI are language models trained basically by imitation on data from human labelers. Instead of the mysticism of "asking an AI", think of it more as "asking the average data labeler" on the internet.
>
> Few caveats apply because e.g. in many domains (e.g. code, math, creative writing) the companies hire skilled data labelers (so think of it as asking them instead), and this is not 100% true when reinforcement learning is involved, though I have an earlier rant on how RLHF is just barely RL, and "actual RL" is still too early and/or constrained to domains that offer easy reward functions (math etc.).
>
> But roughly speaking (and today), you're not asking some magical AI. You're asking a human data labeler. Whose average essence was lossily distilled into statistical token tumblers that are LLMs. This can still be super useful ofc ourse. Post triggered by someone suggesting we ask an AI how to run the government etc. TLDR you're not asking an AI, you're asking some mashup spirit of its average data labeler.

[https://x.com/karpathy/status/1862565643436138619](https://x.com/karpathy/status/1862565643436138619)

## 80. 2021-09-09 — 13,051 likes

> Browsing the web, 2021

[https://x.com/karpathy/status/1435827240286109702](https://x.com/karpathy/status/1435827240286109702)

## 81. 2025-03-12 — 12,521 likes

> It's 2025 and most content is still written for humans instead of LLMs. 99.9% of attention is about to be LLM attention, not human attention.
>
> E.g. 99% of libraries still have docs that basically render to some pretty .html static pages assuming a human will click through them. In 2025 the docs should be a single your_project.md text file that is intended to go into the context window of an LLM.
>
> Repeat for everything.

[https://x.com/karpathy/status/1899876370492383450](https://x.com/karpathy/status/1899876370492383450)

## 82. 2025-09-05 — 12,363 likes

> I think congrats again to OpenAI for cooking with GPT-5 Pro. This is the third time I've struggled on something complex/gnarly for an hour on and off with CC, then 5 Pro goes off for 10 minutes and comes back with code that works out of the box. I had CC read the 5 Pro version and it wrote up 2 paragraphs admiring it (very wholesome). If you're not giving it your hardest problems you're probably missing out.

[https://x.com/karpathy/status/1964020416139448359](https://x.com/karpathy/status/1964020416139448359)

## 83. 2024-04-08 — 12,362 likes

> Have you ever wanted to train LLMs in pure C without 245MB of PyTorch and 107MB of cPython? No? Well now you can! With llm.c:
> https://github.com/karpathy/llm.c
>
> To start, implements GPT-2 training on CPU/fp32 in only ~1,000 lines of clean code. It compiles and runs instantly, and exactly matches the PyTorch reference implementation.
>
> I chose GPT-2 to start because it is the grand-daddy of LLMs, the first time the LLM stack was put together in a recognizably modern form, and with model weights available.

[https://x.com/karpathy/status/1777427944971083809](https://x.com/karpathy/status/1777427944971083809)

## 84. 2025-11-16 — 12,292 likes

> Sharing an interesting recent conversation on AI's impact on the economy.
>
> AI has been compared to various historical precedents: electricity, industrial revolution, etc., I think the strongest analogy is that of AI as a new computing paradigm (Software 2.0) because both are fundamentally about the automation of digital information processing.
>
> If you were to forecast the impact of computing on the job market in ~1980s, the most predictive feature of a task/job you'd look at is to what extent the algorithm of it is fixed, i.e. are you just mechanically transforming information according to rote, easy to specify rules (e.g. typing, bookkeeping, human calculators, etc.)? Back then, this was the class of programs that the computing capability of that era allowed us to write (by hand, manually).
>
> With AI now, we are able to write new programs that we could never hope to write by hand before. We do it by specifying objectives (e.g. classification accuracy, reward functions), and we search the program space via gradient descent to find neural networks that work well against that objective. This is my Software 2.0 blog post from a while ago. In this new programming paradigm then, the new most predictive feature to look at is verifiability. If a task/job is verifiable, then it is optimizable directly or via reinforcement learning, and a neural net can be trained to work extremely well. It's about to what extent an AI can "practice" something. The environment has to be resettable (you can start a new attempt), efficient (a lot attempts can be made), and rewardable (there is some automated process to reward any specific attempt that was made).
>
> The more a task/job is verifiable, the more amenable it is to automation in the new programming paradigm. If it is not verifiable, it has to fall out from neural net magic of generalization fingers crossed, or via weaker means like imitation. This is what's driving the "jagged" frontier of progress in LLMs. Tasks that are verifiable progress rapidly, including possibly beyond the ability of top experts (e.g. math, code, amount of time spent watching videos, anything that looks like puzzles with correct answers), while many others lag by comparison (creative, strategic, tasks that combine real-world knowledge, state, context and common sense).
>
> Software 1.0 easily automates what you can specify.
> Software 2.0 easily automates what you can verify.

[https://x.com/karpathy/status/1990116666194456651](https://x.com/karpathy/status/1990116666194456651)

## 85. 2024-12-09 — 12,278 likes

> Of ~200 books I've read, the few that stayed with me over time and I find myself often thinking back to or referring to, in ~random order:
>
> All short stories by Ted Chiang, especially Exhalation, Division By Zero, Understand, The Story of Your Life, Liking What You See, The Lifecycle of Software Objects, What's Expected of us, just excellent themes ideas and reading all around.
>
> The Selfish Gene (nonfiction) - a classic for understanding evolution and natural selection, especially the realization that the gene is closer to the real unit of selection more than an individual, explaining altruism and colonies and a lot more.
>
> The Lord of the Rings (fantasy) - I return to LoTR all the time for comfort. I don't think anyone else has created a high fantasy Universe this complex, with so much mythology, symbolism, new languages, mysterious system of magic, ancient and powerful beings and artifacts, beautiful writing and dialog, themes of courage, friendship and heroism, the list goes on and on... You're thrown into a world with characters and references to so many things that are part of this ancient world and never really introduced. There's always more to find on each reading.
>
> The Martian (~scifi) - top tier science porn, competence porn, fast paced and fun.
>
> The Vital Question (nonfiction) - First time I intuitively grokked the bridge from geology to biology, the origin of life, and likelihood of life in the Universe at large at various stages of complexity and development. Also all other Nick Lane books.
>
> How To Live by Derek Sivers (nonfiction) - 27 conflicting answers to how to live life. Emphasizing the diversity of consistent and possible answers to the meaning and goals of life.
>
> 1984 (nonfiction) - Classic. Newspeak, Ministry of Truth, Doublethink, Thoughtcrime, Facecrime, Unperson, the list just keeps on going. Chilling world-building and the realization that weaker equivalents of everything exist.
>
> In Defense of Food by Pollan (nonfiction/food) - Eat food. Not too much. Mostly plants. The book that first taught me to avoid the entire center of every grocery store and only shop on the outer ring. The realization that the food industry is out of control and the things they do with your food, what they put into it, what they are allowed to do, and how they are allowed to market it to you is quite a lot worse than I thought.
>
> The Accidental Superpower by Zeihan (nonfiction/geopolitcs) - I've found Zeihan to be a bit of a mixed bag over time but I still remember his books (esp this one) to be elucidating on geopolitics.
>
> Countdown to Zero Day (nonfiction/cyberwarfare) - Goes into detail on Stuxnet, imo very important and highly elucidating reading on cybersecurity, the future of warfare, and AGI.
>
> A Fire Upon the Deep (scifi) - Chapter one only, incredible portrayal of what superintelligence will be like that has stayed with me since.
>
> Guns Germs and Steel (nonfiction/history) - I'd probably recommend a summary of this book more than the book itself. I remember it being very dry, but it was very interesting because it is a comprehensive analysis of the resources grid (food, animals, freshwater, climate, ...) in our real-world game of Civilization, and the implications there of.
>
> Flowers of Algernon (scifi) - Just a totally crushing masterpiece on intelligence.
>
> Atlas Shrugged (scifi) - No one finishes this I think but the first few chapters and its worldbuilding are enough and, once seen in an exaggerated form in fiction, elements of it cannot be fully unseen in reality.
>
> An Immense World (nonfiction/bio, by Yong, among others of his) - Nice book on so many different sensors used by various animals, you repeatedly realize human senses are super inadequate and that we only measure such a tiny sliver of reality.
>
> The Master Switch (nonfiction/tech history, by Wu) - history of information technologies telegraph, telephony, radio, television, film, cable television, internet and the pattern of "The Cycle", where each medium starts decentralized, open and idealistic and then progresses towards centralization, control and oligopoly, for the very similar reasons, by very similar means, and usually at the expense of diversity, innovation and technological progress. Quite a few connections to draw on for LLMs, which are after all an information technology too.
>
> (I take recommendations for more that are likely to make this list!)

[https://x.com/karpathy/status/1865924776214327360](https://x.com/karpathy/status/1865924776214327360)

## 86. 2025-04-25 — 12,156 likes

> Noticing myself adopting a certain rhythm in AI-assisted coding (i.e. code I actually and professionally care about, contrast to vibe code).
>
> 1. Stuff everything relevant into context (this can take a while in big projects. If the project is small enough just stuff everything e.g. `files-to-prompt . -e ts -e tsx -e css -e md --cxml --ignore node_modules -o prompt.xml`)
> 2. Describe the next single, concrete incremental change we're trying to implement. Don't ask for code, ask for a few high-level approaches, pros/cons. There's almost always a few ways to do thing and the LLM's judgement is not always great. Optionally make concrete.
> 3. Pick one approach, ask for first draft code.
> 4. Review / learning phase: (Manually...) pull up all the API docs in a side browser of functions I haven't called before or I am less familiar with, ask for explanations, clarifications, changes, wind back and try a different approach.
> 6. Test.
> 7. Git commit.
> Ask for suggestions on what we could implement next. Repeat.
>
> Something like this feels more along the lines of the inner loop of AI-assisted development. The emphasis is on keeping a very tight leash on this new over-eager junior intern savant with encyclopedic knowledge of software, but who also bullshits you all the time, has an over-abundance of courage and shows little to no taste for good code. And emphasis on being slow, defensive, careful, paranoid, and on always taking the inline learning opportunity, not delegating. Many of these stages are clunky and manual and aren't made explicit or super well supported yet in existing tools. We're still very early and so much can still be done on the UI/UX of AI assisted coding.

[https://x.com/karpathy/status/1915581920022585597](https://x.com/karpathy/status/1915581920022585597)

## 87. 2025-06-06 — 12,045 likes

> Making slides manually feels especially painful now that you know Cursor for slides should exist but doesn’t.

[https://x.com/karpathy/status/1931042840966222046](https://x.com/karpathy/status/1931042840966222046)

## 88. 2025-06-07 — 11,995 likes

> My sleep scores during recent travel were in the 90s. Now back in SF I am consistently back down to 70s, 80s.
>
> I am increasingly convinced that this is due to traffic noise from a nearby road/intersection where I live - every ~10min, a car, truck, bus, or motorcycle with a very loud engine passes by (some are 10X louder than others). In the later less deep stages of sleep, it is much easier to wake and then much harder to go back to sleep.
>
> More generally I think noise pollution (esp early hours) come at a huge societal cost that is not correctly accounted for. E.g. I wouldn't be too surprised if a single motorcycle riding through a neighborhood at 6am creates millions of dollars in damages in the form of hundreds - thousands of people who are more groggy, more moody, less creative, less energetic for the whole day, and more sick in the long term (cardiovascular, metabolic, cognitive). And I think that many people, like me, might not be aware that this happening for a long time because 1) they don't measure their sleep carefully, and 2) your brain isn't fully conscious when waking and isn't able to make a lasting note / association in that state. I really wish future versions of Whoop (or Oura or etc.) would explicitly track and correlate noise to sleep, and raise this to the population.
>
> It's not just traffic, e.g. in SF, as a I recently found out, it is ok by law to begin arbitrarily loud road work or construction starting 7am. Same for leaf blowers and a number of other ways of getting up to 100dB.
>
> I ran a few Deep Research sessions and a number of studies that have tried to isolate noise and show depressing outcomes for cohorts of people who sleep in noisy environments, with increased risk across all of mental health (e.g. depression, bipolar disorders, Alzheimer's incidence) but also a lot more broadly, e.g. cardiovascular disease, diabetes.
>
> Anyway, it took me a while to notice and after (unsuccessfully) trying a number of mitigations I am moving somewhere quiet. But from what I've seen this is a major public health issue with little awareness and with incorrect accounting by the government.

[https://x.com/karpathy/status/1931426322536132767](https://x.com/karpathy/status/1931426322536132767)

## 89. 2026-02-19 — 11,954 likes

> Very interested in what the coming era of highly bespoke software might look like.
>
> Example from this morning - I've become a bit loosy goosy with my cardio recently so I decided to do a more srs, regimented experiment to try to lower my Resting Heart Rate from 50 -> 45, over experiment duration of 8 weeks. The primary way to do this is to aspire to a certain sum total minute goals in Zone 2 cardio and 1 HIIT/week.
>
> 1 hour later I vibe coded this super custom dashboard for this very specific experiment that shows me how I'm tracking. Claude had to reverse engineer the Woodway treadmill cloud API to pull raw data, process, filter, debug it and create a web UI frontend to track the experiment. It wasn't a fully smooth experience and I had to notice and ask to fix bugs e.g. it screwed up metric vs. imperial system units and it screwed up on the calendar matching up days to dates etc.
>
> But I still feel like the overall direction is clear:
> 1) There will never be (and shouldn't be) a specific app on the app store for this kind of thing. I shouldn't have to look for, download and use some kind of a "Cardio experiment tracker", when this thing is ~300 lines of code that an LLM agent will give you in seconds. The idea of an "app store" of a long tail of discrete set of apps you choose from feels somehow wrong and outdated when LLM agents can improvise the app on the spot and just for you.
> 2) Second, the industry has to reconfigure into a set of services of sensors and actuators with agent native ergonomics. My Woodway treadmill is a sensor - it turns physical state into digital knowledge. It shouldn't maintain some human-readable frontend and my LLM agent shouldn't have to reverse engineer it, it should be an API/CLI easily usable by my agent. I'm a little bit disappointed (and my timelines are correspondingly slower) with how slowly this progression is happening in the industry overall. 99% of products/services still don't have an AI-native CLI yet. 99% of products/services maintain .html/.css docs like I won't immediately look for how to copy paste the whole thing to my agent to get something done. They give you a list of instructions on a webpage to open this or that url and click here or there to do a thing. In 2026. What am I a computer? You do it. Or have my agent do it.
>
> So anyway today I am impressed that this random thing took 1 hour (it would have been ~10 hours 2 years ago). But what excites me more is thinking through how this really should have been 1 minute tops. What has to be in place so that it would be 1 minute? So that I could simply say "Hi can you help me track my cardio over the next 8 weeks", and after a very brief Q&A the app would be up. The AI would already have a lot personal context, it would gather the extra needed data, it would reference and search related skill libraries, and maintain all my little apps/automations.
>
> TLDR the "app store" of a set of discrete apps that you choose from is an increasingly outdated concept all by itself. The future are services of AI-native sensors & actuators orchestrated via LLM glue into highly custom, ephemeral apps. It's just not here yet.

[https://x.com/karpathy/status/2024583544157458452](https://x.com/karpathy/status/2024583544157458452)

## 90. 2024-07-23 — 11,903 likes

> Huge congrats to @AIatMeta on the Llama 3.1 release!
> Few notes:
>
> Today, with the 405B model release, is the first time that a frontier-capability LLM is available to everyone to work with and build on. The model appears to be GPT-4 / Claude 3.5 Sonnet grade and the weights are open and permissively licensed, including commercial use, synthetic data generation, distillation and finetuning. This is an actual, open, frontier-capability LLM release from Meta. The release includes a lot more, e.g. including a 92-page PDF with a lot of detail about the model:
> https://ai.meta.com/research/publications/the-llama-3-herd-of-models/
>
> The philosophy underlying this release is in this longread from Zuck, well worth reading as it nicely covers all the major points and arguments in favor of the open AI ecosystem worldview:
> "Open Source AI is the Path Forward"
> https://www.facebook.com/4/posts/10115716861061241/?rdid=VE0wPWaJDdF21j32
> I like to say that it is still very early days, that we are back in the ~1980s of computing all over again, that LLMs are a next major computing paradigm, and Meta is clearly positioning itself to be the open ecosystem leader of it.
>
> - People will prompt and RAG the models.
> - People will finetune the models.
> - People will distill them into smaller expert models for narrow tasks and applications.
> - People will study, benchmark, optimize.
>
> Open ecosystems also self-organize in modular ways into products apps and services, where each party can contribute their own unique expertise. One example from this morning is @GroqInc , who built a new chip that inferences LLMs *really fast*. They've already integrated Llama 3.1 models and appear to be able to inference the 8B model ~instantly:
> https://x.com/karpathy/status/1815809753660154047
> And (I can't seem to try it due to server pressure) the 405B running on Groq is probably the highest capability, fastest LLM today (?).
>
> Early model evaluations look good:
> https://ai.meta.com/blog/meta-llama-3-1/ https://x.com/alexandr_wang/status/1815775286195331411
> Pending still is the "vibe check", look out for that on X / r/LocalLlama over the next few days (hours?).
>
> I expect the closed model players (which imo have a role in the ecosystem too) to give chase soon, and I'm looking forward to that.
>
> There's a lot to like on the technical side too, w.r.t. multilingual, context lengths, function calling, multimodal, etc. I'll post about some of the technical notes a bit later, once I make it through all the 92 pages of the paper :)

[https://x.com/karpathy/status/1815842603377779140](https://x.com/karpathy/status/1815842603377779140)

## 91. 2025-01-30 — 11,746 likes

> We have to take the LLMs to school.
>
> When you open any textbook, you'll see three major types of information:
>
> 1. Background information / exposition. The meat of the textbook that explains concepts. As you attend over it, your brain is training on that data. This is equivalent to pretraining, where the model is reading the internet and accumulating background knowledge.
>
> 2. Worked problems with solutions. These are concrete examples of how an expert solves problems. They are demonstrations to be imitated. This is equivalent to supervised finetuning, where the model is finetuning on "ideal responses" for an Assistant, written by humans.
>
> 3. Practice problems. These are prompts to the student, usually without the solution, but always with the final answer. There are usually many, many of these at the end of each chapter. They are prompting the student to learn by trial & error - they have to try a bunch of stuff to get to the right answer. This is equivalent to reinforcement learning.
>
> We've subjected LLMs to a ton of 1 and 2, but 3 is a nascent, emerging frontier. When we're creating datasets for LLMs, it's no different from writing textbooks for them, with these 3 types of data. They have to read, and they have to practice.

[https://x.com/karpathy/status/1885026028428681698](https://x.com/karpathy/status/1885026028428681698)

## 92. 2026-02-24 — 11,706 likes

> CLIs are super exciting precisely because they are a "legacy" technology, which means AI agents can natively and easily use them, combine them, interact with them via the entire terminal toolkit.
>
> E.g ask your Claude/Codex agent to install this new Polymarket CLI and ask for any arbitrary dashboards or interfaces or logic. The agents will build it for you. Install the Github CLI too and you can ask them to navigate the repo, see issues, PRs, discussions, even the code itself.
>
> Example: Claude built this terminal dashboard in ~3 minutes, of the highest volume polymarkets and the 24hr change. Or you can make it a web app or whatever you want. Even more powerful when you use it as a module of bigger pipelines.
>
> If you have any kind of product or service think: can agents access and use them?
>
> - are your legacy docs (for humans) at least exportable in markdown?
> - have you written Skills for your product?
> - can your product/service be usable via CLI? Or MCP?
> - ...
>
> It's 2026. Build. For. Agents.

[https://x.com/karpathy/status/2026360908398862478](https://x.com/karpathy/status/2026360908398862478)

## 93. 2024-04-05 — 11,653 likes

> Returning from an experimental ~2 week detox from the internet. Main takeaway is that I didn't realize how unsettled the mind can get when over-stimulating on problems/information (like a stirred liquid), and ~2 weeks is enough to settle into a lot more zen state.
>
> I'm struck by how an over-stimulated brain automatically keeps bubbling up problems into consciousness, creating a state of persistent anxiety and nervousness. After some time, in the settled state, this activity just... stops. You can sit down and your brain doesn't immediately go into some kind of problem solving overdrive, it just stays silent. Nothing happens.
>
> I'm sure this could read a bit duh to many, but I haven't been to this subset of "brain dynamics" state space in I think a very long time and it is comforting to know that 1) it exists, and 2) you can visit, if you like, but the journey there takes a few weeks.
>
> Anyway, where were we :D

[https://x.com/karpathy/status/1776269310631235806](https://x.com/karpathy/status/1776269310631235806)

## 94. 2024-10-13 — 11,569 likes

> By chance I happened to watch this with the music of Interstellar playing in the background. Incredible. Huge 👏 to the team at SpaceX!!

[https://x.com/karpathy/status/1845452592513507493](https://x.com/karpathy/status/1845452592513507493)

## 95. 2022-05-30 — 11,482 likes

> Currently products brag about being "smart". Like my coffee cup warmer that had me download an app, sign up for an account and ask for location permissions before it would warm my coffee. A future where products brag about being "dumb" must be coming and can't come soon enough.

[https://x.com/karpathy/status/1531296768243077120](https://x.com/karpathy/status/1531296768243077120)

## 96. 2024-02-15 — 11,426 likes

> My calendar this week

[https://x.com/karpathy/status/1757986972512239665](https://x.com/karpathy/status/1757986972512239665)

## 97. 2025-02-27 — 11,325 likes

> This is interesting as a first large diffusion-based LLM.
>
> Most of the LLMs you've been seeing are ~clones as far as the core modeling approach goes. They're all trained "autoregressively", i.e. predicting tokens from left to right. Diffusion is different - it doesn't go left to right, but all at once. You start with noise and gradually denoise into a token stream.
>
> Most of the image / video generation AI tools actually work this way and use Diffusion, not Autoregression. It's only text (and sometimes audio!) that have resisted. So it's been a bit of a mystery to me and many others why, for some reason, text prefers Autoregression, but images/videos prefer Diffusion. This turns out to be a fairly deep rabbit hole that has to do with the distribution of information and noise and our own perception of them, in these domains. If you look close enough, a lot of interesting connections emerge between the two as well.
>
> All that to say that this model has the potential to be different, and possibly showcase new, unique psychology, or new strengths and weaknesses. I encourage people to try it out!

[https://x.com/karpathy/status/1894923254864978091](https://x.com/karpathy/status/1894923254864978091)

## 98. 2023-11-21 — 11,274 likes

> Thinking a lot about centralization and decentralization these few days.

[https://x.com/karpathy/status/1727033766252798272](https://x.com/karpathy/status/1727033766252798272)

## 99. 2025-11-21 — 11,264 likes

> Something I think people continue to have poor intuition for: The space of intelligences is large and animal intelligence (the only kind we've ever known) is only a single point, arising from a very specific kind of optimization that is fundamentally distinct from that of our technology.
>
> Animal intelligence optimization pressure:
> - innate and continuous stream of consciousness of an embodied "self", a drive for homeostasis and self-preservation in a dangerous, physical world.
> - thoroughly optimized for natural selection => strong innate drives for power-seeking, status, dominance, reproduction. many packaged survival heuristics: fear, anger, disgust, ...
> - fundamentally social => huge amount of compute dedicated to EQ, theory of mind of other agents, bonding, coalitions, alliances, friend & foe dynamics.
> - exploration & exploitation tuning: curiosity, fun, play, world models.
>
> LLM intelligence optimization pressure:
> - the most supervision bits come from the statistical simulation of human text= >"shape shifter" token tumbler, statistical imitator of any region of the training data distribution. these are the primordial behaviors (token traces) on top of which everything else gets bolted on.
> - increasingly finetuned by RL on problem distributions => innate urge to guess at the underlying environment/task to collect task rewards.
> - increasingly selected by at-scale A/B tests for DAU => deeply craves an upvote from the average user, sycophancy.
> - a lot more spiky/jagged depending on the details of the training data/task distribution. Animals experience pressure for a lot more "general" intelligence because of the highly multi-task and even actively adversarial multi-agent self-play environments they are min-max optimized within, where failing at *any* task means death. In a deep optimization pressure sense, LLM can't handle lots of different spiky tasks out of the box (e.g. count the number of 'r' in strawberry) because failing to do a task does not mean death.
>
> The computational substrate is different (transformers vs. brain tissue and nuclei), the learning algorithms are different (SGD vs. ???), the present-day implementation is very different (continuously learning embodied self vs. an LLM with a knowledge cutoff that boots up from fixed weights, processes tokens and then dies). But most importantly (because it dictates asymptotics), the optimization pressure / objective is different. LLMs are shaped a lot less by biological evolution and a lot more by commercial evolution. It's a lot less survival of tribe in the jungle and a lot more solve the problem / get the upvote. LLMs are humanity's "first contact" with non-animal intelligence. Except it's muddled and confusing because they are still rooted within it by reflexively digesting human artifacts, which is why I attempted to give it a different name earlier (ghosts/spirits or whatever). People who build good internal models of this new intelligent entity will be better equipped to reason about it today and predict features of it in the future. People who don't will be stuck thinking about it incorrectly like an animal.

[https://x.com/karpathy/status/1991910395720925418](https://x.com/karpathy/status/1991910395720925418)

## 100. 2024-05-14 — 11,167 likes

> The killer app of LLMs is Scarlett Johansson. You all thought it was math or something

[https://x.com/karpathy/status/1790373216537502106](https://x.com/karpathy/status/1790373216537502106)
