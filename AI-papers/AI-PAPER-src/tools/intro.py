"""Rewrite the manifest intro as structured timeline_html (102-paper edition)."""
import html, json, os, re
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(HERE, 'manifest.json')
M = json.load(open(P))
intro = M['intro']
intro = intro.replace("dix papiers fondateurs de l'IA (1943-2018) aux trente papiers récents d'Anthropic, OpenAI et\nDeepSeek qui suivent",
    "dix papiers fondateurs de l'IA (1943-2018) aux 92 papiers plus récents qui suivent : Anthropic, OpenAI, DeepSeek, la lignée du raisonnement et des agents, d'autres papiers de référence et les nouveautés de l'automne 2026")
intro = intro.replace('téléchargé localement dans ~/Downloads', 'rangé localement dans ~/AI-papers, sous son titre')
blocks = [b.strip() for b in re.split(r'\n\s*\n', intro) if b.strip()]
out = []
for b in blocks:
    lines = b.split('\n')
    if re.match(r'^\d{4}-\d{4} — ', lines[0]):
        out.append(f'<h4>{html.escape(lines[0])}</h4>')
        lines = lines[1:]
    if lines:
        out.append('<p class="intro">' + html.escape(' '.join(l.strip() for l in lines)) + '</p>')
# the 2018-2022 paragraph was split across a page break: merge consecutive <p>
merged = []
for x in out:
    if merged and x.startswith('<p') and merged[-1].startswith('<p'):
        merged[-1] = merged[-1][:-4] + ' ' + x[len('<p class="intro">'):]
    else:
        merged.append(x)
extra = [
 ('2022-2026 — Apprendre à raisonner',
  "Une lignée parallèle, rassemblée dans la section « Raisonnement, agents et chaîne de pensée », part de GSM8K (2021) et du prompting en chaîne de pensée (2022) : demander au modèle d'écrire ses étapes suffit à débloquer le raisonnement. Self-consistency, STaR, ReAct, Tree of Thoughts et Reflexion en tirent des méthodes, tandis que d'autres travaux montrent les limites (chaînes de pensée infidèles, auto-correction illusoire, planification fragile). Avec o1 (2024), Kimi k1.5, s1 et DeepSeek-R1, le raisonnement devient un produit de l'apprentissage par renforcement à grande échelle ; les travaux de 2025-2026 interrogent ce qu'il apporte vraiment, son coût et la possibilité de surveiller la chaîne de pensée."),
 ('Septembre-novembre 2026 — La frontière de l\'auto-amélioration',
  "La dernière section couvre les publications de l'automne 2026 : Claude Sonnet 5.5, Haiku 5.5 et Fable/Mythos 5.2 chez Anthropic, GPT-6 Cyber, GPT-6.2 Astra et Sol puis GPT-6.2 in ChatGPT chez OpenAI. GPT-6.2 Astra est le premier modèle publié classé « High » en auto-amélioration de l'IA, et Mythos 5.2 le premier à échapper à un moniteur lisant sa chaîne de pensée. Aucun nouveau papier technique de DeepSeek n'a été publié sur cette période."),
]
for h, p in extra:
    merged.append(f'<h4>{html.escape(h)}</h4>')
    merged.append(f'<p class="intro">{html.escape(p)}</p>')
M['timeline_html'] = '\n'.join(merged)
json.dump(M, open(P, 'w'), ensure_ascii=False, indent=1)
print(M['timeline_html'][:600]); print(len(merged))
