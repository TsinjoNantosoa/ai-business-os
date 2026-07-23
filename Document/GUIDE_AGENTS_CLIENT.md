# Guide client — Agents IA & Copilot AI BOS

> **Public :** administrateurs et utilisateurs métier  
> **Version produit :** Phase 2 (Lots C–I) · Juillet 2026  
> **Connexion démo :** `ceo@demo.aibos.io` / `demo1234`

---

## 1. Qu’est-ce que l’équipe d’agents ?

AI BOS met à disposition une **galerie d’agents spécialisés** (CEO, Sales, Finance, Marketing, HR, Analytics…).  
Chaque agent a une **persona** et s’appuie sur :

- le **Copilot** (chat temps réel SSE)
- la **base documentaire RAG** (`Document/*.md` + FAQ)
- des **outils métier** contrôlés (CRM, finance, tâches, projets)
- des **workflows** déclenchés par événements (lead créé, webhook, etc.)

Vous n’avez pas à « entraîner » un modèle : l’agent lit le contexte de votre organisation (multi-tenant) et vos permissions RBAC.

---

## 2. Démarrer avec le Copilot

1. Connectez-vous puis ouvrez le **widget Copilot** (bas à droite) ou la page **Copilot**.
2. Posez une question en français, par exemple :
   - « Liste les projets en cours »
   - « Cherche le contact TechSolutions »
   - « Crée un lead Acme à 12 000 € »
3. Observez les **chips d’outils** (appel / résultat) et les **citations** de documents.

### Approbation humaine (HITL)

Les actions sensibles (`crm_create_lead`, `tasks_create`) **demandent une validation** avant exécution.  
Une carte d’approbation apparaît dans le Copilot : **Approuver** ou **Refuser**.

---

## 3. Catalogue des outils

| Outil | Lecture / écriture | Approbation | Permission |
|-------|--------------------|-------------|------------|
| `crm_search_contacts` | Lecture | Non | `crm.contact.read` |
| `crm_create_lead` | Écriture | **Oui** | `crm.lead.write` |
| `finance_list_invoices` | Lecture | Non | `finance.invoice.read` |
| `tasks_create` | Écriture | **Oui** | `task.write` |
| `projects_list` | Lecture | Non | `project.read` |

Les outils respectent toujours le **RBAC** de l’utilisateur connecté.

---

## 4. Workflows & triggers (S33)

Dans **Workflows** :

1. Créez un graphe (trigger + actions) dans le constructeur visuel.
2. Passez le statut à **actif**.
3. Déclencheurs supportés (exemples) :
   - **Lead créé** → événement `crm.lead.created`
   - **Webhook entrant** → `POST /api/v1/webhooks/inbound/{token}`
   - Manuel via bouton **Exécuter**

Actions exécutées réellement (S34/G) : email, création de tâche, notification, mise à jour CRM, etc.

Consultez les onglets **Événements**, **Webhooks** et **Historique** pour le suivi.

---

## 5. Observabilité & quotas

### Traces (S34)

Page **Agents** : KPIs 30 jours (tokens, coût estimé) + table des traces.  
Chaque réponse Copilot expose aussi `traceId`, tokens et coût dans l’événement SSE `done`.

### Quotas plan (S35)

| Plan | RPM Copilot | Tokens / mois (indicatif) |
|------|-------------|---------------------------|
| Starter | 10 / min | 100 000 |
| Pro | 60 / min | 1 000 000 |
| Enterprise | 200 / min | 2 000 000 |

En cas de dépassement : HTTP **429** avec message d’upgrade.  
Voir **Paramètres → Facturation**.

---

## 6. Bonnes pratiques

- Préférez des questions **actionnables** (« crée… », « liste… », « résume… »).
- Vérifiez toujours une **création** proposée via HITL.
- Activez un workflow **Lead créé → email + tâche** pour industrialiser le suivi.
- Surveillez les **traces** si les coûts OpenAI augmentent.
- Ne partagez pas le token chatbot (`X-Chatbot-Token`) hors de votre front.

---

## 7. FAQ rapide

**Le Copilot répond « Token chatbot invalide »**  
Alignez `CHATBOT_API_TOKEN` (backend) et `VITE_CHATBOT_API_TOKEN` (frontend), puis redémarrez Vite.

**Aucune trace n’apparaît**  
Envoyez au moins un message Copilot ; rechargez la page Agents.

**Le workflow ne part pas**  
Vérifiez que le statut est **actif** et que le libellé du trigger correspond au catalogue (ex. « Lead créé »).

---

## 8. Où trouver plus d’infos

- Documentation technique : `Document/README_10_Agents.md`, `README_08_AIArchitecture.md`
- Roadmap : `Document/README_ETAPE_SUIVANTE.md`
- API structurée : `GET /api/v1/ai/docs`
