# Funeral Academy

Fork do [LearnHouse](https://github.com/learnhouse/learnhouse) voltado à formação profissional
de **agentes funerários e demais profissionais do setor funerário brasileiro**.

A plataforma opera integralmente em **português do Brasil**.

## O que muda em relação ao upstream

| Área | Upstream (LearnHouse) | Funeral Academy |
|---|---|---|
| Idioma padrão | Inglês (`en`), com detecção pelo navegador | **Português (`pt`)**, fixo — a troca só ocorre por ação explícita do usuário |
| Bundle de idioma | `en` embutido, demais sob demanda | `pt` embutido, demais sob demanda (inclusive `en`) |
| Nome do site | LearnHouse | Funeral Academy |
| Organização inicial | `Default Organization` / `default` | `Funeral Academy` / `funeral-academy` |

Nenhuma outra alteração foi feita no código do upstream. Isso é deliberado: quanto menor a
divergência, mais barato é incorporar atualizações do LearnHouse.

## Documentos

- [`ambiente-local.md`](ambiente-local.md) — como rodar na sua máquina e as armadilhas do setup
- [`curriculo.md`](curriculo.md) — desenho instrucional completo: trilhas, cursos, módulos,
  objetivos de aprendizagem e modelo de avaliação
- [`mapeamento-plataforma.md`](mapeamento-plataforma.md) — como o currículo se traduz nos
  recursos do LearnHouse (coleções, cursos, capítulos, atividades, turmas, certificados)
- [`implantacao.md`](implantacao.md) — roadmap de implantação em fases

## Aviso sobre conteúdo técnico e regulatório

O currículo referencia legislação sanitária, trabalhista e de registros públicos, além de
procedimentos de biossegurança e tanatopraxia. **Normas variam entre municípios e estados e
mudam com o tempo.** Todo conteúdo deve ser revisado e validado por profissionais habilitados
(responsável técnico, assessoria jurídica e vigilância sanitária local) antes de ir ao ar.
Os documentos deste diretório são estrutura pedagógica — não substituem essa validação.

## Licença

O upstream é AGPL-3.0 e a licença foi mantida. Ver [`../../LICENSE`](../../LICENSE).
