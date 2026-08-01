# Implantação

Roadmap do fork, do estado atual até a operação com alunos reais.

## Estado atual

Concluído neste fork:

- Import do LearnHouse (snapshot `c8d76f6`)
- Idioma padrão pt-BR (bundle, fallback e detecção)
- Nome do site, organização inicial e e-mail de contato
- Remoção da marca LearnHouse da interface (watermark, "Powered by", badge de embed,
  wordmark do menu, linha de copyright)
- Documentação do currículo e do mapeamento para a plataforma

## Fase 1 — Identidade visual

| Item | Onde | Status |
|---|---|---|
| Logotipo da organização | Admin → Organização → Logo | Pendente — sem logo, o menu exibe o nome em texto |
| Favicon | `customization.general.favicon_image` | Pendente |
| Cor primária | `customization.general.color` | Pendente |
| Fonte | `customization.general.font` | Pendente |
| Landing page | `customization.landing` | Pendente |

Nenhum destes exige código — são configuráveis pelo painel administrativo.

## Fase 2 — Infraestrutura

| Item | Observação |
|---|---|
| Domínio e SSL | `hosting_config.domain` / `frontend_domain` |
| Banco de dados | PostgreSQL com extensão `pgvector` |
| Redis | Cache e filas |
| Armazenamento de mídia | `filesystem` no início; `s3api` quando o volume de vídeo crescer |
| E-mail transacional | Resend ou SMTP — necessário para verificação de conta e recuperação de senha |
| Backup | `learnhouse backup` em cron diário, com restore testado |

**Vídeo é o gargalo previsível.** O currículo é fortemente demonstrativo (procedimentos passo a
passo). Dimensionar armazenamento e banda antes de produzir a Fase 1 do conteúdo, não depois.

## Fase 3 — Conteúdo

Ordem de produção conforme [`curriculo.md`](curriculo.md#9-sequência-de-produção-sugerida):
Núcleo Comum → Operações → Atendimento → Gestão → Tanatopraxia.

Por curso: roteiro → revisão técnica (responsável técnico) → revisão jurídica quando houver
base regulatória → gravação → montagem na plataforma → piloto com turma reduzida → ajuste.

O piloto não é opcional em conteúdo com risco regulatório ou sanitário.

## Fase 4 — Operação

- Definição de coordenação pedagógica e instrutores corretores de assignments
- Fluxo de matrícula (individual e B2B por funerária)
- Política de recertificação a cada 24 meses para trilhas regulatórias
- Rotina de revisão normativa — no mínimo semestral para FA-102, FA-103 e FA-502

## Dívidas técnicas conhecidas

| Item | Impacto | Observação |
|---|---|---|
| Workflows de CI herdados do upstream | Alto | `.github/workflows/` aponta para infra, Codecov e npm da LearnHouse. Falham por falta de secrets. Decidir entre remover, adaptar ou desativar |
| ~300 chaves não traduzidas em `pt.json` | Médio | ~6,8% do total; boa parte são nomes próprios (Discord, YouTube). As de navegação já foram corrigidas |
| Lint backlog do upstream | Baixo | 295 erros pré-existentes em `apps/web`, sem impacto funcional |
| Import por snapshot | Médio | O histórico do upstream não foi preservado; atualizações do LearnHouse exigem merge manual |

## Atualizando a partir do upstream

O fork mantém a divergência deliberadamente pequena — os arquivos alterados são poucos e
estão listados no [`README.md`](README.md). Para incorporar mudanças do LearnHouse:

```bash
git remote add upstream https://github.com/learnhouse/learnhouse.git
git fetch upstream
git diff HEAD upstream/dev -- apps/web/lib/i18n.ts   # revisar arquivo a arquivo
```

Como o import foi por snapshot, não existe ancestral comum: o merge é manual, arquivo a
arquivo, priorizando os que este fork não tocou.
