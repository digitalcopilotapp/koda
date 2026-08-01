# Mapeamento — currículo → recursos da plataforma

Como as entidades do desenho instrucional se traduzem nos recursos do LearnHouse.

## Hierarquia

| Conceito pedagógico | Recurso na plataforma | Observação |
|---|---|---|
| Trilha (ex.: Operações Funerárias) | **Collection** | Agrupa os cursos da trilha e dá origem ao certificado de trilha |
| Curso (ex.: FA-201) | **Course** | Unidade de matrícula e de certificação |
| Módulo | **Chapter** | Blocos de 60–90 min |
| Lição | **Activity** | 8–15 min; vídeo, texto em blocos, documento ou quiz |
| Avaliação prática | **Assignment** | Com rubrica no enunciado e correção por instrutor |
| Quiz de verificação | **Activity** tipo quiz | Formativa, tentativas ilimitadas |
| Turma / coorte | **User Group** | Controla acesso e permite acompanhar uma turma específica |
| Fórum da trilha | **Discussion** | Um espaço por trilha, não por curso — evita dispersão |
| Certificado | **Certificate** | Emitido na conclusão do curso e da trilha |

## Convenções de nomenclatura

- **Código do curso no título:** `FA-201 — Remoção e Translado`. O código é o que aparece em
  planilhas de RH, matrícula e certificado; sem ele o rastreio quebra.
- **Slug:** derivado do código em minúsculo — `fa-201-remocao-e-translado`.
- **Módulos:** numerados dentro do curso (`1. Remoção em domicílio`), nunca com código próprio.

## Configuração por trilha

| Trilha | Visibilidade | Pré-requisito | Grupo |
|---|---|---|---|
| Núcleo Comum | Aberta a todos os matriculados | — | `todos` |
| Operações Funerárias | Restrita | Núcleo Comum concluído | `operacoes` |
| Tanatopraxia | Restrita | Núcleo Comum + FA-202 | `tanatopraxia` |
| Atendimento e Planos | Restrita | Núcleo Comum concluído | `comercial` |
| Gestão | Restrita | Núcleo Comum concluído | `gestao` |

O LearnHouse não impõe pré-requisito entre cursos de forma nativa. Duas opções:

1. **Operacional (recomendada para o início):** liberação manual do User Group pela coordenação
   ao concluir o Núcleo Comum. Custo baixo, funciona desde o primeiro dia.
2. **Automatizada:** verificar a conclusão via API e mover o aluno de grupo por webhook. Exige
   desenvolvimento e só se justifica com volume alto de matrículas.

Começar pela opção 1 e só migrar quando o volume doer.

## Recursos da plataforma que valem ativar

| Recurso | Uso previsto |
|---|---|
| **Certificates** | Certificação por curso e por trilha; obrigatório para o setor |
| **Assignments** | Avaliações somativas com evidência de execução real |
| **Discussions** | Tira-dúvidas por trilha, moderado pela coordenação |
| **User Groups** | Turmas, controle de pré-requisito, contratos B2B (funerárias) |
| **Analytics** | Conclusão por módulo — identifica onde o aluno trava |
| **Podcasts** | Formato adequado ao público: consumo em deslocamento entre chamadas |

## Recursos a manter desligados no início

**Playgrounds**, **Boards** e **Code** não têm aplicação neste currículo e apenas poluem a
navegação do aluno. Desligar em `admin_toggles` até que exista um caso de uso concreto.
